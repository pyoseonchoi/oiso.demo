import uuid
import base64
from pathlib import Path
from uuid import uuid4
import asyncio


from fastapi import UploadFile
from langgraph_sdk import get_client
from exceptions.base import AppException
from exceptions.http import BadRequestException, StorageException
from core.config import settings
from core.storage import get_s3_client, get_bucket_name, generate_image_url

client = get_client(url=settings.LANGGRAPH_SERVER_URL)

DEFAULT_CHAT_ATTACHMENT_URL_EXPIRES_IN = 60 * 10
CHAT_ATTACHMENT_PREFIX = "chat_attachments"

# ── Thread 인메모리 캐시 ────────────────────────────────────
# 이미 확인된 thread_id를 캐시 → 재방문 시 GET/CREATE HTTP 호출 제거
_thread_cache: set[str] = set()
_cache_lock = asyncio.Lock()

async def ensure_thread(lg_thread_id: str):
    """Thread 존재를 캐시하여 불필요한 HTTP 라운드트립을 제거합니다."""
    if lg_thread_id in _thread_cache:
        return
    async with _cache_lock:
        if lg_thread_id in _thread_cache:
            return
        try:
            thread = await client.threads.get(lg_thread_id)
            if thread.get("status") in ("error", "interrupted"):
                await client.threads.delete(lg_thread_id)
                await client.threads.create(thread_id=lg_thread_id)
        except Exception:
            await client.threads.create(thread_id=lg_thread_id)
        _thread_cache.add(lg_thread_id)


def upload_chat_attachment(image: UploadFile, thread_id: str | None = None) -> dict:
    """
    채팅 첨부 이미지를 S3/MinIO에만 저장합니다.

    지도 데이터 구축용 Picture/Metadata/Image 테이블에는 저장하지 않습니다.
    """
    if not image.filename:
        raise BadRequestException(reason="업로드할 파일명이 존재하지 않습니다.")

    if not image.content_type or not image.content_type.startswith("image/"):
        raise BadRequestException(reason="이미지 파일만 업로드할 수 있습니다.")

    ext = Path(image.filename).suffix
    raw_thread_id = (thread_id or "anonymous").strip() or "anonymous"
    safe_thread_id = "".join(
        char if char.isalnum() or char in "-_" else "_"
        for char in raw_thread_id
    )
    s3_key = f"{CHAT_ATTACHMENT_PREFIX}/{safe_thread_id}/{uuid4()}{ext}"

    try:
        
        s3_client = get_s3_client()
        bucket_name = get_bucket_name()

        s3_client.upload_fileobj(
            image.file,
            bucket_name,
            s3_key,
            ExtraArgs={
                "ContentType": image.content_type,
                "CacheControl": "private, max-age=600",
            },
        )

        attachment_url = generate_image_url(
            s3_key=s3_key,
            expires_in=DEFAULT_CHAT_ATTACHMENT_URL_EXPIRES_IN,
        )

        return {
            "type": "image",
            "attachment_id": str(uuid4()),
            "url": attachment_url,
            "s3_bucket": bucket_name,
            "s3_key": s3_key,
            "s3_version": None,
            "mime_type": image.content_type,
        }

    except BadRequestException:
        raise
    except Exception as e:
        raise StorageException(reason=f"채팅 첨부 이미지 업로드에 실패했습니다. ({str(e)})")
    finally:
        pass


def load_chat_attachment_as_base64(s3_key: str) -> str:
    """
    Load a chat attachment object from S3/MinIO and return it as base64 text.
    Only chat_attachments objects are allowed.
    """
    if not s3_key:
        raise BadRequestException(reason="s3_key가 필요합니다.")

    if not s3_key.startswith(f"{CHAT_ATTACHMENT_PREFIX}/"):
        raise BadRequestException(reason="채팅 첨부 이미지 경로만 분석할 수 있습니다.")

    try:
        s3_client = get_s3_client()
        bucket_name = get_bucket_name()
        response = s3_client.get_object(Bucket=bucket_name, Key=s3_key)
        image_bytes = response["Body"].read()
        return base64.b64encode(image_bytes).decode("utf-8")

    except BadRequestException:
        raise
    except Exception as e:
        raise StorageException(reason=f"채팅 첨부 이미지를 읽지 못했습니다. ({str(e)})")


def prepare_attachments_for_langgraph(attachments: list[dict] | None) -> list[dict]:
    """
    Prepare chat attachments before sending them to LangGraph.

    Local MinIO URLs are usually localhost URLs that OpenAI cannot fetch.
    In that case, include a base64 data URL for vision input.
    """
    prepared = []
    for attachment in attachments or []:
        item = dict(attachment)
        if (
            settings.MINIO_ENDPOINT_URL
            and item.get("type") == "image"
            and item.get("s3_key")
            and not item.get("data_url")
        ):
            image_b64 = load_chat_attachment_as_base64(item["s3_key"])
            mime_type = item.get("mime_type") or "image/jpeg"
            item["data_url"] = f"data:{mime_type};base64,{image_b64}"

        prepared.append(item)

    return prepared


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
            "location": {"lat": client_lat, "lng": client_lng},
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


