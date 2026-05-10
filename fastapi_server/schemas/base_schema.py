from pydantic import BaseModel

class BaseSuccessResponse(BaseModel):
    """
    모든 API 성공 응답의 공통 부모 스키마
    기본적으로 {"success": true} 를 포함하게 됩니다.
    """
    success: bool = True
