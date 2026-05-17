# (c) 2026 oiso.ai
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv("../.env")

# 쿼리 분류 전용 — 빠른 TTFT가 중요
classification_model = ChatOpenAI(model="gpt-4.1-nano", temperature=0.0, timeout=15.0)

# 대화용 — 약간의 창의성
chat_model = ChatOpenAI(model="gpt-4.1-mini", temperature=0.7, timeout=30.0, max_tokens=1024,)

# 쿼리 추출/분류 — 환각 최소화 / OCR노드도 사용
extraction_model = ChatOpenAI(model="gpt-4.1-mini", temperature=0.0, timeout=30.0)
