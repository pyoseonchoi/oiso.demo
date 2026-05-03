from states.ocr_state import OCRAgentState
from pydantic import BaseModel, Field
from typing import List

from langchain_core.messages import HumanMessage
from prompts import ocr_prompts

from config.llm import extraction_model

# Pydantic 출력 스키마 정의
# LLM이 어떤 형태로 결과를 뱉어야하는지 정의함 (description이 중요 - LLM이 이거 읽고 판단)
class MenuInformation(BaseModel):
    """This field is designated for recording the detailed information of each individual menu item."""
    number: int = Field(description="Menu item number, starting from 1")
    text_in_original_language: str = Field(description="Menu name in the original language as shown on the menu")
    text_in_user_language: str = Field(description="Provide a translation of the source text in the user's target language, consisting of a literal translation followed by a brief, natural paraphrase or supplementary explanation in parentheses. If the target language is identical to the source language, populate this field with the verbatim original text. Exclude the price part.")
    price: int | float = Field(description="""Identify the menu prices from the source text and represent them using the currency units and formatting conventions standard to that specific regional or linguistic context.
                               ex) Korean Text with 5.0 => It means 5000 Won""")

class OCRInformation(BaseModel):
    """This field stores an array of all extracted menu items, the user's target language, and the original source language of the OCR content."""
    menus: List[MenuInformation] = Field(description="List of all extracted menu items from the image")
    user_language: str = Field(description="User's Language")
    original_language: str = Field(description="Source Language")


# OCR 노드 함수 작성

def call_ocr_node(state: OCRAgentState):
    # 이미지 보낼 메시지 구성 -> with_structured_ouput으로 OCROutput 강제 -> 결과를 state에 반환

    # extraction_model 재사용 
    structured_llm = extraction_model.with_structured_output(OCRInformation)
    
    user_lang = state["user_language"] 

    # 이미지 전달 - https://docs.langchain.com/oss/python/langchain/messages#multimodal 참고함
    message = HumanMessage(content= [
        {"type": "text", "text": f"이 메뉴판 이미지에서 메뉴 항목들을 추출해라. 각 메뉴의 원래 언어 텍스트, {user_lang}로 번역한 텍스트, 가격을 구조화해서 반환해라."},
        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{state["image_b64"]}"}},

    ])

    # invoke 이후 결과를 state로 반환

    result = structured_llm.invoke([message])
    return {"ocr_result": result.model_dump()}


def validate_image_node(state: OCRAgentState):
    """
    첨부된 이미지가 메뉴판이 맞는지 검증하는 노드
    """ 

    llm = extraction_model
    system_prompt = ocr_prompts.get_validate_image_prompt()
    
    #State에서 이미지 가져와서 HumanMessage 구성
    human_message = HumanMessage(content=[
        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{state['image_b64']}"}}
    ])
    
    #함께 invoke
    msg = llm.invoke([system_prompt, human_message])

    error_message = ""
    is_valid = True

    result_text = msg.content.strip().upper() 
    
    if "NO" in result_text:
        error_message = "메뉴판 이미지가 아닙니다. 다시 확인해 주세요."
        is_valid = False
    elif "BLURRY" in result_text:
        error_message = "이미지가 너무 흐립니다. 흔들리지 않게 다시 촬영해 주세요."
        is_valid = False
    
    return {"is_valid": is_valid, "error_message": error_message}


def check_validity(state: OCRAgentState) -> str:
    """
    사진이 유효한지 검증하는 gate function
    """

    if state["is_valid"]:
        return "Pass"
    else:
        return "Fail"