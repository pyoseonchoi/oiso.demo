from fastapi import APIRouter, Query, Depends
from typing import Annotated
from db.session import get_db
from sqlalchemy.orm import Session
from schemas.mx_schema import (
    GetMarkersResponse,
    MarkerItem,
    MarkerInfosResponse,
    PostItem,
)
from services import mx_services

router = APIRouter()


db_session = Annotated[Session, Depends(get_db)]

@router.get("/get_markers", response_model=GetMarkersResponse)
def get_markers(
    user_long: float = Query(..., description="유저 현재 경도"),
    user_lat: float = Query(..., description="유저 현재 위도"),
    screen_topleft: str = Query(..., description="화면 좌상단 위경도 (예: '35.9,128.5')"),
    screen_bottomright: str = Query(..., description="화면 우하단 위경도 (예: '35.8,128.6')"),
    nearmode: bool = Query(True, description="True: 범위 내 없으면 빈 배열 / False: 가장 가까운 것 반환"),
    db: db_session = None,
):
    """
    현재 지도 화면 범위 내의 클러스터 마커 목록을 반환합니다.

    - 현재: 더미 마커 1개 반환
    - 추후: PostgreSQL ClusterArray/TagList 조회 + MinIO lowres 이미지 URL 반환
    """
    # TODO: bounding box 파싱 → ClusterArray/TagList DB 조회 → MinIO URL 반환

    markers = mx_services.get_markers(db=db, user_lng=user_long, user_lat=user_lat, screen_topleft=screen_topleft, screen_bottomright=screen_bottomright, nearmode=nearmode)
    
    return GetMarkersResponse(markers=markers)


@router.get("/get_marker_infos", response_model=MarkerInfosResponse)
def marker_infos(
    cluster_no: int = Query(..., description="조회할 클러스터 번호"),
    db: db_session = None
):
    """
    특정 클러스터 번호에 해당하는 게시물(사진+태그) 목록을 반환합니다.

    - 현재: 더미 게시물 1개 반환
    - 추후: ClusterArray → TagList → Picture 조회 + MinIO highres 이미지 URL 반환
    """
    # TODO: ClusterArray 조회 → Picture 목록 → MinIO highres URL 반환
    posts = mx_services.get_markers_infos(db=db, cluster_no=cluster_no)
    return MarkerInfosResponse(posts=posts)