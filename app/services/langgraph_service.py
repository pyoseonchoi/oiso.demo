import os
from typing import Annotated, TypedDict, Optional, List
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

# os.environ["LANGCHAIN_TRACING_V2"] = "true"
# os.environ["LANGCHAIN_PROJECT"] = "oiso-alpha-01"

class GraphState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    user_language: str
    rag_language: Optional[str]
    retrieved_context: Optional[str]
    translated_context: Optional[str]

main_llm = ChatOpenAI(model="gpt-4.1-mini", streaming=True).with_config({"run_name": "main_model"})
nano_llm = ChatOpenAI(model="gpt-4o-mini", streaming=False)


async def retrieve_node(state: GraphState):
    """
    RAG 컨텍스트 검색 라우터
    """
    latest_query = state["messages"][-1].content
    
    # TODO: 실제 vector_db.similarity_search 연동
    fetched_doc = "소문난 떡볶이집: 이곳은 아주 매운 떡볶이가 일품이며, 가격은 3000원입니다."
    doc_lang = "ko"
    
    return {
        "retrieved_context": fetched_doc,
        "rag_language": doc_lang
    }


def translation_condition(state: GraphState) -> str:
    """
    문서 언어와 사용자 설정 언어를 비교하여 라우팅합니다.
    """
    user_lang = state.get("user_language", "ko")
    rag_lang = state.get("rag_language", "ko")
    
    if user_lang.lower() != rag_lang.lower():
        return "translate"
    return "main"


async def translate_node(state: GraphState):
    """
    컨텍스트 기계 번역 서브 에이전트
    """
    source_text = state["retrieved_context"]
    target_lang = state["user_language"]
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a fast and accurate professional translator. Translate the following text into {target_lang}. Return ONLY the translated text."),
        ("user", "{text}")
    ])
    
    chain = prompt | nano_llm
    response = await chain.ainvoke({"target_lang": target_lang, "text": source_text})
    
    return {"translated_context": response.content}


async def main_agent_node(state: GraphState):
    """
    최종 챗봇 응답 생성 메인 에이전트
    """
    context = state.get("translated_context") or state.get("retrieved_context")
    user_lang = state.get("user_language", "ko")
    
    system_msg = SystemMessage(
        content=f"You are a friendly traditional market guide. "
                f"If the user is just greeting or making small talk, respond naturally without using the context. "
                f"But if the user asks for market information or recommendations, you MUST use the provided Context below to answer.\n\n"
                f"Context: {context}\n\n"
                f"Must respond in this language: {user_lang}."
    )
    
    messages = [system_msg] + state["messages"]
    response = await main_llm.ainvoke(messages)
    return {"messages": [response]}


workflow = StateGraph(GraphState)

workflow.add_node("retrieve", retrieve_node)
workflow.add_node("translate", translate_node)
workflow.add_node("main", main_agent_node)

workflow.add_edge(START, "retrieve")
workflow.add_conditional_edges(
    "retrieve",
    translation_condition,
    {
        "translate": "translate",
        "main": "main"
    }
)
workflow.add_edge("translate", "main")
workflow.add_edge("main", END)

# TODO: 상용화 시 PostgreSQL (AsyncPostgresSaver) 연동으로 교체 추천
memory = MemorySaver()
app_graph = workflow.compile(checkpointer=memory)
