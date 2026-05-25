# YouSync RAG Q&A Chatbot

LangChain과 Google Gemini API를 활용한 기술 문서 기반 RAG 챗봇.

## 파이프라인

```
문서 로드 → 청킹 → 임베딩 → ChromaDB 저장
                                      ↓
사용자 질문 → 임베딩 → 유사도 검색 → 컨텍스트 구성 → Gemini → 답변
```

## 기술 스택

- **LangChain**: 문서 로더, 텍스트 스플리터, 체인 구성
- **Google Gemini API**:
  - `gemini-2.0-flash`: 응답 생성
  - `text-embedding-004`: 임베딩
- **ChromaDB**: 로컬 벡터 저장소
- **FastAPI**: REST API 서버
- **Pydantic**: 스키마 검증

## 설치 및 실행

### 1. 환경 설정

```bash
# 가상환경
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 의존성
pip install -r requirements.txt

# 환경변수
cp .env.example .env
# .env 파일을 열어 GOOGLE_API_KEY 입력
```

Google API 키는 https://aistudio.google.com/app/apikey 에서 발급.

### 2. 문서 인덱싱

`data/docs/` 디렉토리에 PDF, MD, TXT 파일을 넣고 실행:

```bash
python -m scripts.ingest
```

### 3. API 서버 실행

```bash
uvicorn app.main:app --reload --port 8000
```

Swagger UI: http://localhost:8000/docs

### 4. 질의 예시

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "립싱크 정렬 품질 지표가 뭐야?"}'
```

응답:
```json
{
  "question": "립싱크 정렬 품질 지표가 뭐야?",
  "answer": "립싱크 정렬 품질 지표는 LSE-D(Lip-Sync Error Distance)와 LSE-C(Lip-Sync Error Confidence)입니다. ...",
  "sources": [
    {
      "content": "...",
      "source": "data/docs/yousync_tech_overview.md",
      "score": 0.82
    }
  ]
}
```

## 구조

```
rag-chatbot/
├── app/
│   ├── config.py        # 환경설정
│   ├── ingestion.py     # 문서 인덱싱 파이프라인
│   ├── retriever.py     # 유사도 검색
│   ├── chain.py         # RAG 체인 (프롬프트 + LLM)
│   ├── schemas.py       # Pydantic 모델
│   └── main.py          # FastAPI 엔트리포인트
├── scripts/
│   └── ingest.py        # CLI 인덱싱 스크립트
├── data/docs/           # 원본 문서
├── vectorstore/         # ChromaDB 저장소 (자동 생성)
└── requirements.txt
```

## 설계 노트

### 청크 크기와 검색 범위
- 청크 크기 800자 / 오버랩 100자로 설정. 문단 단위 의미를 유지하면서 검색 정밀도 확보.
- `RecursiveCharacterTextSplitter`로 문단 → 문장 → 단어 순으로 분할 시도하여 의미 경계 보존.

### 프롬프트 설계
- 컨텍스트 외 추론 금지 (할루시네이션 방지)
- "모르면 모른다" 명시
- temperature 0.2로 사실성 위주 응답
- 출처 인용 유도

### 검색 점수
- ChromaDB는 거리(distance)를 반환하므로 `1 - distance`로 직관적 점수화.
- 응답에 score를 포함하여 답변 신뢰도 판단 가능.
