from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):

    DATABASE_URL: str
    OPENAI_API_KEY: str
    
    # IAM Role 기반 환경에서는 사용X
    AWS_ACCESS_KEY_ID: str | None = None
    AWS_SECRET_ACCESS_KEY: str | None = None
    
    # EC2/로컬 공통
    AWS_REGION: str
    
    # 로컬 MinIO 전용
    MINIO_ENDPOINT_URL: str | None = None
    MINIO_BUCKET_NAME: str | None = None

    #EC2 S3 전용
    S3_BUCKET_NAME: str | None = None

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

@lru_cache
def get_settings():
    return Settings()

settings = get_settings()