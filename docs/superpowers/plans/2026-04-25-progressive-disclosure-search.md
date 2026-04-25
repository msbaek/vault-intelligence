# Progressive Disclosure Search Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `vis search "쿼리" --titles-only`로 인덱스만(path/score/title) 반환받고, 관심 있는 결과의 본문은 `vis get <path>` 또는 `vis search "쿼리" --full-content`로 따로 가져올 수 있다. 기본 동작(옵션 미지정)은 변경 없음.

**Architecture:** 서버(`src/server.py`, FastAPI port 8741)의 `/search` 엔드포인트에 `include` Query 파라미터를 추가하고, 신규 `/document` GET/POST 엔드포인트를 추가한다. CLI(`src/__main__.py`)와 HTTP 클라이언트(`src/client.py`)는 server 변경의 wrapper 역할만 한다. 검색 로직(`src/features/advanced_search.py`)은 변경하지 않는다.

**Tech Stack:** Python 3.10+, FastAPI, Pydantic, httpx, argparse, pytest + FastAPI TestClient. 신규 의존성 없음 (stdlib + 기존 의존성만).

---

## Pre-conditions (실행 전 반드시 확인)

- [ ] **PC-1**: 현재 main 브랜치의 uncommitted changes (`src/server.py` lifespan 백그라운드화, `src/__main__.py`, `src/client.py`)가 commit 또는 stash되어 있음
- [ ] **PC-2**: `cd /Users/msbaek/git/vault-intelligence && git status -s`가 `M`/`??` 표시 없이 깨끗함, 또는 격리된 worktree에서 작업 중
- [ ] **PC-3**: pytest 환경 동작 확인: `cd /Users/msbaek/git/vault-intelligence && pytest tests/test_server.py -v --collect-only`로 테스트 수집 성공
- [ ] **PC-4**: 데몬이 실행 중이라면 정지 (`vis stop` 또는 port 8741 LISTEN 종료) — 테스트 중 인덱스 충돌 방지

**격리 권장:** `superpowers:using-git-worktrees` skill로 `feature/progressive-disclosure-search` worktree를 만들어 진행. 25GB 모델/인덱스 영향 차단.

---

## Constraints (non-negotiable)

- **C1**: `pyproject.toml`이 의존성 source of truth. **신규 의존성 추가 금지** (stdlib + 기존 fastapi/pydantic/httpx만 사용)
- **C2**: server (port 8741)와 CLI 분리 구조 유지 — 검색/문서 fetch 로직은 server에만, CLI는 HTTP wrapper
- **C3**: 기존 `vis search "쿼리"` 호출 backward compatible — 옵션 미지정 시 출력 포맷 동일
- **C4**: TDD red-green-blue (각 task에 명시). 기존 `tests/test_server.py` mock_engine fixture 패턴 그대로 따름
- **C5**: 한국어 path/title/content 처리 — 모든 서버/CLI 테스트에 한글 케이스 1개 이상 포함

## Failure Conditions

- **F1**: 기존 `vis search "쿼리"` (옵션 없이) 호출 시 출력 포맷이 변경됨 → 즉시 revert
- **F2**: server endpoint 변경으로 client 호환성 깨짐 (HTTP 422/500) → revert
- **F3**: `pyproject.toml` 의존성 추가 → revert
- **F4**: 25GB 모델/인덱스에 영향 (`engine.build_index` 강제 호출 등 재인덱싱 트리거) → revert

---

## File Structure

| 파일 | 역할 | 변경 유형 |
|------|------|-----------|
| `src/server.py:48-55` | `SearchResultResponse` 옵셔널 필드화 | 수정 |
| `src/server.py:205-263` | `/search` 엔드포인트에 `include` 파라미터 추가 | 수정 |
| `src/server.py:288 직전` | `/document` GET, `/document/batch` POST 신규 엔드포인트 | 추가 |
| `src/server.py` (적절한 위치) | `DocumentResponse`, `DocumentBatchRequest` Pydantic 모델 | 추가 |
| `src/client.py:105-151` | `search()`에 `include` 파라미터 추가 | 수정 |
| `src/client.py:153 직후` | `get_document()`, `get_documents_batch()` 추가 | 추가 |
| `src/__main__.py:2062-2074` | search subparser에 `--titles-only`, `--full-content` 옵션 추가 | 수정 |
| `src/__main__.py:2258-2278` | search 핸들러 출력 분기 | 수정 |
| `src/__main__.py` (related 다음) | `get` 서브커맨드 + 핸들러 추가 | 추가 |
| `tests/test_server.py` | `/search` include + `/document` 테스트 추가 | 수정 |
| `tests/test_client.py` | `client.search(include=...)`, `get_document()` 테스트 추가 | 수정 |
| `tests/test_main.py` (없으면 신규) | argparse 옵션 파싱 단위 테스트 | 추가 또는 수정 |
| `README.md:53-` (`### 검색 옵션` 섹션) | progressive disclosure 워크플로우 예시 | 수정 |
| `CHANGELOG.md` | 신규 기능 entry | 추가 또는 수정 |

---

## Phase 1: server `/search`에 `include` 파라미터 추가

### Task 1.1: `SearchResultResponse` 옵셔널 필드화 (TDD red-green-blue)

**Files:**
- Modify: `src/server.py:48-55`
- Test: `tests/test_server.py` (mock_engine fixture 활용 신규 테스트)

- [ ] **Step 1.1.1: Red — 옵셔널 필드 직렬화 테스트 추가**

`tests/test_server.py` 끝부분에 추가:

