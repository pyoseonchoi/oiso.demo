from pathlib import Path
from uuid import uuid4
from fastapi import UploadFile
from sqlalchemy.orm import Session
from core.storage import get_s3_client, get_bucket_name, generate_image_url

DEFAULT_PRESIGNED_URL_EXPIRES_IN = 60 * 10

#커스텀 예외
from exceptions.http import BadRequestException, StorageException

from datetime import datetime
from PIL import Image as PILImage, ExifTags
from PIL.ExifTags import IFD

from models.mx_model import Image, Metadata, Picture

def _dms_to_decimal(dms: tuple, ref: str) -> float:
    """
    도/분/초(DMS) → 십진수(Decimal Degrees) 변환
    dms: (도, 분, 초) 형태의 튜플
    ref: 'N', 'S', 'E', 'W' 방향값
    """
    degrees, minutes, seconds = dms
    decimal = float(degrees) + float(minutes) / 60 + float(seconds) / 3600

    # 남위(S), 서경(W)는 음수 처리
    if ref in ("S", "W"):
        decimal = -decimal

    return decimal


def extract_image_metadata(file_obj) -> dict:
    """
    이미지의 메타데이터 추출
    time_stamp, 위도, 경도
    """

    metadata = {
        "longitude" : None,
        "latitude" : None,
        "time_stamp" : None,
    }

    try:
        file_obj.seek(0)
        image = PILImage.open(file_obj)
        exif = image.getexif()

        if not exif:
            return metadata

        
        # 촬영 시각
        exif_info = exif.get_ifd(IFD.Exif)
        if exif_info and 36867 in exif_info:
            datetime_original = exif_info.get(36867)
            metadata["time_stamp"] = datetime.strptime(
                datetime_original,
                "%Y:%m:%d %H:%M:%S",
            )

        # GPS 정보 -> tag 34853
        if 34853 not in exif:
            return metadata

        gps_info = exif.get_ifd(IFD.GPSInfo)
        if not gps_info:
            return metadata

        # GPS 태그 상수
        # 1=GPSLatitudeRef, 2=GPSLatitude, 3=GPSLongitudeRef, 4=GPSLongitude
        lat_ref = gps_info.get(1)   # 'N' or 'S'
        lat_dms = gps_info.get(2)   # ((도, 1), (분, 1), (초, 100)) 형태
        lon_ref = gps_info.get(3)   # 'E' or 'W'
        lon_dms = gps_info.get(4)

        if lat_ref and lat_dms and lon_ref and lon_dms:
            metadata["latitude"] = _dms_to_decimal(lat_dms, lat_ref)
            metadata["longitude"] = _dms_to_decimal(lon_dms, lon_ref)

        return metadata
        
    except Exception:
        return metadata

    finally:
        file_obj.seek(0)




def upload_picture(image: UploadFile, db: Session) -> dict:
    """
    이미지를 S3(MinIO)에 업로드하고, DB에 Image/Metadata/Picture 레코드 생성 후 URL 반환
    """

    if not image.filename:
        raise BadRequestException(reason="업로드할 파일명이 존재하지 않습니다.")

    if not image.content_type or not image.content_type.startswith("image/"):
        raise BadRequestException(reason="이미지 파일만 업로드할 수 있습니다.")
        
    # 고유 파일명 생성
    ext = Path(image.filename).suffix
    s3_key = f"pictures/{uuid4()}{ext}"

    try:
        s3_client = get_s3_client()
        bucket_name = get_bucket_name()

        # 이미지 메타데이터 추출
        meta_dict = extract_image_metadata(image.file)

        # S3 업로드
        s3_client.upload_fileobj(
            image.file,
            bucket_name,
            s3_key,
            ExtraArgs={
                "ContentType": image.content_type or "application/octet-stream",
                "CacheControl": "public, max-age=31536000, immutable",
            },
        )

        s3_version = None

        # 프론트 미리보기용 URL
        picture_url = generate_image_url(
            s3_key=s3_key,
            expires_in=DEFAULT_PRESIGNED_URL_EXPIRES_IN,
        )


        # ─── DB 저장: Image → Metadata → Picture ───────────────
        image_id = str(uuid4())
        metadata_id = str(uuid4())
        picture_id = str(uuid4())

        # 1) Image 레코드
        db_image = Image(
            unique_id=image_id,
            s3_bucket=bucket_name,
            s3_key=s3_key,
            s3_version=s3_version,
        )
        db.add(db_image)

        # 2) Metadata 레코드
        db_metadata = Metadata(
            unique_id=metadata_id,
            longitude=meta_dict.get("longitude"),
            latitude=meta_dict.get("latitude"),
            time_stamp=meta_dict.get("time_stamp"),
        )
        db.add(db_metadata)

        # 3) Picture 레코드 (Image + Metadata 연결)
        db_picture = Picture(
            unique_id=picture_id,
            created_date=datetime.utcnow(),
            image_id=image_id,
            metadata_id=metadata_id,
        )
        db.add(db_picture)

        db.commit()

        return {
            "picture_url": picture_url,
            "picture_id": picture_id,
            "s3_bucket": bucket_name,
            "s3_key": s3_key,
            "s3_version": s3_version,
            "metadata": meta_dict,
        }

    except BadRequestException:
        raise
    except Exception as e:
        db.rollback()
        raise StorageException(reason=f"파일 업로드에 실패했습니다. ({str(e)})")
