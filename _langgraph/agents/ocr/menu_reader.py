from langchain.agents import create_agent
from pydantic import BaseModel, Field
from typing import List
from llm_configs.sysmsg import picnorder_sys_prompt
from langchain_openai import ChatOpenAI
from custom_classes.custom_msg_state import CustomMessagesState

import os

class MenuInformation(BaseModel):
    """This field is designated for recording the detailed information of each individual menu item."""
    number: int = Field(description="A zero-based index for each menu item.")
    text_in_original_language: str = Field(description="The verbatim, unedited source text for each individual menu item. Exclude the price part.")
    text_in_user_language: str = Field(description="Provide a translation of the source text in the user's target language, consisting of a literal translation followed by a brief, natural paraphrase or supplementary explanation in parentheses. If the target language is identical to the source language, populate this field with the verbatim original text. Exclude the price part.")
    price: int | float = Field(description="""Identify the menu prices from the source text and represent them using the currency units and formatting conventions standard to that specific regional or linguistic context.
                               ex) Korean Text with 5.0 => It means 5000 Won""")

class OCRInformation(BaseModel):
    """This field stores an array of all extracted menu items, the user's target language, and the original source language of the OCR content."""
    menus: List[MenuInformation] = Field(description="")
    user_language: str = Field(description="User's Language")
    original_language: str = Field(description="Source Language")

model = create_agent(
    model=ChatOpenAI(
        model=os.environ["AGENT_MODEL"],
        temperature=os.environ["AGENT_TEMP"]
    ),
    response_format=OCRInformation,
    system_prompt=picnorder_sys_prompt
)

def agent_call(state: CustomMessagesState):
    result = model.invoke(
        state
    )
    
    return {"messages": result["messages"][-1]}