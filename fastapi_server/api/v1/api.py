from fastapi import APIRouter
from api.v1.endpoints import bookmarks, posts, chat, upload, marker

api_router = APIRouter()

api_router.include_router(
    bookmarks.router,
    prefix="/bookmarks",
    tags=["bookmarks"]
)

api_router.include_router(
    posts.router,
    prefix="/posts",
    tags=["posts"]
)

api_router.include_router(
    chat.router,
    prefix="/chat",
    tags=["chat"]
)

api_router.include_router(
    upload.router,
    prefix="/upload",
    tags=["upload"]
)

api_router.include_router(
    marker.router,
    prefix="/marker",
    tags=["marker"]
)