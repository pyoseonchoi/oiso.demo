from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# Load environment variables
load_dotenv()

# App-specific imports
from api.v1.api import v1_router
from core.storage import init_storage
from db.base import Base
from db.session import engine
from exceptions.base import AppException
from exceptions.handlers import (
    app_exception_handler,
    http_exception_handler,
    validation_exception_handler,
    unexpected_exception_handler,
)
from models import mx_model

# Database initialization -> Alembic으로 대체
# try:
#     Base.metadata.create_all(bind=engine)
# except Exception as e:
#     print(f"[WARNING] Database connection failed (server will continue): {e}")

# App lifecycle configuration
@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        init_storage()
    except Exception as e:
        print(f"[WARNING] MinIO/S3 connection failed (server will continue): {e}")
    yield

# Initialize FastAPI app
app = FastAPI(lifespan=lifespan)

# Middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handlers
app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, unexpected_exception_handler)

# Routers
app.include_router(v1_router, prefix="/v1")  # 신버전 라우터 (dx / ax / mx)

@app.get("/health", tags=["Health"])
async def health_check():
    """AWS 등에서 서버 상태를 확인하기 위한 헬스 체크 엔드포인트"""
    return {"status": "ok"}

