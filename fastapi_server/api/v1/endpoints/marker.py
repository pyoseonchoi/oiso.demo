from fastapi import APIRouter, Depends, HTTPException, UploadFile
from typing import Annotated
from typing import Dict
from schemas.marker_schema import MarkerDetail, MarkerImage, MarkerSummary
from services import marker_service
from sqlalchemy.orm import Session
from db.session import get_db

router = APIRouter()

db_session = Annotated[Session, Depends(get_db)]

@router.get("/", response_model=list[MarkerSummary])
async def get_markers(db: db_session):
    return marker_service.get_all_markers(db) 

@router.get("/{marker_id}", response_model=MarkerDetail)
async def get_marker_detail(marker_id: int, db: db_session):
    """특정 마커의 상세 정보 (소속 이미지 포함)"""
    marker = marker_service.get_marker_detail(db, marker_id)
    if not marker:
        raise HTTPException(status_code=404, detail="마커를 찾을 수 없습니다.")
    return marker