async def stream_chat_agent(
    thread_id: str,
    user_message: str,
    user_language: str,
    client_lat: float,
    client_lng: float,
):
    """
    main_agent의 텍스트 토큰만 골라서 delta(증분) 문자열을 yield하는 제너레이터.
    
    로그 분석 결과:
    - messages/metadata : 어떤 노드에서 온 메시지인지 ID 등록
    - messages/partial  : 누적 content (delta 아님!) → 이전값과 비교해서 새 글자만 추출
    - tool_calls 있는 청크 : content='' → 무시
    """
    _NAMESPACE = uuid.UUID("00000000-0000-0000-0000-000000000001")
    lg_thread_id = str(uuid.uuid5(_NAMESPACE, thread_id))

    try:
        thread = await client.threads.get(lg_thread_id)
        if thread.get("status") in ("error", "interrupted"):
            await client.threads.delete(lg_thread_id)
            await client.threads.create(thread_id=lg_thread_id)
    except Exception:
        await client.threads.create(thread_id=lg_thread_id)

    # ── 핵심 상태 추적 변수 ──────────────────────────────
    # { message_id: "main_agent" } 형태로 main_agent 소속 메시지 ID 등록
    main_agent_msg_ids: set[str] = set()
    # { message_id: 마지막으로_전송한_content } 누적값 → delta 계산용
    last_content: dict[str, str] = {}
    # ────────────────────────────────────────────────────

    async for chunk in client.runs.stream(
        lg_thread_id,
        "chat_agent",
        input={
            "messages": [{"role": "human", "content": user_message}],
            "user_language": user_language,
            "location": {"lat": client_lat, "lng": client_lng},
        },
        stream_mode="messages",
    ):
        event = chunk.event
        data  = chunk.data

        # ── 1. 노드 정보 등록 ─────────────────────────────
        if event == "messages/metadata":
            # 로그 형식: data = { "msg_id": { "metadata": { "langgraph_node": "...", ... } } }
            for msg_id, info in data.items():
                node = info.get("metadata", {}).get("langgraph_node", "")
                if node == "main_agent":
                    main_agent_msg_ids.add(msg_id)

        # ── 2. 토큰 스트리밍 ──────────────────────────────
        elif event == "messages/partial":
            # data = [ { id, content, tool_calls, type, ... } ]
            for msg in data:
                msg_id    = msg.get("id", "")
                content   = msg.get("content", "")
                tool_calls = msg.get("tool_calls", [])

                # main_agent 소속 메시지만 처리
                if msg_id not in main_agent_msg_ids:
                    continue

                # tool_call 진행 중인 청크는 content가 '' → 스킵
                if tool_calls or not content:
                    continue

                # 누적값 → delta 변환
                prev = last_content.get(msg_id, "")
                delta = content[len(prev):]          # 새로 추가된 부분만
                last_content[msg_id] = content       # 현재값 저장

                if delta:
                    yield delta


async def stream_chat_agent_v2(
    thread_id: str,
    user_message: str,
    user_language: str,
    client_lat: float,
    client_lng: float,
    attachments: list[dict] | None = None,
):
    """
    stream_chat_agent와 동일하게 main_agent의 텍스트 토큰을 스트리밍하되,
    LangGraph state에 attachments 메타데이터를 함께 전달합니다.
    messages-tuple 모드로 delta를 직접 수신합니다.
    """
    _NAMESPACE = uuid.UUID("00000000-0000-0000-0000-000000000001")
    lg_thread_id = str(uuid.uuid5(_NAMESPACE, thread_id))

    await ensure_thread(lg_thread_id)

    input_payload = {
        "messages": [{"role": "human", "content": user_message}],
        "user_language": user_language,
        "location": {"lat": client_lat, "lng": client_lng},
        "attachments": prepare_attachments_for_langgraph(attachments),
    }

    TOOL_EVENT_MAP = {
        "analyze_menu_image": "__ocr_result__",
        "search_nearby_stores": "__nearby_stores_result__",
    }
    # ── ToolMessage 누적 버퍼 ─────────────────────────────────
    # msg_id → { "name": tool_name, "chunks": [content조각들] }
    tool_buffers: dict[str, dict] = {}

    async for chunk in client.runs.stream(
        lg_thread_id,
        "chat_agent",
        input=input_payload,
        stream_mode="messages-tuple",
    ):
        event = chunk.event
        if event != "messages":
            continue

        msg, metadata = chunk.data
        node = metadata.get("langgraph_node", "")
        msg_type = msg.get("type", "")
        msg_name = msg.get("name", "")

        # ── ToolMessage → 버퍼에 누적 (파싱하지 않음) ──────────
        if msg_type in ("tool", "ToolMessage", "ToolMessageChunk") and msg_name in TOOL_EVENT_MAP:
            msg_id = msg.get("id", "")
            content = msg.get("content", "")
            if msg_id not in tool_buffers:
                tool_buffers[msg_id] = {"name": msg_name, "chunks": []}
            if content:
                tool_buffers[msg_id]["chunks"].append(content)
            continue

        # ── main_agent 텍스트 토큰만 yield ────────────────────
        if node != "main_agent":
            continue
        if msg.get("tool_calls") or not msg.get("content"):
            continue

        yield msg["content"]

    # ── 스트리밍 종료 후: 누적된 ToolMessage 파싱 & yield ───────
    import json as _json
    found_tools: set[str] = set()
    for msg_id, buf in tool_buffers.items():
        tool_name = buf["name"]
        if tool_name in found_tools:
            continue
        full_content = "".join(buf["chunks"])
        if not full_content:
            continue
        try:
            tool_data = _json.loads(full_content)
            found_tools.add(tool_name)
            yield (TOOL_EVENT_MAP[tool_name], tool_data)
        except Exception:
            pass


