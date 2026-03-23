# 프로젝트 개발 가이드 및 안내


## 1. FastAPI 디렉토리 구조 


```
종프_back/
├── app/
│   ├── main.py                👉 앱의 심장 (엔진). FastAPI 애플리케이션을 실행하고 라우터를 연결합니다.
│   ├── core/
│   │   └── database.py        👉 DB와 통신을 뚫어주는 파이프라인(Session/Engine)을 관리합니다.
│   ├── models/
│   │   ├── marker.py          👉 SQLAlchemy: 실제 PostgreSQL에 들어갈 "마커 테이블" 모양.
│   │   └── photo.py           👉 SQLAlchemy: 실제 PostgreSQL에 들어갈 "사진 테이블" 모양.
│   ├── schemas/
│   │   └── upload.py          👉 Pydantic: 프론트엔드에서 넘어온 데이터(GPS, 카테고리 등)가 "옳은 형식인지 검사"하는 보안 요원.
│   ├── services/
│   │   ├── marker_service.py  👉 비즈니스 로직. "DB에 데이터를 어떻게 넣고 어떻게 뺄 것인가?"(핵심 로직).
│   │   └── ai_service.py      👉 AI 로직 분리. AI 팀원이 나중에 자기 코드를 이 파일에만 넣으면 되도록 깔끔하게 분리.
│   └── api/
│       └── endpoints/
│           └── markers.py     👉 프론트엔드와 직접 대화하는 창구(Controller/Router). HTTP 요청(GET/POST)을 받아서 Service로 넘깁니다.
└── requirements.txt           👉 pip install -r requirements.txt 명령어로 필요한 라이브러리를 한 번에 설치하세요!
```

##2. TODO

1. DB 환경 설정: 코드를 돌려보기 전에 본인 컴퓨터 또는 서버에 PostgreSQL과 PostGIS 확장 모듈이 설치되어 있어야 합니다.
2. 플로우: `main.py` -> `api/endpoints/markers.py` -> `services/marker_service.py` -> `models/marker.py` 순
3. AI 통합: `services/ai_service.py` 파일을 보면 `process_image_for_marker` 라는 더미 함수가 활용.
4. 에러 핸들링: `markers.py` 내부를 보시면 `try-except`와 `HTTPException`을 통해 프론트엔드에게 왜 예외가 발생했는지(좌표 잘못됨, DB 뻗음 등) 알려주도록 작성

