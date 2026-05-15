# (c) 2026 oiso.ai
import json
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage
from config.llm import extraction_model
from pydantic import BaseModel, Field
from typing import List


# ─── Structured Output 스키마 ─────────────────────────────────
# ocr_nodes.py의 MenuInformation / OCRInformation을 그대로 가져옴
class MenuInformation(BaseModel):
    """Individual menu item information."""
    number: int = Field(description="Menu item number, starting from 1")
    text_in_original_language: str = Field(
        description="Menu name in the original language as shown on the menu"
    )
    text_in_user_language: str = Field(
        description=(
            "Provide a translation of the source text in the user's target language, "
            "consisting of a literal translation followed by a brief, natural paraphrase "
            "or supplementary explanation in parentheses. "
            "If the target language is identical to the source language, "
            "populate this field with the verbatim original text. Exclude the price part."
        )
    )
    price: int | float = Field(
        description=(
            "Identify the menu prices from the source text and represent them "
            "using the currency units and formatting conventions standard to that "
            "specific regional or linguistic context. "
            "ex) Korean Text with 5.0 => It means 5000 Won"
        )
    )


class OCRInformation(BaseModel):
    """Extracted menu items with language metadata."""
    menus: List[MenuInformation] = Field(
        description="List of all extracted menu items from the image"
    )
    user_language: str = Field(description="User's Language")
    original_language: str = Field(description="Source Language")


# ─── Tool 정의 ────────────────────────────────────────────────
# 기존의 OCR Agent 로직을 Tool로 적용 (main agent에서 호출하기 위함)
# 단, Main Agent가 vision으로 이미 메뉴판 여부를 판단한 뒤에 호출하기에, OCR Agent처럼 validate_image_node 검증은 없음
@tool
def analyze_menu_image(image_data_url: str, user_language: str) -> str:
    """
    Analyze a menu/menu-board image and extract structured menu items
    with prices and translations.

    Use this tool ONLY when the user's image appears to be a restaurant
    or cafe menu and the user wants to read, translate, order from,
    or understand the menu items and prices.

    Args:
        image_data_url: The image as a data URL (data:image/...;base64,...).
        user_language: The language to translate menu items into (e.g. "Korean", "English").

    Returns:
        JSON string containing extracted menu items with original text,
        translated text, and prices.
    """
    structured_llm = extraction_model.with_structured_output(OCRInformation)

    message = HumanMessage(content=[
        {
            "type": "text",
            "text": (
                f"Extract all menu items from this menu image. "
                f"For each item provide the original language text, "
                f"a {user_language} translation, and the price."
            ),
        },
        {"type": "image_url", "image_url": {"url": image_data_url}},
    ])

    result = structured_llm.invoke([message])
    return json.dumps(result.model_dump(), ensure_ascii=False)
