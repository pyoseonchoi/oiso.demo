# (c) 2026 oiso.ai
import os
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage

# .env 로드
load_dotenv(".env")

# 새 구조의 chat_agent 그래프를 불러옵니다.
from graphs.chat_agent import graph


def run_test():
    print("🤖 --- LangGraph Chat Agent 테스트 --- 🤖")
    print("시나리오: 외국인이 영어로 '긴 빨간 떡 파는 곳 찾아줘'라고 질문")
    
    # 1. 초기 메시지와 상태(State) 값 설정
    initial_state = {
        "messages": [HumanMessage(content="I saw people eating long red rice cakes, where can I get those nearby?")],
        "client_lat": 35.8690,
        "client_lng": 128.5930,
        "user_language": "English"
    }
    
    # 2. 랭그래프 실행
    print("\n[진행중] LangGraph가 에이전트들을 순차적으로 호출하여 결과를 추론하고 있습니다...\n")
    
    for step in graph.stream(initial_state, stream_mode="updates"):
        for node_name, node_state in step.items():
            print(f">>> [완료된 노드: {node_name}]")
            
            if "messages" in node_state:
                latest_message = node_state["messages"][-1]
                
                if node_name == "main_agent" and getattr(latest_message, 'tool_calls', None):
                    print("  💡 메인 에이전트가 툴 호출을 결심했습니다!")
                    print("  (호출 도구명:", latest_message.tool_calls[0]['name'], "/ 전달 인자값:", latest_message.tool_calls[0]['args'], ")\n")
                
                elif node_name == "tools":
                    print(f"  🔍 DB 검색 툴이 반환한 내용: \n  {latest_message.content}\n")
                
                elif node_name == "main_agent":
                    print(f"  🗣️ 최종 응답:\n  {latest_message.content}\n")
            
            elif "enhanced_query" in node_state:
                print(f"  🔑 추출된 키워드: {node_state['enhanced_query']}\n")
    
    print("✅ 테스트가 성공적으로 완료되었습니다!")


if __name__ == "__main__":
    run_test()
