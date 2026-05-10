# (c) 2026 oiso.ai
from langgraph.graph import StateGraph, START, END
from states.ocr_state import OCRAgentState
from nodes.ocr_nodes import call_ocr_node, validate_image_node, check_validity


# 그래프 조립
workflow = StateGraph(OCRAgentState)

workflow.add_node("ocr_agent", call_ocr_node)
workflow.add_node("validate_image", validate_image_node)

#TODO: 흐름 강화

workflow.add_edge(START, "validate_image")

workflow.add_conditional_edges(
    "validate_image", check_validity, {"Pass": "ocr_agent", "Fail": END}
)



graph = workflow.compile()
