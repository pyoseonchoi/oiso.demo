from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from llm_configs.sysmsg import chat_sys_prompt
from custom_classes.custom_msg_state import CustomMessagesState

import os

model = create_agent(
    model=ChatOpenAI(
        model=os.environ["AGENT_MODEL"],
        temperature=os.environ["AGENT_TEMP"],
    ),
    system_prompt=chat_sys_prompt
)

def agent_call(state: CustomMessagesState):
    result = model.invoke(
        state
    )
    
    return {"messages": result["messages"][-1]}