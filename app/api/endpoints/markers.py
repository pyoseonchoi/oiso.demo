# app/api/endpoints/markers.py
from fastapi import APIRouter, Depends, UploadFile, File, Form, BackgroundTasks, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db

from app.services import marker_service
from app.services.ai_service import process_image_for_marker
import uuid

router = APIRouter()


@router.post("/upload", summary="마커와 사진 업로드")
async def upload_marker(
    background_tasks: BackgroundTasks,
    latitude: float = Form(..., description="사진을 찍은 위치의 위도"),
    longitude: float = Form(..., description="사진을 찍은 위치의 경도"),
    category: str = Form(..., description="일단 사용자가 선택하거나, 클라에서 보낸 임시 카테고리"),
    file: UploadFile = File(..., description="사용자가 갤러리/카메라에서 선택한 이미지 원본 파일"),
    db: Session = Depends(get_db)
):  
    """
    사진과 위경도를 받아 마커를 생성합니다.
    """
    
    if not (-90 <= latitude <= 90) or not (-180 <= longitude <= 180):
        raise HTTPException(status_code=400, detail="유효하지 않은 GPS 좌표입니다.")
    
    # TODO: 추후 AWS S3 연동 로직으로 교체 필요
    fake_s3_url = f"https://my-s3.aws.com/uploads/{uuid.uuid4()}_{file.filename}"
    
    try:
        new_marker = marker_service.create_marker_and_photo(
            db=db, latitude=latitude, longitude=longitude, 
            category=category, fake_s3_url=fake_s3_url
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail="DB 저장 중 에러가 발생했습니다.")
        
    background_tasks.add_task(process_image_for_marker, new_marker.id, fake_s3_url)
    
    return {
        "status": "success",
        "message": "사진 업로드가 완료되었습니다.",
        "marker_id": new_marker.id
    }


@router.get("", summary="지도 주변 마커 조회 (반경 N 미터 이내)")
def get_markers(
    latitude: float,
    longitude: float,
    radius: int = 1000, # 기본값: 1km
    db: Session = Depends(get_db)
):
    """
    반경(radius) 이내 마커 목록을 반환합니다.
    """
    markers = marker_service.get_markers_within_radius(
        db=db, latitude=latitude, longitude=longitude, radius_meters=radius
    )
    result = []
    for m in markers:
        result.append({
            "id": m.id,
            "category": m.category,
            "latitude": m.latitude,
            "longitude": m.longitude
        })
        
    return {
        "status": "success",
        "count": len(result),
        "data": result
    }
