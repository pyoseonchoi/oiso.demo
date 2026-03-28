from fastapi import APIRouter, Depends, Request
from typing import List, Dict

chat_router = APIRouter()


def get_model_response(request: Request):
    return request.app.state.model

# 중요: async 안에서 def 호출하면 자동으로 다른 스레드에서 일 하게 만들어 줌
# 왜 이렇게 해야 하냐: ML 파이프라인은 다 동기식이라 어차피 동기식 호출할거면 라우터를 동기식을 선언하면
# FastAPI가 알아서 해 줌
@chat_router.post("/")
def invoke_chat(conversation: Dict, model = Depends(get_model_response)):
    """data 형식: {"messages": [{role: "", content: ""}, ...]}, 참고: https://docs.langchain.com/oss/javascript/langchain/models#invoke"""

    response = model.invoke(
        conversation
    )
    
    return response