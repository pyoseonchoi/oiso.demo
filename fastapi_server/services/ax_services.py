import uuid
from langgraph_sdk import get_client
from exceptions.base import AppException

client = get_client(url="http://127.0.0.1:2024")


async def run_ocr_agent(image_b64: str, user_language: str) -> dict:
    """
    LangGraph ocr_agent를 호출하여 이미지에서 메뉴 정보를 추출·번역합니다.
    - thread_id=None: OCR은 대화 연속성이 필요 없으므로 매번 새 스레드 사용
    """
    run = await client.runs.wait(
        thread_id=None,
        assistant_id="ocr_agent",
        input={
            "image_b64": image_b64,
            "user_language": user_language,
        },
    )

    # 최종 State에서 검증된 결과를 추출함
    is_valid = run.get("is_valid", True)
    error_message = run.get("error_message", "")

    if not is_valid:
        raise AppException(
            status_code=400,
            reason=error_message
        )

    # 정상이면 ocr_result 반환
    return run.get("ocr_result", {})


async def run_chat_agent(
    thread_id: str,
    user_message: str,
    user_language: str,
    client_lat: float,
    client_lng: float,
) -> str:
    """
    LangGraph chat_agent를 호출하여 AI 응답 텍스트를 반환합니다.

    - uuid를 LangGraph thread_id로 직접 사용 → 같은 uuid면 대화가 이어짐 (멀티턴)
    - thread가 없으면(404) 새로 생성, 있으면 이어서 사용
    """
    # LangGraph는 thread_id로 UUID 형식만 허용함.
    # uuid5()로 어떤 문자열이든 항상 동일한 UUID로 결정론적 변환.
    # 같은 uuid_str → 같은 UUID → 같은 LangGraph thread → 멀티턴 유지
    _NAMESPACE = uuid.UUID("00000000-0000-0000-0000-000000000001")
    lg_thread_id = str(uuid.uuid5(_NAMESPACE, thread_id))

    try:
        thread = await client.threads.get(lg_thread_id)
        # error/interrupted 상태면 삭제 후 재생성 (이전 실패 run이 thread를 오염시킨 경우)
        if thread.get("status") in ("error", "interrupted"):
            await client.threads.delete(lg_thread_id)
            await client.threads.create(thread_id=lg_thread_id)
    except Exception:
        # 없으면 새로 생성
        await client.threads.create(thread_id=lg_thread_id)

    run = await client.runs.wait(
        thread_id=lg_thread_id,
        assistant_id="chat_agent",
        input={
            "messages": [{"role": "human", "content": user_message}],
            "user_language": user_language,
            "client_lat": client_lat,
            "client_lng": client_lng,
        },
    )

    # 최종 state에서 messages 리스트의 마지막 AI 메시지 내용 추출
    messages = run.get("messages", [])
    if not messages:
        return "응답을 생성하지 못했습니다."

    last_message = messages[-1]

    # dict 형태일 수도, BaseMessage 객체일 수도 있으므로 양쪽 처리
    if isinstance(last_message, dict):
        return last_message.get("content", "")
    return getattr(last_message, "content", "")
