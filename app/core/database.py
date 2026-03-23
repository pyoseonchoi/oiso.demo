# app/core/database.py
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# 1. DB 접속 주소입니다. (.env 파일에 숨겨진 DATABASE_URL을 최우선으로 가져옵니다)
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/oiso_db")

# 2. 엔진(Engine): 실제 DB와 연결선을(Connection) 만들어주는 짐꾼입니다.
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# 3. 팩토리(Factory): DB 세션을 공장처럼 찍어내는 역할을 합니다. 
# autocommit=False 는 개발자인 우리가 직접 db.commit() 을 명시해서 안전하게 DB에 반영하겠다는 의미!
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 4. 베이스(Base): 앞으로 만들 모든 DB 모델(Marker, Photo)의 '부모 클래스'가 될 녀석입니다.
Base = declarative_base()

# 5. 의존성 주입(Dependency)용 함수: API 요청이 들어올 때마다 일회용 통로(세션)를 열고, 일이 끝나면 닫아줍니다.
def get_db():
    db = SessionLocal()
    try:
        # yield는 쉽게 말해 "DB통로 잠깐 빌려줄테니 쓰고 돌려줘~" 라는 의미입니다.
        yield db
    finally:
        db.close()
