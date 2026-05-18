# (c) 2026 oiso.ai
"""
LangGraph 노드 간 전달되는 도메인 객체 정의.

설계도의 Classes(통신 간 필요한 객체들) 영역을 Pydantic 기반으로 구현.
FastAPI 측 SQLAlchemy ORM 모델(mx_model.py)과는 독립적이며,
LangGraph 내부의 노드-투-노드 통신에서 타입 안전성과 가독성을 보장한다.
"""
from __future__ import annotations

from pydantic import BaseModel, Field
from typing import List, Optional


# ─── 위치 / 좌표 ────────────────────────────────────────────────

class Location(BaseModel):
    """GPS 좌표를 캡슐화하는 도메인 객체.

    기존 `client_lat`, `client_lng` 파편화 문제를 해소한다.
    """
    lat: float = Field(0.0, description="위도 (latitude)")
    lng: float = Field(0.0, description="경도 (longitude)")

    def is_valid(self) -> bool:
        """좌표가 실제 사용 가능한 값인지 검증."""
        if self.lat == 0.0 and self.lng == 0.0:
            return False
        return -90.0 <= self.lat <= 90.0 and -180.0 <= self.lng <= 180.0


# ─── 개별 사진 (Individuals / Picture) ───────────────────────────

class PictureInfo(BaseModel):
    """개별 사진의 핵심 정보를 캡슐화하는 도메인 객체.

    FastAPI 측 Picture + Image + Metadata 테이블 3개를 합친 읽기 전용 뷰.
    """
    unique_id: str = Field(description="사진 고유 ID (UUID)")
    s3_key: Optional[str] = Field(None, description="S3/MinIO 저장 키")
    s3_bucket: Optional[str] = Field(None, description="S3 버킷명")
    latitude: Optional[float] = Field(None, description="촬영 위도")
    longitude: Optional[float] = Field(None, description="촬영 경도")
    created_date: Optional[str] = Field(None, description="촬영 일시 (ISO 8601)")
    tags: List[str] = Field(default_factory=list, description="사진에 부착된 태그 목록")


# ─── 클러스터 마커 (Marker) ──────────────────────────────────────

class MarkerInfo(BaseModel):
    """검색 결과로 반환되는 클러스터(마커) 정보.

    DB의 `cluster_array` + 연관 태그 + 거리 계산값을 하나의 도메인 객체로 캡슐화.
    """
    cluster_no: int = Field(description="클러스터 번호 (PK)")
    latitude: float = Field(description="클러스터 중심 위도")
    longitude: float = Field(description="클러스터 중심 경도")
    tags: List[str] = Field(default_factory=list, description="클러스터에 연결된 태그 목록")
    distance_km: float = Field(0.0, description="사용자 위치로부터의 거리 (km)")
    thumbnail_s3_key: Optional[str] = Field(None, description="대표 이미지 S3 키")

    @property
    def location(self) -> Location:
        """마커의 위치를 Location 객체로 반환."""
        return Location(lat=self.latitude, lng=self.longitude)
