# (c) 2026 oiso.ai
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_mongodb import MongoDBAtlasVectorSearch # 아마존은 인증받는데 시간이 좀 걸려서 기존에 있던 MongoDB Atlas 썼음
from pymongo import MongoClient
import os

def embedder_initialize() -> MongoDBAtlasVectorSearch:
    embedder = HuggingFaceEmbeddings(model_name=os.environ["TEXT_EMBEDDER"])
    client   = MongoClient(os.environ["MONGODB_CONNECTION_URL"])

    collection = client[os.environ["MONGODB_DATABASE_NAME"]][os.environ["MONGODB_COLLECTION_NAME"]]

    # 나중에 뭐 아마존 OpenSearch로 하든지 하자 아니면 그냥 써도 좋고 왜냐면 3인덱스 이상 쓰면 돈 내더라고
    vector_store = MongoDBAtlasVectorSearch(
        embedding=embedder, 
        collection=collection,
        index_name=os.environ["MONGODB_COLLECTION_FOODS_VECTOR_INDEX_NAME"],
        dimensions=1024,
        text_key="content",
        relevance_score_fn="cosine",
    )

    return vector_store