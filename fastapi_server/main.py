from contextlib import asynccontextmanager
from fastapi.concurrency import run_in_threadpool
from dotenv import load_dotenv
from sqlalchemy import text
from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import httpx

# Load environment variables
load_dotenv()

# App-specific imports
from api.v1.api import v1_router
from core.storage import init_storage
from db.base import Base
from db.session import get_engine
from core.storage import get_s3_client, get_bucket_name
from core.config import settings
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


@app.get("/ready", tags=["Health"])
async def readiness_check():
    checks = {}

    # DB
    try:
        def check_db():
            engine = get_engine()
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))

        await run_in_threadpool(check_db)
        checks["db"] = "ok"
    except Exception as e:
        checks["db"] = f"failed: {type(e).__name__}"

    # S3 / MinIO
    try:
        def check_storage():
            client = get_s3_client()
            client.head_bucket(Bucket=get_bucket_name())

        await run_in_threadpool(check_storage)
        checks["storage"] = "ok"
    except Exception as e:
        checks["storage"] = f"failed: {type(e).__name__}"

    # LangGraph
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            response = await client.get(f"{settings.LANGGRAPH_SERVER_URL}/ok")
            response.raise_for_status()

        checks["langgraph"] = "ok"
    except Exception as e:
        checks["langgraph"] = f"failed: {type(e).__name__}"

    if all(value == "ok" for value in checks.values()):
        return {"status": "ready", "checks": checks}

    raise HTTPException(
        status_code=503,
        detail={"status": "not_ready", "checks": checks},
    )

