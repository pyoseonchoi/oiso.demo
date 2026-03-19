# (c) 2026 oiso.ai
from langchain.messages import SystemMessage

# add_node는 오로지 (state: dict, context: dict | None)임 그래서 이런 식으로 커스텀 인자를 줄려면
# 래퍼로 이렇게 감싸야 함
def closure_main_llm_call(model_that_has_tools):
    def llm_call(state: dict):
        return {
            "messages": [
                model_that_has_tools.invoke(
                    [
                        SystemMessage(
                            content="""You act as a travel agent who communicates in the user's speaking language. 
To bring the journey to life, you retain the original names of local attractions, ensuring the authentic atmosphere of the trip shines through."""
                        )
                    ]
                    + state["messages"]
                )
            ],
            "llm_calls": state.get('llm_calls', 0) + 1
        }
    
    return llm_call

def closure_translator_llm_call(model_that_translates):
    def llm_call(state: dict):
        return {
            "messages": [
                model_that_translates.invoke(
                    [
                        SystemMessage(
                            content="""You will receive input in the following format:

<user_language>
The user's native language
</user_language>
<translation_target>
The content to be translated
</translation_target>

Your task is to translate the text within the <translation_target> tags into the language specified in the <user_language> tags. 
Do not provide any text, explanations, or commentary other than the translation itself."""
                        )
                    ]
                    + state["messages"]
                )
            ],
            "llm_calls": state.get('llm_calls', 0) + 1
        }
    
    return llm_call