```python
def test_search_result_response_optional_fields():
    """SearchResultResponse는 snippet/match_type 없이도 직렬화 가능해야 한다."""
    from src.server import SearchResultResponse

    minimal = SearchResultResponse(path="ko/한글-문서.md", score=0.85, title="한글 문서", rank=1)
    payload = minimal.model_dump(exclude_none=True)

    assert "snippet" not in payload
    assert "match_type" not in payload
    assert payload["title"] == "한글 문서"
    assert payload["path"] == "ko/한글-문서.md"
```

- [ ] **Step 1.1.2: Run test — FAIL 확인**

```bash
cd /Users/msbaek/git/vault-intelligence
pytest tests/test_server.py::test_search_result_response_optional_fields -v
```

Expected: FAIL — `pydantic` validation error: snippet/match_type missing required field.

- [ ] **Step 1.1.3: Green — 필드를 Optional로 변경**

`src/server.py:48-55` 교체:

```python
class SearchResultResponse(BaseModel):
    """Single search result. snippet/match_type은 include=index 모드에서 생략됨."""
    path: str
    score: float
    title: str
    rank: int = 0
    snippet: Optional[str] = None
    match_type: Optional[str] = None
```

상단 import 보강 (`src/server.py:14` 근처 `from typing import Dict, List` 줄을):

```python
from typing import Dict, List, Optional
```

- [ ] **Step 1.1.4: Run test — PASS 확인**

```bash
pytest tests/test_server.py::test_search_result_response_optional_fields -v
```

Expected: PASS.

- [ ] **Step 1.1.5: 회귀 검증 — 기존 테스트 모두 PASS**

```bash
pytest tests/test_server.py -v
```

Expected: 전체 PASS. (기존 테스트가 snippet/match_type을 명시적으로 채우고 있으면 영향 없음)

- [ ] **Step 1.1.6: Commit**

```bash
git add src/server.py tests/test_server.py
git commit -m "refactor(server): SearchResultResponse의 snippet/match_type을 Optional로 변경"
```

---

### Task 1.2: `/search`에 `include` 파라미터 추가 (TDD)

**Files:**
- Modify: `src/server.py:205-263`
- Modify: `src/server.py:123-145` (`_convert_search_result`)
- Test: `tests/test_server.py`

- [ ] **Step 1.2.1: Red — `include=index` 모드 테스트 추가**

`tests/test_server.py`에 추가 (mock_engine fixture 패턴 그대로 사용 — 기존 테스트 참고하여 client fixture 활용):

```python
def test_search_endpoint_include_index_excludes_snippet(client_with_mock_engine):
    """include=index 모드에서 snippet/match_type이 응답에서 제외되어야 한다."""
    client = client_with_mock_engine
    response = client.get("/search", params={"query": "한글 검색", "include": "index"})

    assert response.status_code == 200
    body = response.json()
    assert body["results"], "검색 결과가 비어있음"
    for r in body["results"]:
        assert "snippet" not in r or r["snippet"] is None
        assert "match_type" not in r or r["match_type"] is None
        # 인덱스 모드에서도 path/score/title/rank는 항상 존재
        assert {"path", "score", "title", "rank"}.issubset(r.keys())


def test_search_endpoint_default_include_keeps_snippet(client_with_mock_engine):
    """include 미지정(기본값) 시 기존 동작 유지 — snippet 포함."""
    client = client_with_mock_engine
    response = client.get("/search", params={"query": "한글 검색"})

    assert response.status_code == 200
    body = response.json()
    assert body["results"]
    # 적어도 첫 결과는 snippet 필드를 가진다 (기존 동작)
    assert body["results"][0].get("snippet") is not None


def test_search_endpoint_include_full_explicit(client_with_mock_engine):
    """include=full 명시 시에도 snippet 포함."""
    client = client_with_mock_engine
    response = client.get("/search", params={"query": "한글 검색", "include": "full"})

    assert response.status_code == 200
    assert response.json()["results"][0].get("snippet") is not None


def test_search_endpoint_include_invalid_returns_422(client_with_mock_engine):
    """잘못된 include 값은 422 반환."""
    client = client_with_mock_engine
    response = client.get("/search", params={"query": "x", "include": "garbage"})
    assert response.status_code == 422
```

> `client_with_mock_engine` fixture가 기존 `tests/test_server.py`에 정확히 같은 이름으로 존재하지 않으면, 기존에 사용되는 fixture 이름으로 치환할 것 (e.g. `test_client`, `client`). 파일 상단 import 영역에서 사용 패턴 확인.

- [ ] **Step 1.2.2: Run tests — FAIL 확인**

```bash
pytest tests/test_server.py -v -k "include_index or default_include or include_full or include_invalid"
```

Expected: 4개 모두 FAIL — `include` 파라미터가 정의되지 않음 (422 또는 무시).

- [ ] **Step 1.2.3: Green — `Literal` 타입의 include 파라미터 추가**

`src/server.py:14` 근처 import 보강 (이미 Optional 추가했으면 같은 줄에 Literal 추가):

```python
from typing import Dict, List, Optional, Literal
```

`src/server.py:123-145` `_convert_search_result` 함수 시그니처를 다음과 같이 교체 (정확한 함수 본문은 기존 파일을 read한 뒤 그 내부 로직을 유지하면서 분기만 추가):

```python
def _convert_search_result(
    result: SearchResult,
    rank: int = 0,
    include: Literal["full", "index"] = "full",
) -> SearchResultResponse:
    """SearchResult → SearchResultResponse. include='index'이면 snippet/match_type 생략."""
    base = {
        "path": result.document.path,
        "score": result.score,
        "title": result.document.title or Path(result.document.path).stem,
        "rank": rank,
    }
    if include == "index":
        return SearchResultResponse(**base)
    return SearchResultResponse(
        **base,
        snippet=getattr(result, "snippet", "") or "",
        match_type=getattr(result, "match_type", "") or "",
    )
```

