from fastapi import APIRouter, File, UploadFile, Form
import json
from core.storage import generate_image_url

from fastapi.responses import StreamingResponse
from typing import List, Annotated
from exceptions.base import AppException
from schemas.ax_schema import (
    ChatV2Request,
    ChatV2WithAttachmentsRequest,
    ChatV2Response,
    ChatAttachmentUploadResponse,
    AnalyzeChatMenuRequest,
    AnalyzeChatMenuResponse,
    MenuInformation,
    OCRInformation,
    PicNOrderResponse,
)

import base64
from services import ax_services

router = APIRouter()

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
async def chat_v2(request: ChatV2Request):
    """
    유저 메시지를 LangGraph Chat Agent로 전달하고 AI 응답을 반환합니다.

    - uuid를 LangGraph thread_id로 활용 → 같은 uuid이면 대화 기록이 이어짐 (멀티턴)
    - chat_agent 내부적으로 query_enhancer → main_agent → DB 검색 툴 순서로 실행
    """
    ai_response = await ax_services.run_chat_agent(
        thread_id=request.uuid,
        user_message=request.user_added_message,
        user_language=request.user_language,
        client_lat=request.client_lat,
        client_lng=request.client_lng,
    )
    return ChatV2Response(response=ai_response)



@router.post("/stream_chat")
async def stream_chat(request: ChatV2Request):
    """
    main_agent의 응답을 SSE(text/event-stream)로 스트리밍합니다.
    임시용, 안정화되면 /get_chat_completion 통합
    """
    async def generate():
        try:
            async for delta in ax_services.stream_chat_agent(
                thread_id=request.uuid,
                user_message=request.user_added_message,
                user_language=request.user_language,
                client_lat=request.client_lat,
                client_lng=request.client_lng,
            ):
                # SSE 포맷: "data: <내용>\n\n"
                yield f"data: {json.dumps(delta, ensure_ascii=False)}\n\n"

        except Exception as e:
            yield f"data: {json.dumps('[ERROR] ' + str(e))}\n\n"
        finally:
            yield "data: \"[DONE]\"\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",   # nginx 버퍼링 비활성화
        },
    )


@router.post("/stream_chat_v2")
async def stream_chat_v2(request: ChatV2WithAttachmentsRequest):
    """
    기존 /stream_chat에 이미지 첨부 메타데이터 전달만 추가한 v2 엔드포인트입니다.
    token/ui_outputs/done 타입을 가진 JSON SSE 이벤트를 반환합니다.
    """
    async def generate():
        attachments = [
            attachment.model_dump()
            for attachment in request.attachments
        ]
        try:
            async for item in ax_services.stream_chat_agent_v2(
                thread_id=request.uuid,
                user_message=request.user_added_message,
                user_language=request.user_language,
                client_lat=request.client_lat,
                client_lng=request.client_lng,
                attachments=attachments,
            ):
                if isinstance(item, tuple):
                    event_key, event_data = item

                    if event_key == "__ocr_result__":
                        for menu_item in event_data.get("menus", []):
                            menu_item["price"] = normalize_menu_price(
                                menu_item.get("price", 0)
                            )
                        payload = {
                            "type": "menu_ocr_result",
                            "ocr_structure": event_data,
                        }
                    elif event_key == "__nearby_stores_result__":
                        
                        for store in event_data.get("results", []):
                            s3_key = store.pop("thumbnail_s3_key", None)
                            store["thumbnail_url"] = (
                                generate_image_url(s3_key) if s3_key else ""
                            )
                        payload = {
                            "type": "nearby_stores_result",
                            "data": event_data,
                        }
                        
                    else:
                        continue  # 알 수 없는 이벤트는 무시
                else:
                    # 일반 텍스트 토큰
                    payload = {"type": "token", "delta": item}
                yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"

        except Exception as e:
            payload = {"type": "error", "message": str(e)}
            yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
        finally:
            yield f"data: {json.dumps({'type': 'done'}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/upload_chat_attachment", response_model=ChatAttachmentUploadResponse)
async def upload_chat_attachment(
    image: Annotated[UploadFile, File(description="채팅 첨부 이미지")],
    thread_id: Annotated[str | None, Form()] = None,
):
    """
    채팅에서 사용할 이미지 첨부 파일을 S3/MinIO에 저장합니다.
    지도 데이터 구축용 DB 테이블에는 저장하지 않습니다.
    """
    attachment = ax_services.upload_chat_attachment(
        image=image,
        thread_id=thread_id,
    )
    return ChatAttachmentUploadResponse(attachment=attachment)


@router.post("/analyze_chat_menu", response_model=AnalyzeChatMenuResponse)
async def analyze_chat_menu(request: AnalyzeChatMenuRequest):
    """
    S3/MinIO에 저장된 채팅 첨부 메뉴판 이미지를 OCR Agent로 분석합니다.
    채팅 첨부 이미지는 DB에 저장하지 않고, OCR 결과만 반환합니다.
    """
    if request.attachment.type != "image":
        raise AppException(
            status_code=400,
            reason="이미지 첨부만 메뉴판 분석에 사용할 수 있습니다.",
        )

    if not request.attachment.s3_key:
        raise AppException(
            status_code=400,
            reason="분석할 이미지의 s3_key가 필요합니다.",
        )

    image_b64 = ax_services.load_chat_attachment_as_base64(
        request.attachment.s3_key,
    )
    ocr_result = await ax_services.run_ocr_agent(
        image_b64,
        request.user_language,
    )

    if hasattr(ocr_result, "model_dump"):
        ocr_result = ocr_result.model_dump()

    menus = ocr_result.get("menus", [])
    for menu_item in menus:
        menu_item["price"] = normalize_menu_price(menu_item.get("price", 0))

    return AnalyzeChatMenuResponse(
        ocr_structure=OCRInformation(**ocr_result)
    )


@router.post("/get_picnorder", response_model=PicNOrderResponse)
async def pic_n_order(
    uuid: Annotated[str, Form(...)],
    user_language: Annotated[str, Form(...)],
    pics: Annotated[UploadFile, File(description="메뉴판 이미지")],
):
    """
    메뉴판 사진을 OCR Agent로 전달하여 구조화된 메뉴 정보를 반환합니다.
    OCR 결과를 DB에 저장합니다 (OCRData + MenuList + OCRMenuArray).
    """


    # 파일 형식 검사
    allowed_content_types = ["image/jpeg", "image/png", "image/gif", "image/webp"]
    if pics.content_type not in allowed_content_types:
        raise AppException(
            status_code=400, 
            reason=f"지원하지 않는 이미지 형식입니다. JPG, PNG, GIF, WEBP 형식만 가능합니다. (현재: {pics.content_type})"
        )

    pics.file.seek(0)
    image_bytes = await pics.read() # uploadfile -> bytes로
    image_b64 = base64.b64encode(image_bytes).decode("utf-8") # bytes -> base64 문자열

    pics.file.seek(0)

    ocr_result = await ax_services.run_ocr_agent(image_b64, user_language)
    
    # 만약 OCR 결과가 Pydantic 객체로 온 경우 dict로 변환
    if hasattr(ocr_result, "model_dump"):
        ocr_result = ocr_result.model_dump()

    # ─── OCR 결과 price 정규화 ───────────────────────── 
    #TODO: 나중에 service 계층으로 빼기
    menus = ocr_result.get("menus", [])
    for menu_item in menus:
        menu_item["price"] = normalize_menu_price(menu_item.get("price", 0))

    
    return PicNOrderResponse(
        ocr_structure=OCRInformation(**ocr_result) # dict형식을 pydantic 모델로 변환해주어야함
    )


