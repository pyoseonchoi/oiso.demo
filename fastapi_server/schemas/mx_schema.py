from pydantic import BaseModel
from typing import List
from schemas.base_schema import BaseSuccessResponse

# ─── /v1/mx/get_markers ─────────────────────────────────────────

class MarkerItem(BaseModel):
    longitude: str
    latitude: str
    cluster_no: int
    cluster_tags: List[str]
    cluster_pics_lowres_url: str  # DB Image.s3_key로부터 동적 생성 (CDN/MinIO URL)


class GetMarkersResponse(BaseSuccessResponse):
    markers: List[MarkerItem]


# ─── /v1/mx/marker_infos ─────────────────────────────────────────

class PostItem(BaseModel):
    image_id: str
    image_tags: List[str]
    pic_highres_url: str          # DB Image.s3_key로부터 동적 생성 (CDN/MinIO URL)


class MarkerInfosResponse(BaseSuccessResponse):
    posts: List[PostItem]
