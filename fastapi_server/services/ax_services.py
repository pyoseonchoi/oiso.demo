from langgraph_sdk import get_client
from exceptions.base import AppException

client = get_client(url = "http://127.0.0.1:2024")



async def run_ocr_agent(image_b64: str, user_language: str) -> dict:

    #ocr_agent 호출
    run = await client.runs.wait(
        thread_id=None,
        assistant_id="ocr_agent",
        input={
            "image_b64": image_b64,
            "user_language": user_language
        }
    )

    #최종 State에서 검증된 결과를 추출함
    is_valid = run.get("is_valid", True)
    error_message = run.get("error_message", "")

    
    if not is_valid:
        raise AppException(
            status_code=400,
            reason=error_message
        )

    # 정상이면 ocr_result반환

    return run.get("ocr_result", {})