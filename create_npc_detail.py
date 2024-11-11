from langchain_community.embeddings import OllamaEmbeddings
from langchain.vectorstores import FAISS

# OllamaEmbeddings 인스턴스 생성
embeddings = OllamaEmbeddings()

def create_npc_detail(detail, charParts):
    # detail이 단일 문자열일 경우, 리스트로 변환
    if isinstance(detail, str):
        detail = [detail]

    # FAISS 벡터 데이터베이스 생성
    vector_db = FAISS.from_texts(detail, embedding=embeddings)
    charParts_dic = {}

    # 각 캐릭터에 대해 MMR 검색으로 다양한 상위 3개의 결과를 가져옴
    for character_name in charParts:
        docs = vector_db.max_marginal_relevance_search(character_name, k=10, fetch_k=30)
        charParts_dic[character_name] = [doc.page_content for doc in docs]

    return charParts_dic
