# (c) 2026 oiso.ai
from langchain_core.tools import tool
import os
import json
from sqlalchemy import create_engine, text

_engine = None

def tool_response(
    status: str,
    tag_name: str,
    radius_km: float,
    results: list | None = None,
    message: str = "",
) -> str:
    payload = {
        "status": status,  # "success" | "empty" | "error"
        "tag_name": tag_name,
        "radius_km": radius_km,
        "count": len(results or []),
        "results": results or [],
        "message": message,
    }
    return json.dumps(payload, ensure_ascii=False)

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



@tool
def search_nearby_stores(tag_name: str, lat: float, lng: float, radius_km: float = 1.0) -> str:
    """
    Search nearby traditional-market clusters by a Korean tag.

    Args:
        tag_name: Korean tag to search for, such as "떡볶이", "김밥", "카페".
        lat: User latitude.
        lng: User longitude.
        radius_km: Search radius in kilometers.

    Returns:
        JSON string with status, tag_name, radius_km, count, results, and message.
    """
    engine = get_engine()
    if engine is None:
        return tool_response(
            status="error",
            tag_name=tag_name,
            radius_km=radius_km,
            message="DATABASE_URL environment variable is not set.",
        )

    try:
        with engine.connect() as conn:
            # tag_list로 태그와 연결된 cluster_array 조회
            # tags 테이블의 PK가 tag_string(문자열)이므로 직접 비교
            query = text("""
                WITH matched_clusters AS (
                    SELECT
                        ca.cluster_no,
                        ca.latitude,
                        ca.longitude,
                        ST_Distance(
                            ca.geom::geography,
                            ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography
                        ) / 1000.0 AS distance_km
                    FROM cluster_array ca
                    JOIN tag_list tl ON ca.cluster_no = tl.cluster_no
                    WHERE tl.tag = :tag_name
                    AND ST_DWithin(
                        ca.geom::geography,
                        ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography,
                        :radius_m
                    )
                )
                SELECT
                    mc.cluster_no,
                    mc.latitude,
                    mc.longitude,
                    mc.distance_km,
                    array_agg(tl2.tag ORDER BY tl2.tag) AS all_tags
                FROM matched_clusters mc
                JOIN tag_list tl2 ON mc.cluster_no = tl2.cluster_no
                GROUP BY mc.cluster_no, mc.latitude, mc.longitude, mc.distance_km
                ORDER BY mc.distance_km ASC
                LIMIT 5
            """)
            result = conn.execute(
                query,
                {
                    "tag_name": tag_name,
                    "lat": lat,
                    "lng": lng,
                    "radius_m": radius_km * 1000,
                },
            ).fetchall()

            nearby_clusters = []
            for row in result:
                nearby_clusters.append({
                    "cluster_no": row[0],
                    "tags": row[4],
                    "distance_km": round(float(row[3]), 2),
                })

            # 거리가 가까운 순서대로 정렬 (오름차순)
            nearby_clusters.sort(key=lambda x: x["distance_km"])

            nearby_clusters = nearby_clusters[:5]

            if not nearby_clusters:
                return tool_response(
                    status="empty",
                    tag_name=tag_name,
                    radius_km=radius_km,
                    message=f"No clusters found within {radius_km}km for the tag '{tag_name}'.",
                )

            return tool_response(
                status="success",
                tag_name=tag_name,
                radius_km=radius_km,
                results=nearby_clusters,
                message=f"Found {len(nearby_clusters)} nearby clusters.",
            )

    except Exception as e:
        return tool_response(
            status="error",
            tag_name=tag_name,
            radius_km=radius_km,
            message=f"Error while searching the database: {str(e)}",
        )

