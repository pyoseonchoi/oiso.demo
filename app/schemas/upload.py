# app/schemas/upload.py
from pydantic import BaseModel, Field, validator

class MarkerResponse(BaseModel):
    """
    프론트엔드 친구들에게 전달해 줄(Response 응답용) "깔끔한 상자" 역할을 하는 클래스.
    보안상 DB의 민감한 내용을 숨기거나 파싱할 때 씁니다.
    """
    id: int
    category: str
    latitude: float
    longitude: float

    class Config:
        # DB 모델(SQLAlchemy 객체)을 이 Pydantic 스키마로 자연스럽게 바꿔주는 놀라운 옵션. 필수!
        orm_mode = True

# 멘토의 참고사항:
# POST /upload 에선 클라이언트가 `multipart/form-data`로 파일(+위경도 텍스트)을 보냅니다.
# FastAPI는 파일이 껴있으면 BaseModel 대신, 보통 함수의 매개변수 부분에서 `Form()` 을 직접 사용해서 받습니다.
# 만약 순수 JSON 요청이라면 아래처럼 짜서 "유효성 검사"를 철저히 했을겁니다. 

class MarkerCreateValidation(BaseModel):
    latitude: float = Field(..., description="위도는 소수점으로 옵니다.")
    longitude: float = Field(..., description="경도는 소수점으로 옵니다.")
    
    # 이 validator 구역을 지나가면 절대로 범위를 벗어난 쓰레기값이 DB에 들어가지 못합니다! (안전제일)
    @validator("latitude")
    def validate_latitude(cls, v):
        if not (-90.0 <= v <= 90.0):
            raise ValueError("위도는 지구상에 존재할 수 없는 값입니다 (-90 ~ 90).")
        return v
        
    @validator("longitude")
    def validate_longitude(cls, v):
        if not (-180.0 <= v <= 180.0):
            raise ValueError("경도는 지구상에 존재할 수 없는 값입니다 (-180 ~ 180).")
        return v
