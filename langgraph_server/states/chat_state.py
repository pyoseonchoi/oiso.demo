# (c) 2026 oiso.ai
from typing import TypedDict, Annotated, Sequence, Optional, Literal, NotRequired
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

# intent 값을 타입으로 고정 — LLM이 임의 문자열 못 뱉게
IntentType = Literal[
    "food_identification",    # "빨갛고 긴 떡 요리" 같은 음식 묘사
    "nearby_recommendation",  # "근처 떡볶이 추천해줘" 명시적 위치 기반 요청
    "market_info",            # 시장 일반 정보 질문
    "general_chat",           # 인사, 잡담
    "clarification_needed",   # 너무 모호해서 되물어야 함
]

class ChatAgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    client_lat: float
    client_lng: float
    user_language: str
    enhanced_query: list[str]  # 쿼리 강화 에이전트가 뽑아낸 태그(명사) 리스트 저장칸

   # ── query_understanding 출력 필드 (신규) ──────────
    intent: NotRequired[IntentType]          # 분류된 의도
    normalized_tags: NotRequired[list[str]]  # 정규화된 한국어 태그 리스트 (예: ["떡볶이", "순대"])
    confidence: NotRequired[float]           # 0.0 ~ 1.0, 낮으면 clarification_needed
    needs_location_search: NotRequired[bool]           # True일 때만 search_nearby_stores 호출
    assistant_hint: NotRequired[str]         # main_agent 프롬프트에 주입할 힌트 문장 

    has_valid_location: NotRequired[bool]              # 0,0 또는 비정상 좌표면 False