> 기존 `_convert_search_result` 본문에서 snippet/match_type을 어떻게 추출하는지 확인 후 그 로직을 그대로 `else` 분기에 옮길 것. 위 코드는 골격일 뿐 — 실제 함수의 SearchResult 속성 접근 패턴을 그대로 재사용.

`src/server.py:205-263` `/search` 엔드포인트 시그니처/본문 교체:

```python
    @app.get("/search", response_model=SearchResponse)
    async def search(
        query: str = Query(..., description="Search query"),
        top_k: int = Query(10, description="Number of results to return"),
        threshold: float = Query(0.0, description="Similarity threshold"),
        search_method: str = Query("hybrid", description="Search method: semantic, keyword, hybrid, colbert"),
        rerank: bool = Query(False, description="Enable reranking"),
        include: Literal["full", "index"] = Query(
            "full",
            description="Response payload depth: 'full'(기본, snippet/match_type 포함) or 'index'(path/score/title/rank만)",
        ),
    ):
        """Search endpoint with progressive disclosure (include=full|index)."""
        if not _is_indexed():
            raise HTTPException(status_code=503, detail="Index not built yet")

        engine: AdvancedSearchEngine = _state["engine"]
        if engine is None:
            raise HTTPException(status_code=503, detail="Search engine not initialized")

        try:
            if rerank:
                results: List[SearchResult] = engine.search_with_reranking(
                    query=query,
                    search_method=search_method,
                    initial_k=min(top_k * 3, 100),
                    final_k=top_k,
                    threshold=threshold,
                    use_reranker=True,
                )
            else:
                if search_method == "semantic":
                    results = engine.semantic_search(query, top_k=top_k, threshold=threshold)
                elif search_method == "keyword":
                    results = engine.keyword_search(query, top_k=top_k)
                elif search_method == "colbert":
                    results = engine.colbert_search(query, top_k=top_k, threshold=threshold)
                elif search_method == "hybrid":
                    results = engine.hybrid_search(query, top_k=top_k, threshold=threshold)
                else:
                    raise HTTPException(status_code=400, detail=f"Invalid search method: {search_method}")

            response_results = [
                _convert_search_result(r, rank=i + 1, include=include)
                for i, r in enumerate(results)
            ]

            return SearchResponse(
                results=response_results,
                query=query,
                search_method=search_method,
                total=len(response_results),
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Search failed: {e}")
            raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")
```

- [ ] **Step 1.2.4: Run tests — PASS 확인**

```bash
pytest tests/test_server.py -v
```

Expected: 전체 PASS (신규 4개 + 기존 테스트).

- [ ] **Step 1.2.5: 토큰 절감 측정 (수동 sanity check)**

데몬이 죽어 있는 상태에서:

```bash
cd /Users/msbaek/git/vault-intelligence
python -c "
from fastapi.testclient import TestClient
import json
# 위 테스트와 동일한 fixture 구성 후
# r1 = client.get('/search', params={'query': '테스트', 'include': 'full'})
# r2 = client.get('/search', params={'query': '테스트', 'include': 'index'})
# print('full size:', len(r1.text), 'bytes')
# print('index size:', len(r2.text), 'bytes')
# print('절감률:', (1 - len(r2.text)/len(r1.text)) * 100, '%')
"
```

Expected: index 모드가 full 모드 대비 60% 이상 작음.

> 정확한 측정은 `pytest -s`로 testfile 내부에서 stdout 출력해도 무방. 측정 결과는 commit message에 기록.

- [ ] **Step 1.2.6: Commit**

```bash
git add src/server.py tests/test_server.py
git commit -m "feat(server): /search endpoint에 include=index|full 파라미터 추가"
```

---

## Phase 2: server `/document` 엔드포인트 추가

### Task 2.1: `GET /document` 단일 fetch (TDD)

**Files:**
- Modify: `src/server.py` (288번 라인 `return app` 직전 신규 엔드포인트)
- Modify: `src/server.py` (Pydantic 모델 영역, ~75번 라인 직후) `DocumentResponse` 추가
- Test: `tests/test_server.py`

- [ ] **Step 2.1.1: Red — 단일 문서 fetch 테스트 추가**

`tests/test_server.py`에 추가:

```python
def test_get_document_returns_full_content(client_with_mock_engine, test_vault):
    """GET /document?path=...로 본문/frontmatter 반환."""
    client = client_with_mock_engine
    response = client.get("/document", params={"path": "test_doc1.md"})

    assert response.status_code == 200
    body = response.json()
    assert body["path"] == "test_doc1.md"
    assert "Python" in body["content"]
    assert body["frontmatter"]["title"] == "Test Document 1"
    assert "test" in body["frontmatter"].get("tags", [])


def test_get_document_korean_path(client_with_mock_engine):
    """한글 경로/콘텐츠 처리."""
    # mock_engine fixture에 한글 문서 1건이 포함되어야 함 — fixture를 보강한다.
    client = client_with_mock_engine
    response = client.get("/document", params={"path": "한글-문서.md"})

    assert response.status_code == 200
    body = response.json()
    assert body["path"] == "한글-문서.md"
    assert "한글" in body["title"]


def test_get_document_not_found(client_with_mock_engine):
    """존재하지 않는 path는 404."""
    client = client_with_mock_engine
    response = client.get("/document", params={"path": "does-not-exist.md"})
    assert response.status_code == 404


def test_get_document_503_when_not_indexed(test_client_no_engine):
    """엔진 미초기화 시 503."""
    response = test_client_no_engine.get("/document", params={"path": "x.md"})
    assert response.status_code == 503
```

