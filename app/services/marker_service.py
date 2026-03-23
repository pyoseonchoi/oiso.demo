# app/services/marker_service.py
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.marker import Marker
from app.models.photo import Photo

def create_marker_and_photo(
    db: Session, 
    latitude: float, 
    longitude: float, 
    category: str, 
    fake_s3_url: str
) -> Marker:
    """
    1) 새 마커(위치/카테고리)를 생성해서 DB에 넣고
    2) 거기에 묶이는 사진 객체도 생성하는 "핵심 비즈니스 로직(서비스)" 입니다.
    """
    # [초보자 필독] PostGIS 는 POINT(경도 위도) 순으로 씁니다! (위도 경도 아님 주의)
    point_wkt = f"POINT({longitude} {latitude})"
    
    # 일단 빈 메모리에 마커 덩어리를 빚어봅니다.
    new_marker = Marker(
        category=category,
        location=point_wkt
    )
    # 진짜 DB에 던져넣기!
    db.add(new_marker)
    db.commit()            # 도장 쾅! 이제 이 시점에 DB 테이블에 1번, 2번 식의 실제 ID(PK)가 생깁니다.
    db.refresh(new_marker) # 방금 만든 번호(ID)를 내 파이썬 지역변수로 다시 당겨옵니다.
    
    # 그 방금 만든 마커ID(부모 번호)를 가지고 자식인 '사진 레코드'를 생성.
    new_photo = Photo(
        marker_id=new_marker.id,
        s3_url=fake_s3_url
    )
    db.add(new_photo)
    db.commit()
    db.refresh(new_photo)
    
    # 라우터 쪽으로 방금 만든 마커 정보를 최종적으로 돌려줍니다.
    return new_marker


def get_markers_within_radius(db: Session, latitude: float, longitude: float, radius_meters: int = 1000):
    """
    현재 사용자가 켠 지도(중심점)을 기준으로 
    반경(radius_meters) 이내에 있는 마커 정보들을 DB에서 확 긁어오는 곳입니다.
    """
    center_point = f"POINT({longitude} {latitude})"
    
    # 멘토의 팁: 
    # Marker 객체 통째로 다 들고 오지 않고(성능 낭비),
    # 앱에서 딱 필요한 정보(id, 카테고리, 위도, 경도)만 예쁘게 분리해서 쏙 뽑아옵니다.
    # 함수 설명:
    # - ST_Y 와 ST_X 는 WKB(알 수 없는 바이너리 글자들)로 저장된 위치에서 위도, 경도를 숫자로 뽑아주는 마법 함수.
    # - ST_DistanceSphere 는 두 점 간의 진짜 구체(지구) 상 거리를 "미터(m)" 단위로 재줍니다.
        
    query = db.query(
        Marker.id.label("id"),
        Marker.category.label("category"),
        func.ST_Y(func.ST_AsText(Marker.location)).label("latitude"),
        func.ST_X(func.ST_AsText(Marker.location)).label("longitude")
    ).filter(
        # 필터링: 마커 위치랑 센터 위치의 거리가 반지름(예:1000m) 보다 같거나 작아야 해!
        func.ST_DistanceSphere(Marker.location, func.ST_GeomFromText(center_point, 4326)) <= radius_meters 
    )
    
    # .all() 은 쿼리 조건을 만족하는 모조리 리스트 형태로 꺼내옵니다.
    return query.all()
