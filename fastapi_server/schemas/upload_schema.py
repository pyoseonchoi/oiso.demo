from pydantic import BaseModel


class ImageMetaDataSchema(BaseModel):
    latitude: float | None = None
    longitude: float | None = None
    captured_at: str | None = None


class FileUploadResponse(BaseModel):
    original_filename: str
    saved_filename: str
    content_type: str | None = None
    file_url: str
    metadata: ImageMetaDataSchema | None = None