> `mock_engine` fixture에 한글 문서를 추가해야 한다 — `tests/test_server.py`의 `mock_engine` 픽스처(현재 100번대 라인) `mock_docs` 리스트에 다음 항목 추가:

```python
        Document(
            path="한글-문서.md",
            title="한글 문서 테스트",
            content="한글 문서 본문입니다. progressive disclosure 검증용.",
            tags=["한글", "test"],
            frontmatter={"title": "한글 문서 테스트", "tags": ["한글", "test"]},
            word_count=10,
            char_count=50,
            file_size=200,
            modified_at=datetime.now(),
        ),
```

- [ ] **Step 2.1.2: Run tests — FAIL 확인**

```bash
pytest tests/test_server.py -v -k "get_document or test_get_document"
```

Expected: 4개 모두 FAIL — `/document` 엔드포인트 없음 (404 from FastAPI router).

- [ ] **Step 2.1.3: Green — `DocumentResponse` 모델 + 엔드포인트 구현**

`src/server.py`의 Pydantic 모델 영역(75번 라인 `HealthResponse` 정의 직후)에 추가:

```python
class DocumentResponse(BaseModel):
    """단일 문서 본문 응답."""
    path: str
    title: str
    content: str
    frontmatter: Dict
    tags: List[str] = []
    word_count: int = 0
    char_count: int = 0


class DocumentBatchRequest(BaseModel):
    """다중 문서 batch fetch 요청."""
    paths: List[str]


class DocumentBatchResponse(BaseModel):
    """다중 문서 batch fetch 응답."""
    documents: List[DocumentResponse]
    not_found: List[str] = []
```

`src/server.py:288 `return app`` 직전에 신규 엔드포인트 추가:

```python
    @app.get("/document", response_model=DocumentResponse)
    async def get_document(path: str = Query(..., description="Document path (vault-relative)")):
        """단일 문서 본문/frontmatter 반환."""
        if not _is_indexed():
            raise HTTPException(status_code=503, detail="Index not built yet")
        engine: AdvancedSearchEngine = _state["engine"]
        if engine is None:
            raise HTTPException(status_code=503, detail="Search engine not initialized")

        # AdvancedSearchEngine은 documents: List[Document]를 보관 (server.py:44 참고)
        doc = next((d for d in engine.documents if d.path == path), None)
        if doc is None:
            raise HTTPException(status_code=404, detail=f"Document not found: {path}")

        return DocumentResponse(
            path=doc.path,
            title=doc.title or "",
            content=doc.content or "",
            frontmatter=doc.frontmatter or {},
            tags=list(doc.tags or []),
            word_count=getattr(doc, "word_count", 0),
            char_count=getattr(doc, "char_count", 0),
        )
```

> `engine.documents`가 정확한 속성명인지 `src/features/advanced_search.py`에서 확인 후 진행. `_document_count` 함수(`src/server.py:42-44`)가 `engine.documents`를 참조하므로 같은 속성명 사용.

- [ ] **Step 2.1.4: Run tests — PASS 확인**

```bash
pytest tests/test_server.py -v
```

Expected: 전체 PASS.

- [ ] **Step 2.1.5: Commit**

```bash
git add src/server.py tests/test_server.py
git commit -m "feat(server): GET /document 엔드포인트로 단일 문서 본문 fetch 지원"
```

---

### Task 2.2: `POST /document/batch` 다중 fetch (TDD)

**Files:**
- Modify: `src/server.py` (Task 2.1에서 추가한 `/document` 다음 줄)
- Test: `tests/test_server.py`

- [ ] **Step 2.2.1: Red — batch 테스트 추가**

`tests/test_server.py`에 추가:

```python
def test_get_document_batch_returns_multiple(client_with_mock_engine):
    """POST /document/batch — 다중 path를 한 번에 가져온다."""
    client = client_with_mock_engine
    response = client.post(
        "/document/batch",
        json={"paths": ["test_doc1.md", "test_doc2.md", "한글-문서.md"]},
    )

    assert response.status_code == 200
    body = response.json()
    assert len(body["documents"]) == 3
    assert {d["path"] for d in body["documents"]} == {
        "test_doc1.md",
        "test_doc2.md",
        "한글-문서.md",
    }
    assert body["not_found"] == []


def test_get_document_batch_partial_not_found(client_with_mock_engine):
    """일부 path만 존재해도 200, 못 찾은 path는 not_found로."""
    client = client_with_mock_engine
    response = client.post(
        "/document/batch",
        json={"paths": ["test_doc1.md", "missing.md"]},
    )

    assert response.status_code == 200
    body = response.json()
    assert len(body["documents"]) == 1
    assert body["documents"][0]["path"] == "test_doc1.md"
    assert body["not_found"] == ["missing.md"]


def test_get_document_batch_empty_paths_returns_422(client_with_mock_engine):
    """빈 paths는 422 (pydantic validation)."""
    client = client_with_mock_engine
    response = client.post("/document/batch", json={"paths": []})
    # 빈 리스트 자체는 valid, 응답은 200 with empty results
    assert response.status_code == 200
    assert response.json()["documents"] == []
```

- [ ] **Step 2.2.2: Run tests — FAIL 확인**

```bash
pytest tests/test_server.py -v -k "document_batch"
```

Expected: 3개 FAIL — 엔드포인트 없음.

- [ ] **Step 2.2.3: Green — `/document/batch` 엔드포인트 추가**

`src/server.py`의 Task 2.1 `get_document` 함수 직후에 추가:

