from pydantic import BaseModel, Field
from datetime import datetime

class MarkerImage(BaseModel):
    id: int
    file_url: str
    original_filename: str
    captured_at: str | None
    
class MarkerSummary(BaseModel): # GET /markers 지도 핀용
    id: int
    latitude: float
    longitude: float
    tags: list[str]
    image_count: int

class MarkerDetail(MarkerSummary): # GET /markers/{id} 상세
    images: list[MarkerImage]
    created_at: datetime