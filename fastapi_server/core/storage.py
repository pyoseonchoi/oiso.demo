import boto3
from botocore.exceptions import ClientError
from core.config import settings
import json
from urllib.parse import quote 
#S3 클라이언트 생성

def get_s3_client():
    
    if settings.MINIO_ENDPOINT_URL:
        # 로컬 환경 — MinIO (Access Key 명시)
        client = boto3.client(
            's3',
            endpoint_url=settings.MINIO_ENDPOINT_URL,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION,
        )
    else:
        # EC2 환경 — IAM Role 자동 인증 (Access Key 전달 안 함)
        client = boto3.client('s3', region_name=settings.AWS_REGION)
    return client

def get_bucket_name() -> str:
    """현재 환경에 맞는 버킷명 반환"""
    if settings.MINIO_ENDPOINT_URL:
        return settings.MINIO_BUCKET_NAME or "images"
    return settings.S3_BUCKET_NAME or ""


def init_storage():
    
    s3_client = get_s3_client()
    bucket_name = get_bucket_name()
    
    try:
        s3_client.head_bucket(Bucket=bucket_name)
        print(f"✅ Storage bucket '{bucket_name}' ready.")
    
    except ClientError:

        print(f"⚠️ Storage bucket '{bucket_name}' not found. Creating a new one...")
        s3_client.create_bucket(Bucket=bucket_name)
        print(f"✅ Storage bucket '{bucket_name}' created successfully.")

    # 로컬 MinIO 전용: 퍼블릭 정책 설정
    # EC2 S3에서는 버킷 정책을 콘솔/IAM에서 관리하는 것을 권장
    if settings.MINIO_ENDPOINT_URL:
        policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "PublicReadGetObject",
                    "Effect": "Allow",
                    "Principal": "*",
                    "Action": ["s3:GetObject"],
                    "Resource": [f"arn:aws:s3:::{bucket_name}/*"]
                }
            ]
        }
        s3_client.put_bucket_policy(Bucket=bucket_name, Policy=json.dumps(policy))

def _join_url(base_url: str, s3_key: str) -> str:
    safe_key = quote(s3_key.lstrip("/"), safe="/")
    return f"{base_url.rstrip('/')}/{safe_key}"


def generate_image_url(s3_key: str, expires_in: int | None = None) -> str:
    """환경에 따라 이미지 접근 URL 생성.

    - Local MinIO: 기존 MinIO direct URL
    - AWS + CloudFront: CDN URL
    - AWS fallback: S3 presigned URL
    """
    if not s3_key:
        return ""

    bucket = get_bucket_name()

    if settings.MINIO_ENDPOINT_URL:
        return _join_url(f"{settings.MINIO_ENDPOINT_URL}/{bucket}", s3_key)

    if settings.CDN_BASE_URL:
        return _join_url(settings.CDN_BASE_URL, s3_key)

    s3_client = get_s3_client()
    return s3_client.generate_presigned_url(
        "get_object",
        Params={"Bucket": bucket, "Key": s3_key},
        ExpiresIn=expires_in or settings.IMAGE_URL_EXPIRES_IN,
    )