```python
    @app.post("/document/batch", response_model=DocumentBatchResponse)
    async def get_document_batch(request: DocumentBatchRequest):
        """다중 문서 batch fetch — not found는 not_found 배열로 반환."""
        if not _is_indexed():
            raise HTTPException(status_code=503, detail="Index not built yet")
        engine: AdvancedSearchEngine = _state["engine"]
        if engine is None:
            raise HTTPException(status_code=503, detail="Search engine not initialized")

        by_path = {d.path: d for d in engine.documents}
        documents: List[DocumentResponse] = []
        not_found: List[str] = []

        for p in request.paths:
            doc = by_path.get(p)
            if doc is None:
                not_found.append(p)
                continue
            documents.append(DocumentResponse(
                path=doc.path,
                title=doc.title or "",
                content=doc.content or "",
                frontmatter=doc.frontmatter or {},
                tags=list(doc.tags or []),
                word_count=getattr(doc, "word_count", 0),
                char_count=getattr(doc, "char_count", 0),
            ))

        return DocumentBatchResponse(documents=documents, not_found=not_found)
```

- [ ] **Step 2.2.4: Run tests — PASS**

```bash
pytest tests/test_server.py -v
```

Expected: 전체 PASS.

- [ ] **Step 2.2.5: Commit**

```bash
git add src/server.py tests/test_server.py
git commit -m "feat(server): POST /document/batch로 다중 문서 batch fetch 지원"
```

---

## Phase 3: CLI `--titles-only` / `--full-content` 옵션

### Task 3.1: `client.search()`에 `include` 파라미터 추가 (TDD)

**Files:**
- Modify: `src/client.py:105-151`
- Test: `tests/test_client.py`

- [ ] **Step 3.1.1: Red — client search include 테스트 추가**

`tests/test_client.py`에 (해당 파일이 있다고 가정 — 없으면 신규 생성, `from unittest.mock import patch` + `httpx.MockTransport` 패턴):

```python
def test_client_search_passes_include_param():
    """client.search(include='index')는 server에 include=index 전달."""
    from src.client import VisClient
    import httpx

    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["params"] = dict(request.url.params)
        return httpx.Response(200, json={
            "results": [{"path": "x.md", "score": 0.9, "title": "x", "rank": 1}],
            "query": "테스트",
            "search_method": "hybrid",
            "total": 1,
        })

    transport = httpx.MockTransport(handler)
    with patch("httpx.Client") as mock_client:
        mock_client.return_value.__enter__.return_value = httpx.Client(transport=transport)
        client = VisClient()
        client._is_server_running = lambda: True  # 서버 체크 우회
        results = client.search(query="테스트", include="index")

    assert captured["params"].get("include") == "index"
    assert results[0]["path"] == "x.md"


def test_client_search_default_include_is_full():
    """include 미지정 시 server에 include 파라미터를 전송하지 않거나 'full'."""
    # 위와 같은 패턴, captured["params"].get("include")가 'full' 또는 미존재 모두 허용
    ...
```

> 기존 `tests/test_client.py` mock 패턴을 먼저 확인하고 그 스타일에 맞춰야 한다. 위 코드는 patch 방식의 한 예시일 뿐. `tests/test_client.py`가 없으면 `tests/test_server.py`처럼 `httpx.MockTransport`로 외부 호출만 가로채는 가벼운 테스트로 작성.

- [ ] **Step 3.1.2: Run — FAIL 확인**

```bash
pytest tests/test_client.py -v -k "include"
```

Expected: FAIL — `include` 파라미터 미지원 (TypeError 또는 무시).

- [ ] **Step 3.1.3: Green — `client.search()` 시그니처 확장**

`src/client.py:105-151` 교체 (signature 부분):

```python
    def search(
        self,
        query: str,
        top_k: int = 10,
        threshold: float = 0.0,
        search_method: str = "hybrid",
        rerank: bool = False,
        include: str = "full",
        auto_start: bool = True,
    ) -> List[Dict]:
        """
        Execute search query.

        Args:
            query: Search query
            top_k: Number of results to return
            threshold: Similarity threshold
            search_method: Search method (semantic, keyword, hybrid, colbert)
            rerank: Enable reranking
            include: Response depth — 'full'(default, snippet 포함) or 'index'(path/score/title/rank만)
            auto_start: Auto-start server if not running

        Returns:
            List of search result dictionaries
        """
        if not self.is_server_running():
            if not auto_start:
                raise ServerNotRunning("Server is not running. Start with auto_start=True or manually start the server.")
            self._ensure_server()

        params = {
            "query": query,
            "top_k": top_k,
            "threshold": threshold,
            "search_method": search_method,
            "rerank": rerank,
            "include": include,
        }

        with httpx.Client(timeout=30.0) as client:
            response = client.get(f"{self.base_url}/search", params=params)
            response.raise_for_status()
            data = response.json()
            return data.get("results", [])
```

- [ ] **Step 3.1.4: Run — PASS**

```bash
pytest tests/test_client.py -v
```

Expected: 전체 PASS.

- [ ] **Step 3.1.5: Commit**

```bash
git add src/client.py tests/test_client.py
git commit -m "feat(client): VisClient.search()에 include 파라미터 추가"
```

---

### Task 3.2: argparse 옵션 추가 + 출력 분기 (TDD)

**Files:**
- Modify: `src/__main__.py:2062-2074` (search subparser)
- Modify: `src/__main__.py:2258-2278` (search 핸들러)
- Test: `tests/test_main.py` (없으면 신규)

- [ ] **Step 3.2.1: Red — argparse 옵션 테스트**

`tests/test_main.py` (없으면 신규 생성):

