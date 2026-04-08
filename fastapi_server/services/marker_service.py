import random
from sqlalchemy.orm import Session
from models.marker_model import Marker, Tag
from models.upload_model import Image, ImageMetaData
from schemas.marker_schema import MarkerSummary, MarkerDetail, MarkerImage



# 미리 정의된 태그 -> 랜덤 부여
MOCK_TAGS = ["노점", "음식점", "카페", "의류", "잡화", "과일", "어물", "반찬"]

def create_marker_from_image(db: Session, image: Image, metadata: ImageMetaData) -> Marker:
    """
    나중에 클러스터링 교체 예정
    """

    marker = Marker(
        latitude=metadata.latitude,
        longitude=metadata.longitude,
    )

    db.add(marker)
    db.flush()

    image.marker_id = marker.id #이미지에 마커 연결

    #랜덤 태그 부여
    assign_random_tags(db, marker)

    return marker

def assign_random_tags(db: Session, marker: Marker, count: int = 2):
    """
    나중에 VLM 서버로 대체
    """

    selected = random.sample(MOCK_TAGS,  min(count, len(MOCK_TAGS)))


    for tag_name in selected:
        tag = db.query(Tag).filter(Tag.name == tag_name).first()
        if not tag:
            tag = Tag(name = tag_name)
            db.add(tag)
            db.flush()

        marker.tags.append(tag)




def get_all_markers(db: Session) -> list[MarkerSummary]:
    """전체 마커 요약 목록"""
    markers = db.query(Marker).all()

    return [
        MarkerSummary(
            id=m.id,
            latitude=m.latitude,
            longitude=m.longitude,
            tags=[tag.name for tag in m.tags],
            image_count=len(m.images),
        )
        for m in markers
    ]


def get_marker_detail(db: Session, marker_id: int) -> MarkerDetail | None:
    """특정 마커 상세 정보"""
    marker = db.query(Marker).filter(Marker.id == marker_id).first()
    if not marker:
        return None

    return MarkerDetail(
        id=marker.id,
        latitude=marker.latitude,
        longitude=marker.longitude,
        tags=[tag.name for tag in marker.tags],
        image_count=len(marker.images),
        images=[
            MarkerImage(
                id=img.id,
                file_url=img.file_url,
                original_filename=img.original_filename,
                captured_at=img.image_metadata.captured_at if img.image_metadata else None,
            )
            for img in marker.images
        ],
        created_at=marker.created_at,
    )
