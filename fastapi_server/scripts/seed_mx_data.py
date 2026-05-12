import csv
import sys
from pathlib import Path
from datetime import datetime
import uuid

# 프로젝트 최상단 디렉토리를 sys.path에 추가하여 db, models 모듈을 임포트할 수 있게 함
current_dir = Path(__file__).resolve().parent
fastapi_dir = current_dir.parent
sys.path.append(str(fastapi_dir))

from db.session import get_db
from models import mx_model

# CSV 파일 경로
DATA_DIR = fastapi_dir / "data"
TAGS_CSV = DATA_DIR / "tags.csv"
CLUSTER_CSV = DATA_DIR / "cluster_info.csv"
PICS_CSV = DATA_DIR / "per_pics_information.csv"

def parse_csv_and_seed():
    missing_files = [f for f in [TAGS_CSV, CLUSTER_CSV, PICS_CSV] if not f.exists()]
    if missing_files:
        print("[오류] 다음 데이터 파일을 찾을 수 없습니다:")
        for f in missing_files:
            print(f"  - {f}")
        return

    # 세션 획득
    db_gen = get_db()
    db = next(db_gen)

    try:
        # 1. 태그(Tags) 데이터 시딩
        print("1. 태그 데이터 시딩 중...")
        with open(TAGS_CSV, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                tag_str = row.get('tag', '').strip()
                if tag_str:
                    # 중복 확인 (upsert 방식이 좋으나 간단히 조회 후 삽입)
                    existing_tag = db.query(mx_model.Tag).filter_by(tag_string=tag_str).first()
                    if not existing_tag:
                        new_tag = mx_model.Tag(tag_string=tag_str)
                        db.add(new_tag)
        db.commit()

        # 2. 클러스터(ClusterArray) 데이터 시딩
        print("2. 클러스터 데이터 시딩 중...")
        with open(CLUSTER_CSV, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row_num, row in enumerate(reader, start=1):
                try:
                    cluster_no = int(row['group_no'])
                    longitude = float(row['centric_point_long'])
                    latitude = float(row['centric_point_lat'])

                    existing_cluster = db.query(mx_model.ClusterArray).filter_by(cluster_no=cluster_no).first()
                    if not existing_cluster:
                        new_cluster = mx_model.ClusterArray(
                            cluster_no=cluster_no,
                            longitude=longitude,
                            latitude=latitude
                        )
                        db.add(new_cluster)
                except Exception as e:
                    print(f"[Cluster CSV {row_num}번째 줄] 파싱 오류: {e}")
        db.commit()

        # 3. 사진(Picture), 메타데이터(Metadata), 매핑(PictureList) 시딩
        print("3. 사진 및 메타데이터 데이터 시딩 중...")
        with open(PICS_CSV, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row_num, row in enumerate(reader, start=1):
                try:
                    # CSV 값 추출
                    pic_no_str = str(row['pic_no']).strip() # unique_id로 사용
                    group_no = int(row['group_no'])
                    pic_long = float(row['pic_long'])
                    pic_lat = float(row['pic_lat'])
                    pic_time_unix = int(row['pic_time'])
                    
                    # UNIX Time -> Datetime 변환
                    pic_timestamp = datetime.fromtimestamp(pic_time_unix)

                    # 이미 존재하는 사진인지 확인
                    existing_pic = db.query(mx_model.Picture).filter_by(unique_id=pic_no_str).first()
                    if existing_pic:
                        continue

                    # 메타데이터 생성 (S3 이미지는 제외하기로 하였으므로 metadata만 처리)
                    new_metadata = mx_model.Metadata(
                        unique_id=pic_no_str,
                        longitude=pic_long,
                        latitude=pic_lat,
                        time_stamp=pic_timestamp
                    )
                    db.add(new_metadata)

                    # Picture 생성
                    new_picture = mx_model.Picture(
                        unique_id=pic_no_str,
                        created_date=pic_timestamp,  # 촬영 시간을 생성 시간으로 임시 매핑
                        image_id=None,               # 룰: S3 업로드 시 생성되므로 None으로 비워둠
                        metadata_id=pic_no_str
                    )
                    db.add(new_picture)
                    
                    # db.flush()를 통해 DB에 반영하여 관계 매핑에 사용할 수 있게 함
                    db.flush()

                    # ClusterArray <-> Picture 다대다 연결 (PictureList)
                    # ClusterArray가 먼저 존재해야 함
                    cluster = db.query(mx_model.ClusterArray).filter_by(cluster_no=group_no).first()
                    if cluster:
                        new_pic_list = mx_model.PictureList(
                            cluster_no=group_no,
                            pic_no=pic_no_str
                        )
                        db.add(new_pic_list)
                    else:
                        print(f"[경고] group_no={group_no} 인 클러스터가 없어 매핑을 생략합니다. (pic_no={pic_no_str})")

                except Exception as e:
                    print(f"[Pics CSV {row_num}번째 줄] 파싱 오류: {e}")
        
        # 전체 커밋
        db.commit()
        print("데이터 시딩이 성공적으로 완료되었습니다!")

    except Exception as e:
        db.rollback()
        print(f"전체 작업 중 오류 발생 (롤백 진행됨): {e}")
    finally:
        # 세션 종료
        try:
            next(db_gen)
        except StopIteration:
            pass

if __name__ == "__main__":
    print("CSV 데이터 시딩 스크립트를 시작합니다...")
    parse_csv_and_seed()
