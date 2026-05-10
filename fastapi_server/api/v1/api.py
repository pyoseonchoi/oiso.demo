from fastapi import APIRouter
from api.v1.endpoints import dx, ax, mx

# ── 설계도 따라서 라우터 수정 (/v1/ 하위) ──────────────────────────────────────
v1_router = APIRouter()

v1_router.include_router(
    dx.router,
    prefix="/dx",
    tags=["dx - Data eXperience"]
)

v1_router.include_router(
    ax.router,
    prefix="/ax",
    tags=["ax - AI eXperience"]
)

v1_router.include_router(
    mx.router,
    prefix="/mx",
    tags=["mx - Map eXperience"]
)
