# app/models/marker.py
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from geoalchemy2 import Geometry  # DB 공간 연산의 꽃! PostGIS를 다루기 위한 마법 지팡이입니다.
from app.core.database import Base

class Marker(Base):
    """
    [DB 테이블: markers]
    지도 상에 찍힐 각각의 가게(분식, 빵집 등)를 담당하는 테이블 구조입니다.
    """
    # 실제 데이터베이스에 만들어질 테이블 이름
    __tablename__ = "markers"

    id = Column(Integer, primary_key=True, index=True)
    
    # 멘토의 팁: category(상호명 대체)에 index=True 를 달면, 나중에 "빵집만 보여줘!" 할 때 탐색 속도가 엄청 빠릅니다.
    category = Column(String(50), nullable=False, index=True)
    
    # 🔥 핵심: 단순 Float로 위도경도를 나누지 않고 PostGIS의 공간 데이터인 Geometry('POINT')로 묶어버립니다.
    # srid=4326 은 위도/경도를 뜻하는 전세계 공통 규칙(WGS 84 좌표계) 번호입니다.
    location = Column(Geometry(geometry_type='POINT', srid=4326), nullable=False)
    
    # 마커가 언제 생성되었는지(서버 기준 시간) 자동으로 콕 찍어줍니다.
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 1:다(1:N) 관계: "가게 1곳(마커)에 여러 장의 등록 사진이 있을 수 있다"는 걸 파이썬 코드로 지정!
    # cascade="all, delete-orphan": 마커가 DB에서 삭제되면, 딸려있던 쓸모없는 사진 정보도 같이 파괴하라는 깔끔한 옵션입니다.
    photos = relationship("Photo", back_populates="marker", cascade="all, delete-orphan")
