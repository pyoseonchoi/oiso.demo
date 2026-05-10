# (c) 2026 oiso.ai
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode

from states.chat_state import ChatAgentState
from nodes.chat_nodes import call_query_enhancer, call_main_agent, should_continue
from tools.db_tools import search_nearby_stores


# 툴 노드
tools = [search_nearby_stores]
tool_node = ToolNode(tools)

# 그래프 조립
workflow = StateGraph(ChatAgentState)

workflow.add_node("query_enhancer", call_query_enhancer)
workflow.add_node("main_agent", call_main_agent)
workflow.add_node("tools", tool_node)

# 스타트 -> 쿼리 강화 -> 메인 에이전트
workflow.add_edge(START, "query_enhancer")
workflow.add_edge("query_enhancer", "main_agent")

# 메인 에이전트 -> (툴 호출 or 종료)
workflow.add_conditional_edges(
    "main_agent",
    should_continue,
    {"tools": "tools", END: END}
)

# 툴 실행 후 -> 다시 메인 에이전트
workflow.add_edge("tools", "main_agent")

graph = workflow.compile()
