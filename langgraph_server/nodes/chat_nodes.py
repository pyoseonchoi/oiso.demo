# (c) 2026 oiso.ai
from typing import Literal
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END

import json
from states.chat_state import ChatAgentState
from config.llm import chat_model, extraction_model, classification_model
from prompts.chat_prompts import get_query_understanding_prompt, get_main_agent_prompt
from tools.db_tools import search_nearby_stores
from tools.vision_tools import analyze_menu_image


# 툴 바인딩
tools = [search_nearby_stores, analyze_menu_image]
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
            "needs_menu_ocr": False,
            "needs_order_flow": False,
            "image_intent": "none",
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
        "needs_menu_ocr": bool(parsed.get("needs_menu_ocr", False)),
        "needs_order_flow": bool(parsed.get("needs_order_flow", False)),
        "image_intent": str(parsed.get("image_intent", "none")).strip() or "none",
        "assistant_hint": str(parsed.get("assistant_hint", "")).strip(),
    }


def get_image_attachment_urls(state: ChatAgentState) -> list[str]:
    """Return image URLs from chat attachments that can be sent to the LLM."""
    urls = []
    for attachment in state.get("attachments", []):
        if attachment.get("type") != "image":
            continue

        url = attachment.get("data_url") or attachment.get("url")
        if not url:
            continue

        urls.append(url)

    return urls


def build_main_agent_messages(state: ChatAgentState, sys_msg: SystemMessage) -> list:
    """
    Build messages for main_agent.

    The persisted LangGraph messages remain text-only for query_understanding.
    Only the last HumanMessage is converted to multimodal content at invoke time.
    """
    messages = [
        m for m in state["messages"]
        if not isinstance(m, SystemMessage)
    ]
    image_urls = get_image_attachment_urls(state)

    if not image_urls:
        return [sys_msg] + messages

    rebuilt_messages = list(messages)
    for idx in range(len(rebuilt_messages) - 1, -1, -1):
        msg = rebuilt_messages[idx]
        if not isinstance(msg, HumanMessage):
            continue

        text = msg.content if isinstance(msg.content, str) else ""
        content = [{"type": "text", "text": text or "Please analyze the attached image."}]
        content.extend(
            {"type": "image_url", "image_url": {"url": url}}
            for url in image_urls
        )
        rebuilt_messages[idx] = HumanMessage(content=content)
        break

    return [sys_msg] + rebuilt_messages


# ----------------- 노드(Node) 정의 -----------------

def call_query_understanding(state: ChatAgentState):
    messages = state["messages"]
    

    # HumanMessage를 [{type: text, ...}, {type: image_url, ...}] 형식
    # -> list형태 방어 로직
   
    user_input = ""
    for msg in reversed(messages):
        if isinstance(msg, HumanMessage):
            # content가 multimodal list일 경우 텍스트만 추출
            if isinstance(msg.content, list):
                user_input = " ".join(
                    block.get("text", "")
                    for block in msg.content
                    if isinstance(block, dict) and block.get("type") == "text"
                ).strip()
            else:
                user_input = msg.content
            break
    
    # 이미지 첨부 유무를 텍스트 힌트로 주입
    # -> query_understanding LLM이 image_intent / needs_menu_ocr 분류를 더 정확하게 수행
    image_urls = get_image_attachment_urls(state)
    if image_urls:
        user_input = (
            f"[첨부 이미지 {len(image_urls)}장 있음]\n"
            + (user_input or "(텍스트 없음)")
        )
            
    # LLM에게 쿼리의 핵심 단어 정제를 요청 (프롬프트 주입)
    sys_msg = get_query_understanding_prompt()
    enhancer_msg = [sys_msg, HumanMessage(content=user_input)]
    
    response = classification_model.invoke(enhancer_msg)
    understanding = parse_query_understanding(response.content)

    normalized_tags = understanding["normalized_tags"]

    return {
        "enhanced_query": normalized_tags,
        "intent": understanding["intent"],
        "normalized_tags": normalized_tags,
        "confidence": understanding["confidence"],
        "needs_location_search": understanding["needs_location_search"],
        "needs_menu_ocr": understanding["needs_menu_ocr"],
        "needs_order_flow": understanding["needs_order_flow"],
        "image_intent": understanding["image_intent"],
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
    attachments = state.get("attachments") or []

    sys_msg = get_main_agent_prompt(
        user_language=user_lang,
        enhanced_query=enhanced_q,
        client_lat=state.get("client_lat", 0.0),
        client_lng=state.get("client_lng", 0.0),
        intent=state.get("intent", "clarification_needed"),
        normalized_tags=state.get("normalized_tags", []),
        confidence=state.get("confidence", 0.0),
        needs_location_search=state.get("needs_location_search", False),
        needs_menu_ocr=state.get("needs_menu_ocr", False),
        needs_order_flow=state.get("needs_order_flow", False),
        image_intent=state.get("image_intent", "none"),
        ocr_result=state.get("ocr_result"),
        has_valid_location=state.get("has_valid_location", False),
        assistant_hint=state.get("assistant_hint", ""),
        attachments=attachments,
    )

    messages = build_main_agent_messages(state, sys_msg)

    response = model_with_tools.invoke(messages)


    # ── 플레이스홀더 → 실제 data_url 교체 ──────────────────────
    # LLM이 __ATTACHMENT_IMAGE_0__ 을 인자로 출력하면 실제 이미지 URL로 교체
    image_urls = get_image_attachment_urls(state)
    if response.tool_calls and image_urls:
        for tc in response.tool_calls:
            if tc["name"] == "analyze_menu_image":
                arg_url = tc["args"].get("image_data_url", "")
                if "__ATTACHMENT_IMAGE_" in arg_url:
                    try:
                        idx = int(
                            arg_url
                            .replace("__ATTACHMENT_IMAGE_", "")
                            .replace("__", "")
                        )
                    except ValueError:
                        idx = 0
                    if idx < len(image_urls):
                        tc["args"]["image_data_url"] = image_urls[idx]


    return {"messages": [response]}



# ----------------- 라우팅 함수 -----------------

def should_continue(state: ChatAgentState) -> Literal["tools", "__end__"]:
    messages = state["messages"]
    last_message = messages[-1]
    
    if getattr(last_message, 'tool_calls', None):
        return "tools"
    
    return END
