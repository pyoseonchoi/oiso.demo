import time
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from core.config import settings

logger = logging.getLogger(__name__)

# 전역 변수로 엔진과 세션 메이커 선언 (Lazy Initialization)
_engine = None
_SessionLocal = None

def get_engine():
    """DB 엔진을 지연 생성하고, 연결 풀(Connection Pool) 및 재시도 로직 적용"""
    global _engine, _SessionLocal
    
    if _engine is None:
        # 배포 환경을 위한 연결 풀링 최적화
        _engine = create_engine(
            settings.DATABASE_URL,
            pool_pre_ping=True,  # 커넥션 사용 전 ping을 날려 유효성 검사 (RDS 재부팅 시 방어)
            pool_recycle=3600,   # 1시간마다 커넥션 초기화 (타임아웃 방지)
            pool_size=10,        # 기본 동시 연결 풀 크기
            max_overflow=20      # 최대 초과 허용 연결 수
        )
        
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)
        
        # 실제 연결 테스트 및 재시도 로직
        retries = 5
        while retries > 0:
            try:
                with _engine.connect() as conn:
                    logger.info("Successfully connected to the database.")
                    break
            except Exception as e:
                logger.warning(f"DB connection failed. Retrying in 5 seconds... ({retries} left) Error: {e}")
                retries -= 1
                time.sleep(5)
                
        if retries == 0:
            logger.error("Failed to connect to the database after multiple attempts. Server will continue but DB calls will fail.")

    return _engine

def get_db():
    """실제 API 호출 시 세션을 생성하여 반환"""
    if _SessionLocal is None:
        get_engine()
        
    db = _SessionLocal()
    try:
        yield db
    finally:
        db.close()