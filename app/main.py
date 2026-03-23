# app/main.py
from fastapi import FastAPI
from app.api.endpoints import markers
from app.api.endpoints import chat
from app.core.database import engine, Base
from app.models import marker, photo # 모델 모양을 파이썬이 미리 인지하도록 불러옵니다.

# 🌟 FastAPI 서버가 켜질 때 DB에 "markers", "photos" 등의 테이블이 없으면 자동으로 뚝딱 만들어주는 마법의 코드!
Base.metadata.create_all(bind=engine)

# 1. FastAPI 애플리케이션의 뼈대(객체)를 만듭니다. 
app = FastAPI(title="UD-AMG Traditional Market Mapper API", version="1.0.0")

# 2. 다른 폴더(api/endpoints/markers.py)에 쪼개어 만든 라우터 조각들을 이 메인 앱에 찰칵 끼워 맞춥니다.
app.include_router(markers.router, prefix="/api/markers", tags=["Markers"])
app.include_router(chat.router, prefix="/api/ai", tags=["AI 챗봇"])

@app.get("/")
def root_check():
    """
    서버가 잘 켜졌는지 브라우저에서 확인해볼 수 있는 아주 간단한 헬스체크용 엔드포인트입니다.
    """
    return {"message": "지도 서버가 정상 가동중입니다! 환영합니다."}
