# (c) 2026 oiso.ai
from typing import Literal
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END

from states.chat_state import ChatAgentState
from config.llm import chat_model, extraction_model
from prompts.chat_prompts import get_query_enhancer_prompt, get_main_agent_prompt
from tools.db_tools import search_nearby_stores


# 툴 바인딩
tools = [search_nearby_stores]
model_with_tools = chat_model.bind_tools(tools)


# ----------------- 노드(Node) 정의 -----------------

# 쿼리 강화 노드 (Query Enhancer - 선행 에이전트)
def call_query_enhancer(state: ChatAgentState):
    messages = state["messages"]
    
    # 마지막 사용자 메시지(HumanMessage)만 추출하여 노이즈 제거
    user_input = ""
    for msg in reversed(messages):
        if isinstance(msg, HumanMessage):
            user_input = msg.content
            break
            
    # LLM에게 쿼리의 핵심 단어 정제를 요청 (프롬프트 주입)
    sys_msg = get_query_enhancer_prompt()
    enhancer_msg = [sys_msg, HumanMessage(content=user_input)]
    
    # 아주 짧은 단일 키워드(예: "떡볶이")를 반환받음
    response = extraction_model.invoke(enhancer_msg)
    
    return {"enhanced_query": response.content.strip()}


# 메인 노드 (도구 사용 및 답변)
def call_main_agent(state: ChatAgentState):
    user_lang = state.get("user_language", "English")
    enhanced_q = state.get("enhanced_query", "")
    
    sys_msg = get_main_agent_prompt(user_lang, enhanced_q, state.get("client_lat", 0.0), state.get("client_lng", 0.0))
    
    messages = [sys_msg] + [m for m in state["messages"] if not isinstance(m, SystemMessage)]
    
    response = model_with_tools.invoke(messages)
    return {"messages": [response]}


# ----------------- 라우팅 함수 -----------------

def should_continue(state: ChatAgentState) -> Literal["tools", "__end__"]:
    messages = state["messages"]
    last_message = messages[-1]
    
    if getattr(last_message, 'tool_calls', None):
        return "tools"
    
    return END
