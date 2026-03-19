# (c) 2026 oiso.ai
from typing import Literal
from langchain.messages import HumanMessage, ToolMessage
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import ToolNode
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.types import Command

# 환경변수 이렇게 로드
from dotenv import load_dotenv

# 툴들 여기서 로드
from tools import *

# 시스템 프롬프트 여기서 로드
from sysmsg import *

# 텍스트 임베더 로드
from embeddings_text import *

# 이걸 해야 비로소 환경변수 로드
load_dotenv()

# 모델을 아마 langchain_huggingface
# https://docs.langchain.com/oss/python/integrations/providers/overview
# 를 활용해서 Qwen 3.4 4B? 이런 작은 모델에서도 돌아가는걸 보여서
# 보통 공공기관이 이런 멋들어진 언어모델 안쓰고 그냥 질문-답변 기반 챗봇 쓰는 이유가 다 비용 문제인데
# 그게 좀 합리적인 수준에서 해결된다는걸 어필해보자
model         = ChatOpenAI(model="gpt-4.1-mini", temperature=0.7)
translator    = ChatOpenAI(model="gpt-4.1-nano", temperature=0.7) # 번역용
text_embedder = embedder_initialize()

# 선언한 툴들을 이렇게 넣어줘야 하는듯
tools = [closure_rag_object_searching_pipelining_entry(text_embedder), rag_user_location_weather, rag_route_public_transport]
tool_node = ToolNode(tools)

# 툴 꽂아넣기
model = model.bind_tools(tools)

def should_continue(state: MessagesState) -> Literal["tool_n", END]:
    messages = state["messages"]
    last_message = messages[-1] # 파이썬에서 -1은 마지막

    # 즉 LLM의 마지막 결정이 도구 호출이냐 아니냐를 보는거임
    # 왜냐하면 도구 호출은 LLM의 응답의 일종이기 때문임
    # 그래서 유저 인터랙션을 END할지 아니면 도구 호출을 한걸 반환해줄지 보는거임
    # 왜냐하면 루프를 돌기 때문임 예를 들어 사칙연산을 다 도구 호출해서 시킨다면
    # 계속 돌다가 END하는거지
    # 유저 응답에 대한 반환을 END하는게 아님
    if last_message.tool_calls:
        return "tool_n"

    return END

workflow = StateGraph(MessagesState)
workflow.add_node("main_model", closure_main_llm_call(model))
workflow.add_node("tool_n", tool_node)

workflow.add_edge(START, "main_model")

# https://reference.langchain.com/python/langgraph/graph/state/StateGraph/add_conditional_edges 
# 참고
workflow.add_conditional_edges(
    "main_model",
    should_continue,
    ["tool_n", END]
)

app = workflow.compile()