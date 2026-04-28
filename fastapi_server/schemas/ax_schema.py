from pydantic import BaseModel
from typing import List
from schemas.base_schema import BaseSuccessResponse

# ─── /v1/ax/chat ────────────────────────────────────────────────

class ChatV2Request(BaseModel):
    uuid: str                  # 대화 세션 식별 UUID → LangGraph thread_id로 사용
    user_added_message: str    # 유저 메시지
    user_language: str         # 응답 언어 (예: "Korean", "English", "Japanese")
    client_lat: float          # 유저 현재 위도 (주변 가게 검색용)
    client_lng: float          # 유저 현재 경도 (주변 가게 검색용)


class ChatV2Response(BaseSuccessResponse):
    response: str              # AI 응답 텍스트 (또는 성공/실패 메시지)


# ─── /v1/ax/pic_n_order ─────────────────────────────────────────

class MenuInformation(BaseModel):
    number: int
    text_in_original_language: str
    text_in_user_language: str
    price: int


class OCRInformation(BaseModel):
    menus: List[MenuInformation]
    user_language: str
    original_language: str


class PicNOrderResponse(BaseSuccessResponse):
    ocr_structure: OCRInformation | None = None
