from fastapi import APIRouter, File, UploadFile, Form
from typing import List, Annotated
from exceptions.base import AppException
from schemas.ax_schema import (
    ChatV2Request,
    ChatV2Response,
    MenuInformation,
    OCRInformation,
    PicNOrderResponse,
)

import base64
from services import ax_services

router = APIRouter()


@router.post("/get_chat_completion", response_model=ChatV2Response)
async def chat_v2(request: ChatV2Request):
    """
    유저 메시지를 LangGraph Chat Agent로 전달하고 AI 응답을 반환합니다.

    - 현재: 더미 응답 반환
    - 추후: LangGraph HTTP 요청 + DB 저장 (UserMessage / AIMessage)
    """
    # TODO: uuid로 ChatSession 조회/생성 → LangGraph httpx 요청 → DB 저장
    dummy_reply = (
        f"[더미 응답] uuid={request.uuid} | "
        f"메시지 수신: '{request.user_added_message}'"
    )
    return ChatV2Response(response=dummy_reply)


@router.post("/get_picnorder", response_model=PicNOrderResponse)
async def pic_n_order(
    uuid: Annotated[str, Form(...)],
    user_language: Annotated[str, Form(...)],
    pics: Annotated[list[UploadFile], File(...)],
):
    """
    메뉴판 사진을 OCR Agent로 전달하여 구조화된 메뉴 정보를 반환합니다.

    - 현재: 첫번째 이미지만 가능
    - 추후: List[UploadFile] 잘 반영하도록
    """
    # TODO: 이미지 base64 인코딩 → LangGraph OCR Agent 요청

    # 이미지를 base64로 변환
    pic = pics[0] # 나중에 수정필요

    # 파일 형식 검사
    allowed_content_types = ["image/jpeg", "image/png", "image/gif", "image/webp"]
    if pic.content_type not in allowed_content_types:
        raise AppException(
            status_code=400, 
            reason=f"지원하지 않는 이미지 형식입니다. JPG, PNG, GIF, WEBP 형식만 가능합니다. (현재: {pic.content_type})"
        )


    image_bytes = await pic.read() # uploadfile -> bytes로
    image_b64 = base64.b64encode(image_bytes).decode("utf-8") # bytes -> base64 문자열

    ocr_result = await ax_services.run_ocr_agent(image_b64, user_language)
    
    
    return PicNOrderResponse(
        ocr_structure=OCRInformation(**ocr_result) # dict형식을 pydantic 모델로 변환해주어야함
    )
