# 프로젝트 개발 가이드 및 안내

환영합니다! 대학교 캡스톤 프로젝트의 핵심인 백엔드를 맡게 되신 것을 축하합니다.
멘토로서, 초보자도 쉽게 디렉토리를 이해하고 개발을 시작할 수 있도록 `app/` 폴더 내에 실무 수준의 뼈대를 꼼꼼히 세워 두었습니다. 모든 주요 파일에는 제가 "왜 이렇게 코드를 짰는지" 주석을 달아두었으니, 천천히 살펴보시면 큰 도움이 될 것입니다.

## 1. 실무형 FastAPI 디렉토리 구조 뜯어보기

보통 실무에서는 하나의 파일(main.py)에 코드를 다 몰아넣지 않고, 역할을 분리합니다. 이를 "관심사 분리"라고 부르며, 프로젝트가 커져도 유지보수가 쉽게 만들어줍니다.

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

## 2. 멘토의 팁 (앞으로 어떻게 개발해야 할까요?)

1. **DB 환경 설정**: 코드를 돌려보기 전에 본인 컴퓨터 또는 서버에 PostgreSQL과 **PostGIS 확장 모듈**이 설치되어 있어야 합니다.
2. **코드 읽는 순서**: `main.py` -> `api/endpoints/markers.py` -> `services/marker_service.py` -> `models/marker.py` 순으로 따라가며 주석을 읽어보시면 흐름이 완벽히 이해될 겁니다.
3. **AI 통합**: `services/ai_service.py` 파일을 보면 `process_image_for_marker` 라는 더미 함수가 있습니다. AI 팀원이 모델을 짜오면, 바로 저기 안에 파이썬 코드를 쑤욱 끼워 넣기만 하면 됩니다! 백엔드 로직 하나도 건드릴 필요 없이요.
4. **에러 핸들링**: `markers.py` 내부를 보시면 `try-except`와 `HTTPException`을 통해 프론트엔드에게 왜 예외가 발생했는지(좌표 잘못됨, DB 뻗음 등) 알려주도록 작성했습니다. 

궁금한 점이 있으면 언제든 멘토를 다시 불러서 질문해 주세요. 파이팅!
