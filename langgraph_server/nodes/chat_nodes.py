# (c) 2026 oiso.ai
from typing import Literal
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END

import json
from states.chat_state import ChatAgentState
from config.llm import chat_model, extraction_model
from prompts.chat_prompts import get_query_understanding_prompt, get_main_agent_prompt
from tools.db_tools import search_nearby_stores


# 툴 바인딩
tools = [search_nearby_stores]
model_with_tools = chat_model.bind_tools(tools)



# 헬퍼 함수 정의
def has_valid_location(lat: float | None, lng: float | None) -> bool:
    """좌표가 실제 사용 가능한 값인지 검증."""
    if lat is None or lng is None:
        return False
    if lat == 0.0 and lng == 0.0:
        return False
    return -90.0 <= lat <= 90.0 and -180.0 <= lng <= 180.0


def parse_query_understanding(raw_content: str) -> dict:
    """
    LLM이 반환한 JSON 문자열을 파싱한다.
    """
    try:
        parsed = json.loads(raw_content)
    except json.JSONDecodeError:
        return {
            "intent": "clarification_needed",
            "normalized_tags": [],
            "confidence": 0.0,
            "needs_location_search": False,
            "assistant_hint": "Ask a short clarification question.",
        }

    intent = parsed.get("intent", "clarification_needed")
    if intent not in {
        "food_identification",
        "nearby_recommendation",
        "market_info",
        "general_chat",
        "clarification_needed",
    }:
        intent = "clarification_needed"

    try:
        confidence = float(parsed.get("confidence", 0.0))
    except (TypeError, ValueError):
        confidence = 0.0

    confidence = max(0.0, min(confidence, 1.0))

    # Parse normalized_tags as a list of strings
    raw_tags = parsed.get("normalized_tags", [])
    if isinstance(raw_tags, str):
        normalized_tags = [raw_tags.strip()] if raw_tags.strip() else []
    elif isinstance(raw_tags, list):
        normalized_tags = [str(t).strip() for t in raw_tags if str(t).strip()]
    else:
        normalized_tags = []

    return {
        "intent": intent,
        "normalized_tags": normalized_tags,
        "confidence": confidence,
        "needs_location_search": bool(parsed.get("needs_location_search", False)),
        "assistant_hint": str(parsed.get("assistant_hint", "")).strip(),
    }


# ----------------- 노드(Node) 정의 -----------------

def call_query_understanding(state: ChatAgentState):
    messages = state["messages"]
    
    # 마지막 사용자 메시지(HumanMessage)만 추출하여 노이즈 제거
    user_input = ""
    for msg in reversed(messages):
        if isinstance(msg, HumanMessage):
            user_input = msg.content
            break
            
    # LLM에게 쿼리의 핵심 단어 정제를 요청 (프롬프트 주입)
    sys_msg = get_query_understanding_prompt()
    enhancer_msg = [sys_msg, HumanMessage(content=user_input)]
    
    response = extraction_model.invoke(enhancer_msg)
    understanding = parse_query_understanding(response.content)

    normalized_tags = understanding["normalized_tags"]

    return {
        "enhanced_query": normalized_tags,
        "intent": understanding["intent"],
        "normalized_tags": normalized_tags,
        "confidence": understanding["confidence"],
        "needs_location_search": understanding["needs_location_search"],
        "has_valid_location": has_valid_location(
            state.get("client_lat"),
            state.get("client_lng"),
        ),
        "assistant_hint": understanding["assistant_hint"],
    }


# 메인 노드 (도구 사용 및 답변)
def call_main_agent(state: ChatAgentState):
    user_lang = state.get("user_language", "English")
    enhanced_q = state.get("enhanced_query", [])

    sys_msg = get_main_agent_prompt(
        user_language=user_lang,
        enhanced_query=enhanced_q,
        client_lat=state.get("client_lat", 0.0),
        client_lng=state.get("client_lng", 0.0),
        intent=state.get("intent", "clarification_needed"),
        normalized_tags=state.get("normalized_tags", []),
        confidence=state.get("confidence", 0.0),
        needs_location_search=state.get("needs_location_search", False),
        has_valid_location=state.get("has_valid_location", False),
        assistant_hint=state.get("assistant_hint", ""),
    )

    messages = [sys_msg] + [
        m for m in state["messages"] if not isinstance(m, SystemMessage)
    ]

    response = model_with_tools.invoke(messages)
    return {"messages": [response]}



# ----------------- 라우팅 함수 -----------------

def should_continue(state: ChatAgentState) -> Literal["tools", "__end__"]:
    messages = state["messages"]
    last_message = messages[-1]
    
    if getattr(last_message, 'tool_calls', None):
        return "tools"
    
    return END
