import os
from fastapi import FastAPI
from contextlib import asynccontextmanager

# LangGraph 원격 서버
from langgraph_sdk import get_client, get_sync_client
from langgraph.pregel.remote import RemoteGraph

# 커스텀 경로들
from core import config

# 라우터들
from crud.api.v1 import v1_routers

# 모델 객체를 홀딩하는 방법
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Booting: LangChain")
    # 모델 불러오는 절차
    graph_instance = "agent" # 기본 이름
    client      = get_client(url=os.environ["LANGGRAPH_URL"], api_key=os.environ["LANGGRAPH_API_KEY"])
    sync_client = get_sync_client(url=os.environ["LANGGRAPH_URL"], api_key=os.environ["LANGGRAPH_API_KEY"])
    app.state.model = RemoteGraph(
        graph_instance,
        client=client,
        sync_client=sync_client
    )
    yield
    print("Turn off: LangChain")

app = FastAPI(lifespan=lifespan)

# 헬로 월드
@app.get("/hello_world/")
async def hello_world():
    """헬로 월드 API입니다."""
    return {"message": "Hello, world!"}

app.include_router(v1_routers.v1_router, prefix="/v1")