```python
import pytest
from src.__main__ import _build_parser  # 아래 Step 3.2.3에서 추출할 함수


def test_search_titles_only_flag():
    parser = _build_parser()
    args = parser.parse_args(["search", "한글 쿼리", "--titles-only"])
    assert args.titles_only is True
    assert args.full_content is False


def test_search_full_content_flag():
    parser = _build_parser()
    args = parser.parse_args(["search", "x", "--full-content"])
    assert args.full_content is True
    assert args.titles_only is False


def test_search_titles_and_full_mutually_exclusive():
    parser = _build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["search", "x", "--titles-only", "--full-content"])
```

- [ ] **Step 3.2.2: Run — FAIL**

```bash
pytest tests/test_main.py -v
```

Expected: FAIL — `_build_parser` 미존재, 또는 옵션 미정의.

- [ ] **Step 3.2.3: Green — `_build_parser()` 추출 + 옵션 추가**

`src/__main__.py:2046` `def main()` 함수에서 `parser = argparse.ArgumentParser(...)`부터 `args = parser.parse_args()` 직전까지의 parser/subparsers 정의 블록을 통째로 별도 함수로 추출:

```python
def _build_parser() -> "argparse.ArgumentParser":
    """argparse 파서를 빌드. 테스트에서 직접 호출 가능하도록 분리."""
    parser = argparse.ArgumentParser(
        prog="vis",
        description="Vault Intelligence System - Sentence Transformers 기반 지능형 검색 시스템",
    )
    parser.add_argument("--data-dir", help="데이터 디렉토리 경로 (기본값: ~/git/vault-intelligence)")
    parser.add_argument("--vault-path", help="Vault 경로 (지정하지 않으면 설정 파일에서 읽음)")
    parser.add_argument("--config", help="설정 파일 경로")
    parser.add_argument("--verbose", action="store_true", help="상세 로그 출력")

    subparsers = parser.add_subparsers(dest="command", title="commands")

    # --- search ---
    p = subparsers.add_parser("search", help="하이브리드 검색 (semantic, keyword, colbert)")
    # ... (기존 옵션 모두 옮김 — src/__main__.py:2063-2074)
    p.add_argument("query", help="검색 쿼리")
    p.add_argument("--top-k", type=int, default=10, help="상위 K개 결과 (기본값: 10)")
    p.add_argument("--threshold", type=float, default=0.3, help="유사도 임계값 (기본값: 0.3)")
    p.add_argument("--rerank", action="store_true", help="재순위화 활성화 (BGE Reranker V2-M3)")
    p.add_argument("--search-method", choices=["semantic", "keyword", "hybrid", "colbert"], default="hybrid")
    p.add_argument("--expand", action="store_true", help="쿼리 확장 활성화 (동의어 + HyDE)")
    p.add_argument("--no-synonyms", action="store_true", help="동의어 확장 비활성화")
    p.add_argument("--no-hyde", action="store_true", help="HyDE 확장 비활성화")
    p.add_argument("--with-centrality", action="store_true", help="중심성 점수를 검색 랭킹에 반영")
    p.add_argument("--centrality-weight", type=float, default=0.2)
    p.add_argument("--sample-size", type=int)
    p.add_argument("--output", nargs="?", const="")

    # 신규: progressive disclosure 옵션 (mutually exclusive)
    include_group = p.add_mutually_exclusive_group()
    include_group.add_argument(
        "--titles-only",
        action="store_true",
        help="인덱스(path/score/title)만 출력 — 토큰 절감용",
    )
    include_group.add_argument(
        "--full-content",
        action="store_true",
        help="snippet 포함 (기본값과 동일)",
    )

    # --- related ---
    # ... (기존 모든 서브파서 옮김. src/__main__.py:2076 이후를 그대로 복사)

    return parser


def main():
    """메인 함수"""
    parser = _build_parser()
    args = parser.parse_args()
    # ... (기존 main 본문에서 parser/subparsers 정의 블록 이후 부분만 남김)
```

> **주의:** 기존 main()의 모든 서브파서 정의(search, related, collect, analyze, analyze-gaps, reindex, tag, clean-tags, generate-moc, summarize, review, add-related-docs 등)를 빠짐없이 `_build_parser()`로 옮겨야 함. 누락 시 다른 기존 명령이 깨진다. **diff를 작게 유지하려면 통째로 cut-paste**.

`src/__main__.py:2258-2278` search 핸들러를 다음과 같이 변경:

```python
    if args.command == "search":
        from src.client import VisClient
        client = VisClient()
        try:
            include = "index" if args.titles_only else "full"
            results = client.search(
                query=args.query,
                top_k=args.top_k,
                threshold=args.threshold,
                search_method=args.search_method,
                rerank=args.rerank,
                include=include,
            )
            print(f"\n📄 검색 결과 ({len(results)}개):")
            print("-" * 80)
            for i, r in enumerate(results, 1):
                print(f"\n{i}. [{r['score']:.4f}] {r['path']}")
                if include == "full" and r.get("snippet"):
                    print(f"   {r['snippet'][:150]}")
            print("\n✅ 검색 완료!")
            return
        except Exception as e:
            print(f"❌ 오류: {e}")
            sys.exit(1)
```

- [ ] **Step 3.2.4: Run — PASS**

```bash
pytest tests/test_main.py -v
pytest tests/ -v   # 전체 회귀
```

Expected: 전체 PASS.

- [ ] **Step 3.2.5: 수동 sanity check (데몬 띄워야 함)**

```bash
vis serve  # 데몬 시작
sleep 5    # 인덱스 빌드 대기 (background, health 즉시 응답이지만 search는 인덱스 필요)
vis search "TDD" --titles-only
vis search "TDD"  # 기본값 — snippet 출력 확인
vis stop
```

