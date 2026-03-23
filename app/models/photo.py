# app/models/photo.py
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class Photo(Base):
    """
    [DB 테이블: photos]
    마커와 연동된 사진 정보 저장
    """
    __tablename__ = "photos"

    id = Column(Integer, primary_key=True, index=True)
    
    marker_id = Column(Integer, ForeignKey("markers.id"), nullable=False)
    s3_url = Column(String(500), nullable=False)
    
    # TODO: AI 모델 분석을 통한 임베딩 벡터/특징 컬럼(pgvector 등) 향후 추가 필요
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    marker = relationship("Marker", back_populates="photos")
