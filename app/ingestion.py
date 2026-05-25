"""문서 인덱싱 파이프라인.

흐름: 원본 문서 로드 → 텍스트 청킹 → 임베딩 → ChromaDB 저장.
"""
from pathlib import Path

from langchain_chroma import Chroma
from langchain_community.document_loaders import (
    DirectoryLoader,
    PyPDFLoader,
    TextLoader,
)
from langchain_core.documents import Document
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.config import settings


def get_embeddings() -> GoogleGenerativeAIEmbeddings:
    """Gemini 임베딩 모델 인스턴스 반환."""
    return GoogleGenerativeAIEmbeddings(
        model=settings.embedding_model,
        google_api_key=settings.google_api_key,
    )


def load_documents(docs_dir: Path) -> list[Document]:
    """문서 디렉토리에서 PDF, MD, TXT 파일을 모두 로드."""
    if not docs_dir.exists():
        raise FileNotFoundError(f"문서 디렉토리가 없습니다: {docs_dir}")

    documents: list[Document] = []

    # 확장자별 로더 매핑 (MD는 텍스트로 충분히 처리됨)
    loaders = [
        ("**/*.pdf", PyPDFLoader, {}),
        ("**/*.md", TextLoader, {"encoding": "utf-8"}),
        ("**/*.txt", TextLoader, {"encoding": "utf-8"}),
    ]

    for pattern, loader_cls, loader_kwargs in loaders:
        loader = DirectoryLoader(
            str(docs_dir),
            glob=pattern,
            loader_cls=loader_cls,
            loader_kwargs=loader_kwargs,
            show_progress=True,
            use_multithreading=True,
        )
        try:
            docs = loader.load()
            documents.extend(docs)
            print(f"  - {pattern}: {len(docs)}개 로드")
        except Exception as e:
            print(f"  ! {pattern} 로드 실패: {e}")

    return documents


def split_documents(documents: list[Document]) -> list[Document]:
    """문서를 청크 단위로 분할.

    RecursiveCharacterTextSplitter는 문단 → 문장 → 단어 순으로
    분할 경계를 시도하므로 의미 단위가 잘 유지됨.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
        length_function=len,
    )
    return splitter.split_documents(documents)


def build_vectorstore(chunks: list[Document]) -> Chroma:
    """청크를 임베딩하여 ChromaDB에 저장."""
    settings.vectorstore_dir.mkdir(parents=True, exist_ok=True)

    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=get_embeddings(),
        persist_directory=str(settings.vectorstore_dir),
        collection_name="yousync_docs",
    )
    return vectorstore


def load_vectorstore() -> Chroma:
    """기존에 저장된 벡터스토어 로드."""
    return Chroma(
        persist_directory=str(settings.vectorstore_dir),
        embedding_function=get_embeddings(),
        collection_name="yousync_docs",
    )


def ingest_pipeline() -> dict:
    """전체 인덱싱 파이프라인 실행."""
    print(f"[1/3] 문서 로드: {settings.docs_dir}")
    documents = load_documents(settings.docs_dir)
    print(f"      총 {len(documents)}개 문서 로드 완료")

    if not documents:
        return {"documents_indexed": 0, "chunks_created": 0}

    print(f"[2/3] 청킹 (size={settings.chunk_size}, overlap={settings.chunk_overlap})")
    chunks = split_documents(documents)
    print(f"      총 {len(chunks)}개 청크 생성")

    print("[3/3] 임베딩 및 벡터스토어 저장")
    build_vectorstore(chunks)
    print(f"      저장 위치: {settings.vectorstore_dir}")

    return {
        "documents_indexed": len(documents),
        "chunks_created": len(chunks),
    }
