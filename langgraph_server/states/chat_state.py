# (c) 2026 oiso.ai
from typing import TypedDict, Annotated, Sequence, Literal, NotRequired
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

IntentType = Literal[
    "food_identification",
    "nearby_recommendation",
    "market_info",
    "general_chat",
    "clarification_needed",
]


class ChatAgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    client_lat: float
    client_lng: float
    user_language: str
    enhanced_query: list[str]
    attachments: NotRequired[list[dict]]

    intent: NotRequired[IntentType]
    normalized_tags: NotRequired[list[str]]
    confidence: NotRequired[float]
    needs_location_search: NotRequired[bool]
    needs_menu_ocr: NotRequired[bool]
    needs_order_flow: NotRequired[bool]
    image_intent: NotRequired[str]
    ocr_result: NotRequired[dict]
    ui_outputs: NotRequired[list[dict]]
    assistant_hint: NotRequired[str]
    has_valid_location: NotRequired[bool]
