# (c) 2026 oiso.ai
from langchain.messages import SystemMessage

def closure_llm_call(model_that_has_tools):
    def llm_call(state: dict):
        return {
            "messages": [
                model_that_has_tools.invoke(
                    [
                        SystemMessage(
                            content="You act as a travel agent who communicates in the user's speaking language. To bring the journey to life, you retain the original names of local attractions, ensuring the authentic atmosphere of the trip shines through."
                        )
                    ]
                    + state["messages"]
                )
            ],
            "llm_calls": state.get('llm_calls', 0) + 1
        }
    
    return llm_call