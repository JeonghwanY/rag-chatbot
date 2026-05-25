"""RAG 체인: 검색된 컨텍스트를 바탕으로 LLM이 답변 생성."""
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

from app.config import settings
from app.retriever import get_retriever
from app.schemas import QueryResponse, SourceChunk


# 프롬프트 설계 포인트:
# 1. 컨텍스트 외 추론 금지 (할루시네이션 방지)
# 2. 모르면 모른다고 답하기
# 3. 한국어 응답 명시
# 4. 출처 활용 유도
RAG_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "당신은 YouSync 기술 문서에 기반하여 사용자 질문에 답변하는 어시스턴트입니다.\n"
     "아래 [컨텍스트]만을 근거로 답변하세요.\n"
     "- 컨텍스트에 없는 내용은 추측하지 마세요.\n"
     "- 답을 찾을 수 없으면 '제공된 문서에서 관련 내용을 찾을 수 없습니다.'라고 답하세요.\n"
     "- 답변은 한국어로, 간결하고 명확하게 작성하세요.\n"
     "- 가능하면 답변 끝에 참고한 문서명을 언급하세요."),
    ("human",
     "[컨텍스트]\n{context}\n\n[질문]\n{question}"),
])


def format_context(docs: list[Document]) -> str:
    """검색된 청크들을 LLM 입력용 컨텍스트 문자열로 변환."""
    parts = []
    for i, doc in enumerate(docs, 1):
        source = doc.metadata.get("source", "unknown")
        parts.append(f"[문서 {i} | 출처: {source}]\n{doc.page_content}")
    return "\n\n---\n\n".join(parts)


def get_llm() -> ChatGoogleGenerativeAI:
    """Gemini LLM 인스턴스."""
    return ChatGoogleGenerativeAI(
        model=settings.gemini_model,
        google_api_key=settings.google_api_key,
        temperature=0.2,  # 사실 기반 응답이므로 낮게
    )


def answer_question(question: str, top_k: int | None = None) -> QueryResponse:
    """RAG 파이프라인 실행: 검색 → 컨텍스트 구성 → LLM 답변."""
    retriever = get_retriever()
    scored_docs = retriever.search(question, k=top_k)
    docs = [doc for doc, _ in scored_docs]

    if not docs:
        return QueryResponse(
            answer="인덱싱된 문서가 없습니다. 먼저 문서를 업로드하고 인덱싱하세요.",
            sources=[],
            question=question,
        )

    context = format_context(docs)
    chain = RAG_PROMPT | get_llm() | StrOutputParser()
    answer = chain.invoke({"context": context, "question": question})

    sources = [
        SourceChunk(
            content=doc.page_content[:300] + ("..." if len(doc.page_content) > 300 else ""),
            source=doc.metadata.get("source", "unknown"),
            score=round(score, 4),
        )
        for doc, score in scored_docs
    ]

    return QueryResponse(answer=answer, sources=sources, question=question)
