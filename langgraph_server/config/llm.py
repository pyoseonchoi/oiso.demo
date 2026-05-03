# (c) 2026 oiso.ai
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv("../.env")

# 대화용 — 약간의 창의성
chat_model = ChatOpenAI(model="gpt-4.1-mini", temperature=0.7, timeout=30.0)

# 쿼리 추출/분류 — 환각 최소화 / OCR노드도 사용
extraction_model = ChatOpenAI(model="gpt-4.1-mini", temperature=0.0, timeout=30.0)
