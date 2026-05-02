# (c) 2026 oiso.ai
from langchain_core.tools import tool
import math
import os
import json
from sqlalchemy import create_engine, text

_engine = None

def get_engine():
    """DB 엔진을 싱글톤으로 지연 생성하고, 배포용 커넥션 풀 최적화 적용"""
    global _engine
    if _engine is None:
        db_url = os.getenv("DATABASE_URL")
        if db_url:
            _engine = create_engine(
                db_url, 
                connect_args={"connect_timeout": 5},
                pool_pre_ping=True,  # RDS 끊김 방지용 ping
                pool_recycle=3600,   # 1시간마다 커넥션 초기화
                pool_size=5,         # LangGraph 전용 풀 사이즈
                max_overflow=10
            )
    return _engine

def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0 # 지구 반지름 (km)
    dLat = math.radians(lat2 - lat1)
    dLon = math.radians(lon2 - lon1)
    a = math.sin(dLat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dLon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

@tool
def search_nearby_stores(tag_name: str, lat: float, lng: float, radius_km: float = 1.0) -> str:
    """
    Search for nearby photo clusters that are tagged with a specific Korean keyword.

    Args:
        tag_name (str): The Korean tag to search for (e.g., "떡볶이", "김밥").
        lat (float): The latitude of the user's current location.
        lng (float): The longitude of the user's current location.
        radius_km (float): The search radius in kilometers (default is 1.0).

    Returns:
        str: A JSON-formatted string containing a list of nearby clusters (cluster_no, tags, distance),
             or a message indicating that no clusters were found.
    """
    engine = get_engine()
    if engine is None:
        return "Error: DATABASE_URL environment variable is not set."

    try:
        with engine.connect() as conn:
            # cluster_tags로 태그와 연결된 cluster_array 조회
            # tags 테이블의 PK가 tagstring(문자열)이므로 직접 비교
            query = text('''
                SELECT ca.clusterno, ca.latitude, ca.longitude,
                       array_agg(ct2.tag) AS all_tags
                FROM cluster_array ca
                JOIN cluster_tags ct ON ca.clusterno = ct.cluster_no
                JOIN cluster_tags ct2 ON ca.clusterno = ct2.cluster_no
                WHERE ct.tag = :tag_name
                GROUP BY ca.clusterno, ca.latitude, ca.longitude
            ''')
            result = conn.execute(query, {"tag_name": tag_name}).fetchall()

            nearby_clusters = []
            for row in result:
                cluster_no  = row[0]
                cluster_lat = row[1]
                cluster_lng = row[2]
                all_tags    = row[3]  # 해당 클러스터의 모든 태그 목록

                distance = haversine(lat, lng, cluster_lat, cluster_lng)

                if distance <= radius_km:
                    nearby_clusters.append({
                        "cluster_no": cluster_no,
                        "tags": all_tags,        # AI가 어떤 곳인지 설명하는 데 사용
                        "distance_km": round(distance, 2)
                    })

            # 거리가 가까운 순서대로 정렬 (오름차순)
            nearby_clusters.sort(key=lambda x: x["distance_km"])

            if not nearby_clusters:
                return f"No clusters found within {radius_km}km for the tag '{tag_name}'."

            return json.dumps(nearby_clusters, ensure_ascii=False)

    except Exception as e:
        return f"Error while searching the database: {str(e)}"

