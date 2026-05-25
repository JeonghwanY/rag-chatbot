"""벡터 유사도 기반 검색."""
from langchain_chroma import Chroma
from langchain_core.documents import Document

from app.config import settings
from app.ingestion import load_vectorstore


class Retriever:
    """벡터스토어에서 질문과 유사한 문서 청크를 검색."""

    def __init__(self, vectorstore: Chroma | None = None):
        self._vs = vectorstore or load_vectorstore()

    def search(self, query: str, k: int | None = None) -> list[tuple[Document, float]]:
        """유사도 점수와 함께 상위 k개 청크 반환.

        ChromaDB의 similarity_search_with_score는 거리(distance)를 반환.
        값이 작을수록 유사함. 응답 직관성을 위해 1 - distance로 점수화.
        """
        k = k or settings.top_k
        results = self._vs.similarity_search_with_score(query, k=k)
        return [(doc, 1.0 - score) for doc, score in results]


# 싱글톤 인스턴스 (앱 시작 시 한 번만 로드)
_retriever: Retriever | None = None


def get_retriever() -> Retriever:
    global _retriever
    if _retriever is None:
        _retriever = Retriever()
    return _retriever
