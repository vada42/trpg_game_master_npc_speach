from langchain_community.embeddings import OllamaEmbeddings
from langchain.vectorstores import FAISS

embeddings = OllamaEmbeddings()
def create_end_quest_judgment(detail, mainQuest, subQuest):
    # FAISS 벡터 데이터베이스에 detail 텍스트 저장
    vector_end_detail_db = FAISS.from_texts([detail], embedding=embeddings)
    # mainQuest 및 각 subQuest와 관련된 정보를 검색하여 요약 텍스트 생성
    queries = [mainQuest] + subQuest  # mainQuest와 subQuest 리스트 결합
    relevant_info = []
    for query in queries:
    # query를 사용하여 관련 문장 검색
        docs = vector_end_detail_db.max_marginal_relevance_search(query, k=10, fetch_k=30)  # 필요한 k와 fetch_k 설정
        relevant_info.extend([doc.page_content for doc in docs])
    # 검색된 관련 문장을 하나의 문자열로 결합
    relevant_detail_text = "\n".join(relevant_info)
    return relevant_detail_text