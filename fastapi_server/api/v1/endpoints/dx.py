from fastapi import APIRouter, File, UploadFile, Depends
from typing import Annotated
from sqlalchemy.orm import Session
from db.session import get_db

from schemas.dx_schema import PicUploadResponse

from services import dx_services

router = APIRouter()

db_session = Annotated[Session, Depends(get_db)]

@router.post("/upload_picture", response_model=PicUploadResponse)
async def upload_picture(
    image: UploadFile = File(...),
    db: db_session = None,
):
    """
    사진 파일을 MinIO에 업로드하고 DB에 Image/Metadata/Picture 레코드를 생성합니다.
    """

    result = dx_services.upload_picture(image, db)

    return PicUploadResponse(**result)
