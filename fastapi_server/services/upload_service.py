from uuid import uuid4
from fastapi import UploadFile
from pathlib import Path
from schemas.upload_schema import FileUploadResponse, ImageMetaData

from core.config import settings
from core.storage import get_s3_client

from PIL import Image
from PIL.ExifTags import IFD



def save_file(file: UploadFile) -> FileUploadResponse:
    ext = Path(file.filename).suffix if file.filename else ""
    saved_name = f"{uuid4()}{ext}"

    extract_meta = extract_metadata(file)

    # S3 클라이언트를 가져옴
    s3_client = get_s3_client()
    bucket_name = settings.MINIO_BUCKET_NAME

    # MinIO로 파일 데이터를 업로드함 참고: https://docs.aws.amazon.com/boto3/latest/guide/s3-uploading-files.html
    s3_client.upload_fileobj(
        file.file,
        bucket_name,
        saved_name,

        ExtraArgs={
            "ContentType": file.content_type,
        },
    )

    # 사진 볼수있는 URL주소 생성
    # 기본 URL 구조: 통신주소/버킷이름/파일이름
    file_url = f"{settings.MINIO_ENDPOINT_URL}/{bucket_name}/{saved_name}"

    return FileUploadResponse(
        original_filename = file.filename,
        saved_filename=saved_name,
        content_type=file.content_type,
        file_url=file_url,
        metadata=extract_meta
        
    )


#GPS 좌표 변환 헬퍼함수
def convert_to_degrees(value):
    """(도, 분, 초) 포맷을 십진수 float로 변환"""
    d = float(value[0])
    m = float(value[1])
    s = float(value[2])
    return d + (m / 60.0) + (s / 3600.0)


def extract_metadata(file: UploadFile) -> ImageMetaData | None:
    try:

        img = Image.open(file.file)
        exif = img.getexif()


        if not exif:
            file.file.seek(0)
            return None

        latitude = None
        longitude = None
        captured_at = None

        gps_info = exif.get_ifd(IFD.GPSInfo)

        # GPS 정보가 잘 들어있는지 확인 
        if gps_info and (2 in gps_info) and (4 in gps_info):
            latitude = convert_to_degrees(gps_info[2])
            longitude = convert_to_degrees(gps_info[4])

        # 촬영 시각
        exif_info = exif.get_ifd(IFD.Exif)
        if exif_info and 36867 in exif_info:
            captured_at = exif_info.get(36867)
        

        # 커서 초기화 필수
        file.file.seek(0)

        if latitude is not None or longitude is not None or captured_at is not None:

            return ImageMetaData(
                latitude=latitude,
                longitude=longitude,
                captured_at=captured_at

            )
        else:
            return None

    except Exception as e:

        file.file.seek(0)
        return None