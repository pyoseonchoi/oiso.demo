from fastapi import APIRouter
from backend.crud.api.v1.endpoints.chat import chat

v1_router = APIRouter()

v1_router.include_router(chat.chat_router, prefix="/chat")