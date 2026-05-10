# (c) 2026 oiso.ai
from typing import TypedDict


class OCRAgentState(TypedDict):
    
    image_b64: str # FastAPI에서 base64인코딩해서 넘겨줄 이미지
    user_language:  str
    is_valid: bool
    error_message: str
    ocr_result: dict | None # OCR결과 - Structured Output

