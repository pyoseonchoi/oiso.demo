# (c) 2026 oiso.ai
from typing import TypedDict, Annotated, Sequence
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class ChatAgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    client_lat: float
    client_lng: float
    user_language: str
    enhanced_query: str  # 쿼리 강화 에이전트가 뽑아낸 단일 태그(명사) 저장칸
