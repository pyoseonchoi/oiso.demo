from fastapi import APIRouter, Depends, HTTPException, UploadFile
from typing import Annotated
from typing import Dict
from schemas.upload_schema import FileUploadResponse
from services import upload_service
from sqlalchemy.orm import Session
from db.session import get_db

router = APIRouter()

db_session = Annotated[Session, Depends(get_db)]

@router.post("/", response_model=FileUploadResponse)
async def upload_file(file: UploadFile, db: db_session):
    if not file.filename:
        raise HTTPException(status_code=400, detail = "파일명이 없습니다.")
    
    return upload_service.save_file(file, db)    
