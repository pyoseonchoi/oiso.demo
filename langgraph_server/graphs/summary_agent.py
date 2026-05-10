# (c) 2026 oiso.ai
from langgraph.graph import StateGraph, START, END
from states.summary_state import SummaryAgentState


def placeholder(state: SummaryAgentState):
    """TODO: Summary 로직으로 교체"""
    return state


workflow = StateGraph(SummaryAgentState)
workflow.add_node("placeholder", placeholder)
workflow.add_edge(START, "placeholder")
workflow.add_edge("placeholder", END)

graph = workflow.compile()
