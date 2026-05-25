"""FastAPI 엔트리포인트.

엔드포인트:
  POST /query   : RAG 질의응답
  POST /ingest  : 문서 인덱싱 (재실행)
  GET  /health  : 헬스체크
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException

from app.chain import answer_question
from app.ingestion import ingest_pipeline
from app.schemas import IngestResponse, QueryRequest, QueryResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    """앱 시작 시 retriever 초기화 (벡터스토어 로드)."""
    print("애플리케이션 시작")
    yield
    print("애플리케이션 종료")


app = FastAPI(
    title="YouSync RAG Q&A API",
    description="LangChain + Gemini 기반 기술 문서 RAG 챗봇",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.post("/query", response_model=QueryResponse)
async def query(req: QueryRequest) -> QueryResponse:
    """질문을 받아 RAG 파이프라인으로 답변 생성."""
    try:
        return answer_question(req.question, top_k=req.top_k)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"질의 처리 실패: {e}")


@app.post("/ingest", response_model=IngestResponse)
async def ingest() -> IngestResponse:
    """문서 디렉토리를 재인덱싱."""
    try:
        result = ingest_pipeline()
        return IngestResponse(status="ok", **result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"인덱싱 실패: {e}")
