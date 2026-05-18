### (c) 2026 oiso.ai

FastAPI + LangGraph 기반 AI 관광 안내 챗봇 백엔드


---

## 구조

```
oiso_back/
├── fastapi_server/    # 클라이언트 요청 관리, 세션/DB 연동, LangGraph 통신 역할
└── langgraph_server/  # LangGraph Agent를 서빙하는 API 서버
```

---