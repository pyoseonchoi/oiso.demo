# app/services/ai_service.py
import asyncio
import logging

logger = logging.getLogger(__name__)

async def process_image_for_marker(marker_id: int, s3_url: str):
    """
    [AI 프로세싱 워커]
    백그라운드에서 AI 사진 분석 실행 (추후 파이썬 모델 연동 필요)
    """
    logger.info(f"👉 [AI 분석 시작] 마커 ID: {marker_id}, 이미지 URL 분석을 시작합니다.")
    
    # 더미 AI 연산 지연
    await asyncio.sleep(5)
    
    logger.info(f"✅ [AI 분석 완료] 마커 ID: {marker_id} AI 작업 완료! (분류/임베딩 결과 등)")
    
    # TODO: 분석 종료 후 DB(Marker/Photo) 저장 로직 추가 필요
