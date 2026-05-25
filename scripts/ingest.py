"""CLI에서 문서 인덱싱 실행.

사용법:
    python -m scripts.ingest
"""
from app.ingestion import ingest_pipeline


if __name__ == "__main__":
    result = ingest_pipeline()
    print("\n=== 인덱싱 완료 ===")
    print(f"문서: {result['documents_indexed']}개")
    print(f"청크: {result['chunks_created']}개")