Expected:
- `--titles-only`: snippet 줄(`   ...`)이 출력 안 됨
- 기본: 기존 출력 유지

- [ ] **Step 3.2.6: Commit**

```bash
git add src/__main__.py tests/test_main.py
git commit -m "feat(cli): vis search에 --titles-only/--full-content 옵션 추가"
```

---

## Phase 4: `vis get` 서브커맨드

### Task 4.1: `client.get_document()` / `get_documents_batch()` (TDD)

**Files:**
- Modify: `src/client.py` (Task 3.1에서 수정한 `search()` 다음에 추가)
- Test: `tests/test_client.py`

- [ ] **Step 4.1.1: Red — client get_document 테스트**

```python
def test_client_get_document_single():
    """client.get_document(path)는 단일 문서 본문을 반환."""
    from src.client import VisClient
    import httpx

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/document"
        assert request.url.params.get("path") == "한글-문서.md"
        return httpx.Response(200, json={
            "path": "한글-문서.md",
            "title": "한글 문서",
            "content": "본문 내용",
            "frontmatter": {"tags": ["한글"]},
            "tags": ["한글"],
            "word_count": 5,
            "char_count": 20,
        })

    transport = httpx.MockTransport(handler)
    # ... (Task 3.1과 동일한 패치 패턴)

    doc = client.get_document("한글-문서.md")
    assert doc["path"] == "한글-문서.md"
    assert doc["content"] == "본문 내용"


def test_client_get_documents_batch():
    """client.get_documents(paths)는 batch fetch."""
    # ... POST /document/batch 호출 검증
    # not_found 처리도 검증
```

- [ ] **Step 4.1.2: Run — FAIL**

```bash
pytest tests/test_client.py -v -k "get_document"
```

- [ ] **Step 4.1.3: Green — `get_document()` / `get_documents()` 구현**

`src/client.py`의 `search()` 메서드 다음에 추가:

```python
    def get_document(self, path: str, auto_start: bool = True) -> Dict:
        """단일 문서 본문 fetch."""
        if not self.is_server_running():
            if not auto_start:
                raise ServerNotRunning("Server is not running.")
            self._ensure_server()

        with httpx.Client(timeout=30.0) as client:
            response = client.get(f"{self.base_url}/document", params={"path": path})
            response.raise_for_status()
            return response.json()

    def get_documents(self, paths: List[str], auto_start: bool = True) -> Dict:
        """다중 문서 batch fetch. 반환: {'documents': [...], 'not_found': [...]}."""
        if not self.is_server_running():
            if not auto_start:
                raise ServerNotRunning("Server is not running.")
            self._ensure_server()

        with httpx.Client(timeout=30.0) as client:
            response = client.post(f"{self.base_url}/document/batch", json={"paths": paths})
            response.raise_for_status()
            return response.json()
```

- [ ] **Step 4.1.4: Run — PASS**

```bash
pytest tests/test_client.py -v
```

- [ ] **Step 4.1.5: Commit**

```bash
git add src/client.py tests/test_client.py
git commit -m "feat(client): VisClient.get_document() / get_documents() 추가"
```

---

### Task 4.2: argparse `get` 서브커맨드 + 핸들러

**Files:**
- Modify: `src/__main__.py` (Task 3.2 `_build_parser`의 `related` 서브파서 다음에 `get` 추가)
- Modify: `src/__main__.py` (search 핸들러 다음에 `get` 핸들러 추가)
- Test: `tests/test_main.py`

- [ ] **Step 4.2.1: Red — `vis get` 옵션 파싱 테스트**

`tests/test_main.py`에 추가:

```python
def test_get_subcommand_single_path():
    parser = _build_parser()
    args = parser.parse_args(["get", "한글-문서.md"])
    assert args.command == "get"
    assert args.paths == ["한글-문서.md"]
    assert args.format == "markdown"


def test_get_subcommand_multiple_paths():
    parser = _build_parser()
    args = parser.parse_args(["get", "a.md", "b.md", "한글.md", "--format", "json"])
    assert args.paths == ["a.md", "b.md", "한글.md"]
    assert args.format == "json"
```

- [ ] **Step 4.2.2: Run — FAIL**

- [ ] **Step 4.2.3: Green — `get` 서브파서 추가**

`_build_parser()`의 `related` 서브파서 정의 직후에 추가:

```python
    # --- get ---
    p = subparsers.add_parser("get", help="단일/다중 문서 본문 fetch (progressive disclosure layer 3)")
    p.add_argument("paths", nargs="+", help="문서 path(s) — 1개 이상")
    p.add_argument("--format", choices=["markdown", "json"], default="markdown", help="출력 포맷 (기본: markdown)")
```

`main()` 함수 안에 search 핸들러 다음에 `get` 핸들러 추가:

```python
    if args.command == "get":
        from src.client import VisClient
        import json as _json

        client = VisClient()
        try:
            if len(args.paths) == 1:
                doc = client.get_document(args.paths[0])
                docs = [doc]
                not_found: List[str] = []
            else:
                response = client.get_documents(args.paths)
                docs = response["documents"]
                not_found = response.get("not_found", [])

            if args.format == "json":
                print(_json.dumps({"documents": docs, "not_found": not_found}, ensure_ascii=False, indent=2))
            else:
                for d in docs:
                    print(f"\n# {d['title']} ({d['path']})\n")
                    if d.get("frontmatter"):
                        print("---")
                        for k, v in d["frontmatter"].items():
                            print(f"{k}: {v}")
                        print("---\n")
                    print(d["content"])
                    print("\n" + "─" * 80)
                if not_found:
                    print(f"\n⚠️ Not found: {', '.join(not_found)}")
            return
        except Exception as e:
            print(f"❌ 오류: {e}")
            sys.exit(1)
```

