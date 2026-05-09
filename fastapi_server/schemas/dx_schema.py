from pydantic import BaseModel
from schemas.base_schema import BaseSuccessResponse
from datetime import datetime

class ImageMetaData(BaseModel):
    longitude: float | None = None
    latitude: float | None = None
    time_stamp: datetime | None = None


class PicUploadResponse(BaseSuccessResponse):
    picture_url: str = ""  # 업로드된 원본 이미지의 MinIO URL
    picture_id: str        # DB에 생성된 Picture의 unique_id
    s3_bucket: str
    s3_key: str
    s3_version: str | None = None
    metadata: ImageMetaData


