import json
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from langchain_core.messages import HumanMessage
from app.services.langgraph_service import app_graph

router = APIRouter()

class ChatRequest(BaseModel):
    session_id: str
    user_language: str
    message: str

@router.post("/chat", summary="다국어 스트리밍 AI 챗봇")
async def chat_stream(req: ChatRequest):
    """
    LangGraph 이벤트 스트리밍 방식(SSE)로 프론트엔드에 응답을 전송합니다.
    """
    initial_state = {
        "messages": [HumanMessage(content=req.message)],
        "user_language": req.user_language
    }
    
    config = {
        "configurable": {
            "thread_id": req.session_id
        }
    }

    async def event_generator():
        try:
            async for event in app_graph.astream_events(initial_state, config, version="v2"):
                kind = event["event"]
                
                if kind == "on_chat_model_stream" and event["name"] == "main_model":
                    chunk = event["data"]["chunk"]
                    if chunk.content:
                        yield f"data: {json.dumps({'content': chunk.content}, ensure_ascii=False)}\n\n"
                        
            yield "data: [DONE]\n\n"
            
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