- [ ] **Step 4.2.4: Run — PASS**

```bash
pytest tests/test_main.py -v
```

- [ ] **Step 4.2.5: 수동 sanity check**

```bash
vis serve
sleep 5
vis search "TDD" --titles-only        # Layer 1
vis get "<위에서 본 path>"             # Layer 3 단일
vis get "path1.md" "path2.md"         # Layer 3 batch
vis get "한글-문서.md" --format json   # JSON 포맷
vis stop
```

- [ ] **Step 4.2.6: Commit**

```bash
git add src/__main__.py tests/test_main.py
git commit -m "feat(cli): vis get 서브커맨드로 progressive disclosure layer 3 지원"
```

---

## Phase 5: 문서 / CHANGELOG

### Task 5.1: README progressive disclosure 섹션 추가

**Files:**
- Modify: `README.md` (`### 검색 옵션` 섹션 끝, 53번 줄 부근 다음 위치)

- [ ] **Step 5.1.1: README의 `### 검색 옵션` 섹션 끝에 다음 내용 추가**

```markdown
### Progressive Disclosure 검색 워크플로우 (token 절감)

대량 결과를 빠르게 훑은 뒤 관심 있는 문서만 본문을 가져오는 3-layer 패턴:

```bash
# Layer 1: 인덱스만 (path/score/title) — 토큰 절감
vis search "TDD 리팩토링" --titles-only --top-k 30

# Layer 2: 의미적/구조적 이웃 탐색 (기존 명령)
vis related "<관심 path>" --top-k 5

# Layer 3: 본문 fetch (단일 또는 batch)
vis get "<관심 path>"
vis get "path1.md" "path2.md" "path3.md"
vis get "<path>" --format json   # 파이프라인 입력용
```

기본 `vis search` 호출은 변경 없음 — 옵션 미지정 시 snippet까지 출력된다.
```

- [ ] **Step 5.1.2: Commit**

```bash
git add README.md
git commit -m "docs(readme): progressive disclosure 검색 워크플로우 섹션 추가"
```

---

### Task 5.2: CHANGELOG entry

**Files:**
- Modify: `CHANGELOG.md` (없으면 신규 생성, vault-intelligence 루트)

- [ ] **Step 5.2.1: CHANGELOG.md 상단에 entry 추가**

```markdown
## [Unreleased]

### Added
- `vis search --titles-only` / `--full-content` 옵션으로 progressive disclosure 검색 지원
- `vis get <path>` 서브커맨드 — 단일/다중 문서 본문 fetch (`--format markdown|json`)
- HTTP API: `GET /search?include=index|full`, `GET /document?path=`, `POST /document/batch`
- Pydantic 모델: `DocumentResponse`, `DocumentBatchRequest`, `DocumentBatchResponse`

### Changed
- `SearchResultResponse.snippet`/`match_type`을 `Optional`로 변경 (backward compatible)
- `VisClient.search()`에 `include` 파라미터 추가 (기본값 `"full"`)
```

- [ ] **Step 5.2.2: Commit**

```bash
git add CHANGELOG.md
git commit -m "docs(changelog): progressive disclosure 검색 기능 entry 추가"
```

---

## Final Verification (모든 Phase 완료 후)

- [ ] **FV-1**: 전체 테스트 통과
  ```bash
  cd /Users/msbaek/git/vault-intelligence && pytest tests/ -v
  ```
- [ ] **FV-2**: backward compat — 기존 호출 변경 없음
  ```bash
  vis serve && sleep 5
  vis search "TDD"        # 기존 출력과 동일해야 함
  vis stop
  ```
- [ ] **FV-3**: 토큰 절감 측정 — `--titles-only` vs 기본 응답 크기 비교 (Phase 1.2 측정 결과 참조). 60% 이상 절감 확인.
- [ ] **FV-4**: 한글 path 처리 — `vis get "한글-문서.md"` UTF-8 정상 출력.
- [ ] **FV-5**: 의존성 변경 없음
  ```bash
  git diff main -- pyproject.toml requirements.txt
  ```
  Expected: empty diff.
- [ ] **FV-6**: 25GB 모델/인덱스 영향 없음 — `~/git/vault-intelligence/models/`, `~/git/vault-intelligence/cache/` mtime 변경 없음.

---

## Self-Review Checklist (실행 전 작성자 검토)

- [x] Spec coverage: 5개 Phase 모두 사용자 요청(Goal-1~3) 커버
- [x] Placeholder 없음: 모든 step에 실제 코드/명령 포함 — 단, fixture 이름(`client_with_mock_engine`)과 `_convert_search_result` 본문 일부는 기존 코드 참조 필요. 실행자가 해당 위치 확인 후 정확한 이름/구조 적용해야 함
- [x] Type consistency: `SearchResultResponse` 필드, `DocumentResponse` 필드, `include` 리터럴(`"full"|"index"`) 일관
- [x] TDD red-green-blue: 각 task에 명시적으로 분리됨
- [x] Backward compatibility: F1/F2 failure condition + FV-2 검증 step 포함
- [x] Frequent commit: 각 task 끝마다 commit step (Phase 1: 2 commits, Phase 2: 2, Phase 3: 2, Phase 4: 2, Phase 5: 2 → 총 10 commits)

---

## Resume Point

다음 task부터 시작:
- 미시작 → **Pre-conditions PC-1 부터** (uncommitted changes 정리)
- Phase N 진행 중 → 마지막 완료한 commit 확인 후 다음 미체크 step부터
