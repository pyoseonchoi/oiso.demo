from custom_classes.custom_msg_state import CustomMessagesState
from langgraph.types import Command
from langgraph.graph import END

PICNORDER_CLASSIFIER = """<|ocr|>"""
CHATAGENT_CLASSIFIER = """<|chat|>"""
AISUMMARY_CLASSIFIER = """<|aihelp|>"""

def route_by_mode(state: CustomMessagesState) -> Command:
    """
    - https://reference.langchain.com/python/langchain-core/messages/utils/AnyMessage
    - https://reference.langchain.com/python/langgraph/graph/state/StateGraph
    - https://reference.langchain.com/python/langgraph/graph/state/StateGraph/add_node
    - https://reference.langchain.com/python/langchain-core/messages/human/HumanMessage
    - https://docs.langchain.com/oss/python/langgraph/graph-api#messagesstate
    이 구조를 이해하기 위해서 참고해야 할 것 들
    """
    mode = state["mode"]

    if mode == "ocr":
        return Command(
            goto="Agent[OCR]"
        )
    elif mode == "chat":
        return Command(
            goto="Agent[Chat]"
        )
    elif mode == "help":
        return Command(
            goto="Agent[Help]"
        )

    return END