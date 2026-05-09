from fastapi import APIRouter, File, UploadFile, Form, Depends
from typing import List, Annotated, Optional
from sqlalchemy.orm import Session
from db.session import get_db
from exceptions.base import AppException
from schemas.ax_schema import (
    ChatV2Response,
    MenuInformation,
    OCRInformation,
    PicNOrderResponse,
)

import base64
import uuid
from datetime import datetime
from services import ax_services
from models.ax_model import UserMessage, AIMessage, Chats

router = APIRouter()

db_session = Annotated[Session, Depends(get_db)]


def normalize_menu_price(price) -> int:
    """
    OCR/LLM이 반환한 가격을 Integer로 정규화합니다.

    예:
    4.5     -> 4500
    5.5     -> 5500
    "4.5"   -> 4500
    "5,500" -> 5500
    "5500원" -> 5500
    None    -> 0
    """

    if price is None:
        return 0

    if isinstance(price, int):
        return price

    if isinstance(price, float):
        if price < 100:
            return int(price * 1000)
        return int(price)

    if isinstance(price, str):
        cleaned = (
            price.replace(",", "")
                 .replace("원", "")
                 .replace("₩", "")
                 .strip()
        )

        if cleaned == "":
            return 0

        try:
            price_float = float(cleaned)
            if price_float < 100:
                return int(price_float * 1000)
            return int(price_float)
        except ValueError:
            return 0

    try:
        return int(price)
    except Exception:
        return 0


@router.post("/get_chat_completion", response_model=ChatV2Response)
async def chat_v2(
    uuid_str: Annotated[str, Form(alias="uuid")],
    user_added_message: Annotated[str, Form(...)],
    user_language: Annotated[str, Form(...)],
    client_lat: Annotated[float, Form(...)],
    client_lng: Annotated[float, Form(...)],
    pic: Annotated[Optional[UploadFile], File(description="첨부 이미지")] = None,
    db: db_session = None,
):
    """
    유저 메시지를 LangGraph Chat Agent로 전달하고 AI 응답을 반환합니다.
    이미지 첨부 가능 (multipart/form-data).

    - uuid를 LangGraph thread_id로 활용 → 같은 uuid이면 대화 기록이 이어짐 (멀티턴)
    - chat_agent 내부적으로 query_enhancer → main_agent → DB 검색 툴 순서로 실행
    """

    # ─── chat_order 자동 계산 ───────────────────────────
    from sqlalchemy import func
    max_order = db.query(func.max(UserMessage.chat_order)).join(
        Chats, Chats.user_msg_id == UserMessage.unique_id
    ).filter(Chats.uuid == uuid_str).scalar()
    next_order = (max_order or 0) + 1

    # ─── 첨부 이미지 처리 (선택적) ─────────────────────
    picture_id = None
    if pic is not None:
        from services import dx_services
        result = dx_services.upload_picture(pic, db)
        picture_id = result["picture_id"]

    # ─── LangGraph Agent 호출 ─────────────────────────
    ai_response = await ax_services.run_chat_agent(
        thread_id=uuid_str,
        user_message=user_added_message,
        user_language=user_language,
        client_lat=client_lat,
        client_lng=client_lng,
    )

    # ─── DB 저장: UserMessage → AIMessage → Chats ─────
    now = datetime.utcnow()

    user_msg = UserMessage(
        unique_id=str(uuid.uuid4()),
        message=user_added_message,
        time_stamp=now,
        chat_order=next_order,
        picture_id=picture_id,
    )
    db.add(user_msg)

    ai_msg = AIMessage(
        unique_id=str(uuid.uuid4()),
        message=ai_response,
        time_stamp=now,
        chat_order=next_order,
    )
    db.add(ai_msg)

    chat = Chats(
        unique_id=str(uuid.uuid4()),
        uuid=uuid_str,
        user_msg_id=user_msg.unique_id,
        ai_msg_id=ai_msg.unique_id,
    )
    db.add(chat)
    db.commit()

    return ChatV2Response(response=ai_response)


@router.post("/get_picnorder", response_model=PicNOrderResponse)
async def pic_n_order(
    uuid_str: Annotated[str, Form(alias="uuid")],
    user_language: Annotated[str, Form(...)],
    pic: Annotated[UploadFile, File(description="메뉴판 이미지")],
    db: db_session = None,
):
    """
    메뉴판 사진을 OCR Agent로 전달하여 구조화된 메뉴 정보를 반환합니다.
    OCR 결과를 DB에 저장합니다 (OCRData + MenuList + OCRMenuArray).
    """
    from models.ax_model import OCRData, MenuList, OCRMenuArray

    # 파일 형식 검사
    allowed_content_types = ["image/jpeg", "image/png", "image/gif", "image/webp"]
    if pic.content_type not in allowed_content_types:
        raise AppException(
            status_code=400,
            reason=f"지원하지 않는 이미지 형식입니다. JPG, PNG, GIF, WEBP 형식만 가능합니다. (현재: {pic.content_type})"
        )

    # ─── 먼저 파일을 읽어서 OCR용 base64 생성 ─────────
    # dx_services.upload_picture() 이후에는 파일 객체가 닫힐 수 있으므로
    # OCR에 필요한 bytes를 먼저 확보합니다.
    pic.file.seek(0)
    image_bytes = await pic.read()
    image_b64 = base64.b64encode(image_bytes).decode("utf-8")

    # upload_picture()에서 같은 파일을 다시 읽어야 하므로 포인터를 처음으로 되돌림
    pic.file.seek(0)

    # ─── 이미지를 S3에 업로드 + DB에 Picture 저장 ─────
    from services import dx_services
    upload_result = dx_services.upload_picture(pic, db)
    picture_id = upload_result["picture_id"]

    # ─── OCR Agent 호출 ───────────────────────────────
    ocr_result = await ax_services.run_ocr_agent(image_b64, user_language)

    # 만약 OCR 결과가 Pydantic 객체로 온 경우 dict로 변환
    if hasattr(ocr_result, "model_dump"):
        ocr_result = ocr_result.model_dump()

    # ─── OCR 결과 price 정규화 ─────────────────────────
    menus = ocr_result.get("menus", [])
    for menu_item in menus:
        menu_item["price"] = normalize_menu_price(menu_item.get("price", 0))

    # ─── OCR 결과 DB 저장 ─────────────────────────────
    now = datetime.utcnow()

    # 1) OCRData 레코드 생성
    ocr_data = OCRData(
        uuid=uuid_str,
        pic_no=picture_id,
    )
    db.add(ocr_data)
    db.flush()  # ocr_data.ocr_no 확보

    # 2) 메뉴 항목들 저장 + 연결
    for menu_item in menus:
        menu = MenuList(
            unique_id=str(uuid.uuid4()),
            menu_name=menu_item.get("text_in_original_language", ""),
            menu_price=menu_item.get("price", 0),
            upload_time_stamp=now,
        )
        db.add(menu)
        db.flush()

        # OCRMenuArray 연결
        link = OCRMenuArray(
            data_no=ocr_data.ocr_no,
            menu_no=menu.unique_id,
        )
        db.add(link)

    db.commit()

    return PicNOrderResponse(
        ocr_structure=OCRInformation(**ocr_result)
    )