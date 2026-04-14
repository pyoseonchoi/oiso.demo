# (c) 2026 oiso.ai
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.types import Command
from dotenv import load_dotenv

load_dotenv("../.env")

# 라우터
from router import router

# 에이전트
from agents.chat import chatbot
from agents.help import ai_summary
from agents.ocr import menu_reader

# 커스텀 클래스
from custom_classes.custom_msg_state import CustomMessagesState

# 아래 코드들은 참고용으로 놔 둠
# 모델을 아마 langchain_huggingface
# https://docs.langchain.com/oss/python/integrations/providers/overview
# 를 활용해서 Qwen 3.4 4B? 이런 작은 모델에서도 돌아가는걸 보여서
# 보통 공공기관이 이런 멋들어진 언어모델 안쓰고 그냥 질문-답변 기반 챗봇 쓰는 이유가 다 비용 문제인데
# 그게 좀 합리적인 수준에서 해결된다는걸 어필해보자
# model         = ChatOpenAI(model="gpt-4.1-mini", temperature=0.7)
# text_embedder = embedder_initialize()

# # 선언한 툴들을 이렇게 넣어줘야 하는듯
# tools = [closure_rag_object_searching_pipelining_entry(text_embedder), rag_user_location_weather, rag_route_public_transport, translate_ragged_data]
# tool_node = ToolNode(tools)

# # 툴 꽂아넣기
# model = model.bind_tools(tools)

# https://reference.langchain.com/python/langgraph/graph/state/StateGraph?_gl=1*ejzyiq*_gcl_au*MTE1NzA5Mjc1MS4xNzczOTIxNzYw*_ga*MTMyOTk2MjgwNC4xNzczOTIxNzYx*_ga_47WX3HKKY2*czE3NzQ5NDY5NzMkbzIxJGcxJHQxNzc0OTQ4MTU3JGozOSRsMCRoMA..
workflow = StateGraph(CustomMessagesState)

# 파서 기반 라우팅 노드
workflow.add_node("Router", router.route_by_mode)

# 라우팅을 받는 에이전트 노드들
workflow.add_node("Agent[Chat]", chatbot.agent_call)
workflow.add_node("Agent[Help]", ai_summary.agent_call)
workflow.add_node("Agent[OCR]", menu_reader.agent_call)

workflow.add_edge(START, "Router")

# https://reference.langchain.com/python/langgraph/graph/state/StateGraph/add_conditional_edges 
# 참고
# workflow.add_conditional_edges(
#     "main_model",
#     should_continue,
#     ["tool_n", END]
# )

app = workflow.compile()