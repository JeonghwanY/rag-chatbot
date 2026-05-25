"""API 요청/응답 스키마."""
from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=1, description="사용자 질문")
    top_k: int | None = Field(None, ge=1, le=20, description="검색할 문서 개수")


class SourceChunk(BaseModel):
    content: str
    source: str
    score: float | None = None


class QueryResponse(BaseModel):
    answer: str
    sources: list[SourceChunk]
    question: str


class IngestResponse(BaseModel):
    status: str
    documents_indexed: int
    chunks_created: int
