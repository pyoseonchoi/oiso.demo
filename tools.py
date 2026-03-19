# (c) 2026 oiso.ai
from langchain.tools import tool

# 중요 정보
"""
우리가 함수를 작성 할 때 
@tool                                    < tool 데코레이터 달아야 langchain이 툴인지 알고
def girlfriend(query: str) -> str:       < 일반 파이썬 하듯이 타입 명시 안하면 안됨 입력 출력값 타입 명시
    Making a girlfriend for you.         <    
    hehehe.                              < 지금은 삼중 따옴표를 못 달아서 안 썼는데 이렇게 독스트링을 달아야
                                         < 모델이 이걸 언제 써야 하는지 인식함
    Args:                                < 영어 쓰는게 좋을듯
        query: 너의 이상형                  < 
    return None

암튼 저렇게 적으면, 이게 모델에 들어갈 때
아래 양식처럼 들어가서 상황에 맞는 도구 사용을 유발함

근데 함수 이름도 직관적으로 지어야 함!

{
  "name": "multiply",
  "description": "Multiply `a` and `b`. Args: a: First int b: Second int",  // docstring에서 추출
  "parameters": {
    "type": "object",
    "properties": {
      "a": {"type": "integer", "description": "First int"},
      "b": {"type": "integer", "description": "Second int"}
    }
  }
}

그런데 영어 딸리니까(듣고 말할줄 아는거랑 작문은 다른 영역)
아래 프롬프트 넣은 채팅 세션으로 의도를 번역하셈:
[당신은 지금부터 저의 말을 매우 매끄러운 영어 파이썬 독스트링으로 번역해야 합니다.]
"""

@tool
def rag_object_searching_pipelining_entry(user_query: str) -> str:
    """
    Maps a tourist's desired experience to a specific food, place, concept or entity.

    This function takes a natural language description of what a user wants to 
    drink, eat, see, or do during their trip. It identifies the exact underlying 
    concept in English and translates the result back into the language of 
    the user's original query.

    Args:
        user_query (str): A description of the experience the user wants 
            to have (e.g., desired food, attractions, or activities).

    Returns:
        str: The identified concept in English, translated into the 
            user's original query language.
    """
    # 일단은 더미 기능으로 유니코드 범위를 활용해서 언어 감지하는 값을 반환함
    return "잘 되누."

@tool
def rag_user_location_weather(address: str) -> str:
    """
    Retrieves the weather data for a specific location and returns it as a JSON string.

    This function accepts a single-sentence address representing the current region, 
    precise to the city, county, or district level (시/군/구), and fetches the 
    weather conditions for that area.

    Args:
        address (str): A single-sentence address representing the location, 
            with city, county, or district level precision.

    Returns:
        str: A JSON-formatted string containing the weather information 
            for the specified region.
    """
    return "맑누."

@tool
def rag_route_public_transport(departure: str, destination: str):
    """
    Calculates the optimal public transit route between two locations.

    This function takes the origin and destination addresses as input and 
    determines the best route using public transportation. The resulting 
    route information is returned as a JSON-formatted string.

    Args:
        departure (str): The starting address of the journey.
        destination (str): The destination address of the journey.

    Returns:
        str: A JSON-formatted string containing the optimal public transit route.
    """
    return "937 걍 없어졌으면."