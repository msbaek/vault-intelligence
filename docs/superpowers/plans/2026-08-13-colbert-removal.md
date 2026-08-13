# ColBERT 검색 제거 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** ColBERT 검색 기능을 코드·캐시·설정·스크립트·문서에서 완전히 제거하여, 야간 재인덱싱이 메모리 32GB+ 를 요구하며 시스템 OOM을 유발하는 원인을 없앤다.

**Architecture:** `search_method == "colbert"`를 받는 모든 진입점(CLI, HTTP, rerank 파이프라인, 쿼리 확장, 관련문서, 중심성 부스팅)에 `hybrid`로 안전하게 대체하는 정규화를 넣고, 실제 ColBERT 구현(`colbert_search.py`, 캐시 테이블, 설정)을 통째로 삭제한다. 캐시 DB는 dense 임베딩만 남기고 재생성한다.

**Tech Stack:** Python 3.11, FastAPI, SQLite, pytest (pipx venv: `/Users/msbaek/.local/pipx/venvs/vault-intelligence/bin/python`)

**Spec:** `docs/superpowers/specs/2026-08-13-colbert-removal-design.md`

## Global Constraints

- 삭제가 아니라 안전한 대체다: `search_method=colbert` 요청은 에러가 아니라 경고 로그 + hybrid 결과로 응답해야 한다 (spec §4.1).
- ColBERT 캐시(32GB)는 백업하지 않고 삭제한다 (spec §4.2, 사용자 결정).
- `archive/`, `private/` 하위의 과거 기록 문서는 수정하지 않는다 (spec §5 AC6).
- 데몬 `phys_footprint` 기준선은 8GB 미만(신규 데몬 실측 6,445MB) — 검색 반복 후에도 이 근처에서 유지되어야 한다 (spec §5 AC3).
- 모든 코드 변경은 pipx venv(`/Users/msbaek/.local/pipx/venvs/vault-intelligence/bin/python`)로 검증한다 — 이 환경에만 torch/sentence-transformers/fastapi가 설치되어 있다.

---

### Task 1: AdvancedSearchEngine의 ColBERT 디스패치 제거

**Files:**
- Modify: `src/features/advanced_search.py`
- Test: `tests/test_advanced_search_colbert_fallback.py` (신규)

**Interfaces:**
- Produces: `normalize_search_method(search_method: str) -> str` — 모듈 레벨 함수. `"colbert"` 입력 시 경고 로그 후 `"hybrid"` 반환, 그 외는 입력 그대로 반환. Task 2·3에서 동일 함수를 재사용(import)한다.

- [ ] **Step 1: 실패하는 테스트 작성**

`tests/test_advanced_search_colbert_fallback.py`:

```python
"""normalize_search_method 폴백 동작 테스트 (ColBERT 제거, 2026-08-13)"""
import logging
from src.features.advanced_search import normalize_search_method


def test_colbert_falls_back_to_hybrid():
    assert normalize_search_method("colbert") == "hybrid"


def test_colbert_fallback_logs_warning(caplog):
    with caplog.at_level(logging.WARNING, logger="src.features.advanced_search"):
        normalize_search_method("colbert")
    assert any("colbert" in record.message.lower() for record in caplog.records)


def test_other_methods_pass_through_unchanged():
    for method in ["semantic", "keyword", "hybrid"]:
        assert normalize_search_method(method) == method
```

- [ ] **Step 2: 테스트 실행하여 실패 확인**

Run: `/Users/msbaek/.local/pipx/venvs/vault-intelligence/bin/python -m pip install pytest -q && /Users/msbaek/.local/pipx/venvs/vault-intelligence/bin/python -m pytest tests/test_advanced_search_colbert_fallback.py -v`
Expected: FAIL with `ImportError: cannot import name 'normalize_search_method'`

- [ ] **Step 3: `normalize_search_method` 추가**

`src/features/advanced_search.py`의 `logger = logging.getLogger(__name__)` 줄(현재 29번째 줄) 바로 다음, `@dataclass` 줄 앞에 삽입:

```python

def normalize_search_method(search_method: str) -> str:
    """ColBERT 요청을 hybrid로 안전하게 대체한다.

    ColBERT는 재인덱싱마다 문서 전량을 메모리에 적재해(2026-08-13 기준
    캐시 32GB) 시스템 OOM을 유발했고, 실사용은 전체 검색의 0.04%뿐이라
    제거되었다. 호출부를 깨뜨리지 않도록 에러 대신 경고 후 hybrid로
    폴백한다.
    """
    if search_method == "colbert":
        logger.warning(
            "search_method='colbert'는 제거되었습니다 (2026-08-13). hybrid로 대체합니다."
        )
        return "hybrid"
    return search_method
```

- [ ] **Step 4: `search_with_reranking`에 정규화 삽입 + colbert 분기 제거**

`search_with_reranking` 메서드(723번째 줄)의 docstring이 끝나는 `"""` 바로 다음, `# Reranker가 요청되었지만 사용 불가능한 경우` 주석 앞에 삽입:

```python
        search_method = normalize_search_method(search_method)

```

같은 메서드의 아래 블록에서 colbert 분기를 제거:

```python
        elif search_method == "colbert":
            return self.colbert_search(query, top_k=final_k, threshold=threshold, **search_kwargs)
```

를 삭제 (`elif search_method == "hybrid":` 바로 앞 줄).

- [ ] **Step 5: `colbert_search` 메서드 전체 삭제**

`def colbert_search(` 로 시작해 `return self.semantic_search(query, top_k, threshold)`로 끝나는 메서드 전체(`colbert_search` 메서드, `expanded_search` 정의 바로 앞까지)를 삭제한다. 삭제 범위는 아래 블록 전체:

```python
    def colbert_search(
        self,
        query: str,
        top_k: int = 10,
        threshold: float = 0.0
    ) -> List[SearchResult]:
        """
        ColBERT 기반 토큰 수준 late interaction 검색
        
        Args:
            query: 검색 쿼리
            top_k: 반환할 상위 결과 수
            threshold: 유사도 임계값
            
        Returns:
            ColBERT 검색 결과
        """
        try:
            from .colbert_search import ColBERTSearchEngine
            
            # ColBERT 엔진 설정
            colbert_config = self.config.get('colbert', {})
            
            # ColBERT 엔진 초기화 (캐시 포함)
            colbert_engine = ColBERTSearchEngine(
                model_name=colbert_config.get('model_name', 'BAAI/bge-m3'),
                device=colbert_config.get('device', self.config.get('model', {}).get('device')),
                use_fp16=colbert_config.get('use_fp16', True),
                cache_folder=colbert_config.get('cache_folder', self.config.get('model', {}).get('cache_folder')),
                max_length=colbert_config.get('max_length', self.config.get('model', {}).get('max_length', 4096)),
                cache_dir=self.cache_dir,
                enable_cache=colbert_config.get('enable_cache', True)
            )
            
            if not colbert_engine.is_available():
                logger.warning("ColBERT 엔진을 사용할 수 없습니다. 의미적 검색으로 대체합니다.")
                return self.semantic_search(query, top_k, threshold)
            
            # 인덱스가 없으면 구축 (캐시를 활용하여 전체 문서 처리 가능)
            if not colbert_engine.is_indexed:
                logger.info("ColBERT 인덱스 구축 중...")
                max_docs = colbert_config.get('max_documents', None)  # None이면 전체 문서
                force_rebuild = False  # 기본적으로 캐시 활용
                
                if not colbert_engine.build_index(
                    self.documents, 
                    max_documents=max_docs,
                    force_rebuild=force_rebuild
                ):
                    logger.error("ColBERT 인덱스 구축 실패")
                    return self.semantic_search(query, top_k, threshold)
            
            # ColBERT 검색 수행
            colbert_results = colbert_engine.search(query, top_k, threshold)
            
            # SearchResult 형태로 변환
            search_results = colbert_engine.convert_to_search_results(colbert_results)
            
            logger.info(f"ColBERT 검색 완료: {len(search_results)}개 결과")
            return search_results
            
        except ImportError:
            logger.warning("ColBERT 모듈을 가져올 수 없습니다. 의미적 검색으로 대체합니다.")
            return self.semantic_search(query, top_k, threshold)
        except Exception as e:
            logger.error(f"ColBERT 검색 실패: {e}. 의미적 검색으로 대체합니다.")
            return self.semantic_search(query, top_k, threshold)
    
```

(삭제 후 바로 `def expanded_search(` 가 이어져야 한다.)

- [ ] **Step 6: `expanded_search`에 정규화 삽입 + colbert 분기 3곳 제거**

`expanded_search` 메서드의 docstring 바로 다음, `try:` 블록 시작 앞에 삽입:

```python
        search_method = normalize_search_method(search_method)

```

docstring의 `search_method: 검색 방법 ("semantic", "keyword", "hybrid", "colbert")` 를 `search_method: 검색 방법 ("semantic", "keyword", "hybrid")` 로 수정.

아래 세 곳의 분기를 각각 삭제:

```python
                    elif search_method == "colbert":
                        results = self.colbert_search(search_query, top_k * 2, threshold, **search_kwargs)
```

```python
            elif search_method == "colbert":
                return self.colbert_search(query, top_k, threshold, **search_kwargs)
```

(이 패턴이 `except ImportError:` 블록과 `except Exception as e:` 블록에 각각 한 번씩, 총 2회 등장 — 둘 다 삭제)

- [ ] **Step 7: `search_with_related`에 정규화 삽입 + colbert 분기 제거**

`search_with_related` 메서드의 docstring 바로 다음, `try:` 앞에 삽입:

```python
        search_method = normalize_search_method(search_method)

```

다음 분기 삭제:

```python
            elif search_method == "colbert":
                main_results = self.colbert_search(query, top_k, **search_kwargs)
```

- [ ] **Step 8: `search_with_centrality_boost`에 정규화 삽입 + colbert 분기 2곳 제거**

`search_with_centrality_boost` 메서드에서 `threshold = search_kwargs.pop('threshold', 0.0)` 다음 줄에 삽입:

```python
        search_method = normalize_search_method(search_method)
```

docstring의 `search_method: 검색 방법 ("semantic", "keyword", "hybrid", "colbert")` 를 `search_method: 검색 방법 ("semantic", "keyword", "hybrid")` 로, `# threshold는 semantic/colbert만 지원` 를 `# threshold는 semantic만 지원` 으로 수정.

다음 두 분기를 각각 삭제:

```python
            elif search_method == "colbert":
                results = self.colbert_search(query, top_k * 2, threshold=threshold, **search_kwargs)
```

```python
            elif search_method == "colbert":
                return self.colbert_search(query, top_k, threshold=threshold, **search_kwargs)
```

- [ ] **Step 9: 테스트 재실행하여 통과 확인**

Run: `/Users/msbaek/.local/pipx/venvs/vault-intelligence/bin/python -m pytest tests/test_advanced_search_colbert_fallback.py -v`
Expected: PASS (3 passed)

- [ ] **Step 10: `grep`으로 잔존 colbert 참조 확인**

Run: `grep -n "colbert" src/features/advanced_search.py`
Expected: 0 matches (전부 제거됨. `colbert_config`, `colbert_engine` 등 로컬 변수까지 모두 삭제된 상태여야 함)

- [ ] **Step 11: Commit**

```bash
git add src/features/advanced_search.py tests/test_advanced_search_colbert_fallback.py
git commit -m "$(cat <<'EOF'
refactor(search): AdvancedSearchEngine에서 ColBERT 디스패치 제거

전체 검색 요청의 0.04%만 쓰였지만 재인덱싱마다 캐시 전량(32GB)을
메모리에 적재해 OOM을 유발했다(2026-08-13). search_method=colbert는
에러 대신 hybrid로 폴백해 호출부를 깨뜨리지 않는다.

Spec: docs/superpowers/specs/2026-08-13-colbert-removal-design.md
EOF
)"
```

---

### Task 2: HTTP 레이어(server.py) + reranker.py 정리

**Files:**
- Modify: `src/server.py`
- Modify: `src/client.py`
- Modify: `src/features/reranker.py`
- Modify: `tests/test_server.py`

**Interfaces:**
- Consumes: `normalize_search_method` from Task 1 (`src.features.advanced_search`)

- [ ] **Step 1: `reranker.py`의 colbert 분기 제거**

`src/features/reranker.py`의 `search_and_rerank` 메서드에서:

```python
        elif search_method == "colbert":
            initial_results = self.search_engine.colbert_search(
                query, top_k=initial_k, threshold=similarity_threshold, **search_kwargs
            )
```

삭제. docstring의 `search_method: 검색 방법 ("semantic", "keyword", "hybrid")` — 이미 colbert가 빠져 있으므로 수정 불필요, 확인만 한다.

- [ ] **Step 2: `server.py`의 `/search` 엔드포인트 수정**

`src/server.py` 상단 import 줄:

```python
from .features.advanced_search import AdvancedSearchEngine, SearchResult
```

를

```python
from .features.advanced_search import AdvancedSearchEngine, SearchResult, normalize_search_method
```

로 변경.

`/search` 엔드포인트(`async def search(`) 안의 `try:` 블록 시작 직후에 삽입:

```python
        try:
            search_method = normalize_search_method(search_method)

```

(기존 `try:` 다음 줄이 `# Execute search based on method and rerank option` 주석이었다면 그 앞에 넣는다.)

같은 함수 안의 direct-search 분기에서:

```python
                elif search_method == "colbert":
                    results = engine.colbert_search(query, top_k=top_k, threshold=threshold)
```

삭제.

`Query(...)` 파라미터 설명에서 `description="Search method: semantic, keyword, hybrid, colbert"` 를 `description="Search method: semantic, keyword, hybrid"` 로 수정.

- [ ] **Step 3: `client.py` docstring 수정**

`src/client.py:122` 의 `search_method: Search method (semantic, keyword, hybrid, colbert)` 를 `search_method: Search method (semantic, keyword, hybrid)` 로 수정.

- [ ] **Step 4: `tests/test_server.py`의 죽은 mock 제거**

```python
    engine.colbert_search = Mock(side_effect=make_search_results)
```

삭제 (167번째 줄, `engine.search_with_reranking = Mock(...)` 바로 앞).

- [ ] **Step 5: colbert 폴백 테스트 추가**

`tests/test_server.py`의 `test_search_with_different_methods` 함수 바로 다음에 추가:

```python
def test_search_with_colbert_falls_back_to_hybrid(client):
    """ColBERT was removed (2026-08-13) — should warn and return hybrid results, not error."""
    response = client.get("/search", params={
        "query": "test",
        "search_method": "colbert",
        "top_k": 3
    })

    assert response.status_code == 200
    data = response.json()
    assert data["search_method"] == "hybrid"
```

- [ ] **Step 6: pytest 설치 확인 후 전체 서버 테스트 실행**

Run: `/Users/msbaek/.local/pipx/venvs/vault-intelligence/bin/python -m pytest tests/test_server.py -v`
Expected: 모든 테스트 PASS, 특히 `test_search_with_colbert_falls_back_to_hybrid` PASS

- [ ] **Step 7: 잔존 참조 확인**

Run: `grep -rn "colbert" src/server.py src/client.py src/features/reranker.py`
Expected: 0 matches

- [ ] **Step 8: Commit**

```bash
git add src/server.py src/client.py src/features/reranker.py tests/test_server.py
git commit -m "$(cat <<'EOF'
refactor(server): HTTP 검색 엔드포인트에서 ColBERT 제거, hybrid 폴백 테스트 추가

/search?search_method=colbert 는 이제 에러가 아니라 경고 로그 후
hybrid 결과를 반환한다. 외부 스킬 문서가 아직 colbert를 호출할 수
있어 조용한 성공보다 명시적 폴백을 택했다.

Spec: docs/superpowers/specs/2026-08-13-colbert-removal-design.md
EOF
)"
```

---

### Task 3: CLI 레이어(`__main__.py`) 정리

**Files:**
- Modify: `src/__main__.py`

**Interfaces:**
- Consumes: `normalize_search_method` from Task 1 (`src.features.advanced_search`)

- [ ] **Step 1: import에 `normalize_search_method` 추가**

`_load_deps()` 함수 내부(현재 54번째 줄 부근):

```python
        from src.features.advanced_search import AdvancedSearchEngine, SearchQuery
```

를

```python
        from src.features.advanced_search import AdvancedSearchEngine, SearchQuery, normalize_search_method
```

로 변경. 그리고 `_load_deps()` 상단의 `global` 선언 목록(41번째 줄 부근)에 `normalize_search_method`를 추가:

```python
    global AdvancedSearchEngine, SearchQuery, DuplicateDetector
```

를

```python
    global AdvancedSearchEngine, SearchQuery, DuplicateDetector, normalize_search_method
```

로 변경.

- [ ] **Step 2: `run_search()`의 direct-dispatch 분기 수정**

`run_search()` 함수 시작부(`try:` 블록 진입 직후)에 삽입:

```python
        search_method = normalize_search_method(search_method)
```

(`print(f"🔍 검색 시작: '{query}'")` 바로 다음 줄)

다음 분기를 삭제:

```python
            elif search_method == "colbert":
                results = search_engine.colbert_search(query, top_k=top_k, threshold=threshold)
```

- [ ] **Step 3: `run_reindex()`에서 ColBERT 블록 제거**

함수 시그니처를:

```python
def run_reindex(vault_path: str, force: bool, config: dict, sample_size: Optional[int] = None,
                include_folders: Optional[list] = None, exclude_folders: Optional[list] = None,
                with_colbert: bool = False, colbert_only: bool = False):
```

에서

```python
def run_reindex(vault_path: str, force: bool, config: dict, sample_size: Optional[int] = None,
                include_folders: Optional[list] = None, exclude_folders: Optional[list] = None):
```

로 변경.

함수 본문에서 `with_colbert`/`colbert_only` 를 참조하는 아래 블록을 모두 삭제:

- `if with_colbert: print("🎯 ColBERT 인덱싱 포함")` / `if colbert_only: print(...)` (두 줄)
- `if not colbert_only:` 로 시작하는 dense 빌드 블록의 조건문은 유지하되, 조건을 단순화: `if not colbert_only:` → 조건 제거하고 항상 실행 (해당 블록의 들여쓰기를 한 단계 왼쪽으로 옮긴다)
- `# ColBERT 인덱싱` 주석부터 `except Exception as e: print(f"⚠️ ColBERT 인덱싱 중 오류: {e}")` 까지의 `if with_colbert or colbert_only:` 블록 전체
- 함수 끝부분의 `if not colbert_only:` 통계 출력 블록도 조건 제거하고 항상 실행되도록 들여쓰기 조정
- `if with_colbert or colbert_only:` 로 시작하는 ColBERT 캐시 통계 블록 전체 삭제

결과적으로 `run_reindex`는 dense 임베딩 인덱스만 구축하고 통계를 출력하는 함수가 된다.

- [ ] **Step 4: argparse에서 `--with-colbert`/`--colbert-only`/`colbert` choice 처리**

`reindex` 서브파서(2138번째 줄 부근)에서 아래 두 줄 삭제:

```python
    p.add_argument("--with-colbert", action="store_true", help="ColBERT 인덱싱 포함")
    p.add_argument("--colbert-only", action="store_true", help="ColBERT만 재인덱싱 (Dense 제외)")
```

`search` 서브파서(2063번째 줄 부근)의 help 문구를:

```python
    p = subparsers.add_parser("search", help="하이브리드 검색 (semantic, keyword, colbert)")
```

에서

```python
    p = subparsers.add_parser("search", help="하이브리드 검색 (semantic, keyword, hybrid)")
```

로 수정.

`--search-method`의 `choices`는 **`"colbert"`를 남겨둔다** (CLI 파싱 단계에서 즉시 거부하지 않고 `run_search` 내부의 `normalize_search_method`가 경고+폴백하도록 하기 위함 — spec §4.1 폴백 정책). 다만 help 문구는 수정:

```python
    p.add_argument("--search-method", choices=["semantic", "keyword", "hybrid", "colbert"], default="hybrid", help="검색 방법 (기본값: hybrid)")
```

를

```python
    p.add_argument("--search-method", choices=["semantic", "keyword", "hybrid", "colbert"], default="hybrid", help="검색 방법 (기본값: hybrid). colbert는 2026-08-13 제거되어 hybrid로 자동 대체됩니다.")
```

- [ ] **Step 5: `main()`의 `run_reindex` 호출부 수정**

```python
        if run_reindex(vault_path, args.force, config,
                      args.sample_size,
                      args.include_folders,
                      args.exclude_folders,
                      args.with_colbert,
                      args.colbert_only):
```

를

```python
        if run_reindex(vault_path, args.force, config,
                      args.sample_size,
                      args.include_folders,
                      args.exclude_folders):
```

로 변경.

- [ ] **Step 6: `show_system_info()`에서 ColBERT 통계·안내 제거**

```python
        colbert_stats = cache.get_colbert_statistics()
        print(f"- ColBERT 임베딩: {colbert_stats.get('total_colbert_embeddings', 0):,}개")
```

삭제(두 줄).

```python
    print("🎯 완료된 기능 (Phase 1-7):")
    print("- BGE-M3 기반 Dense + Sparse + ColBERT 검색")
```

에서 `"- BGE-M3 기반 Dense + Sparse + ColBERT 검색"` 를 `"- BGE-M3 기반 Dense + Sparse 검색"` 로 수정.

```python
    print("- ColBERT 증분 캐싱 시스템 (신규!)")
    print()
    print("⚡ ColBERT 검색 명령어:")
    print("  vis reindex --with-colbert     # ColBERT 포함 인덱싱")
    print("  vis reindex --colbert-only     # ColBERT만 인덱싱")
    print("  vis search --query 'TDD' --search-method colbert")
    print()
```

이 블록 전체(`- ColBERT 증분 캐싱 시스템` 줄부터 `⚡ 기본 명령어:` 바로 앞까지) 삭제.

- [ ] **Step 7: 문법 검증**

Run: `/Users/msbaek/.local/pipx/venvs/vault-intelligence/bin/python -c "import ast; ast.parse(open('src/__main__.py').read())"`
Expected: 에러 없이 종료

- [ ] **Step 8: 실제 CLI로 수동 검증 (pytest 커버리지 없는 경로)**

Run: `/Users/msbaek/.local/pipx/venvs/vault-intelligence/bin/python -m src search "TDD" --search-method colbert --top-k 3 2>&1 | head -20`
Expected: stderr/stdout에 `search_method='colbert'는 제거되었습니다` 경고가 보이고, 검색 결과가 정상 출력됨(에러로 종료하지 않음)

Run: `/Users/msbaek/.local/pipx/venvs/vault-intelligence/bin/python -m src reindex --help 2>&1 | grep -i colbert`
Expected: 출력 없음 (0 matches — `--with-colbert`/`--colbert-only` 플래그가 더 이상 존재하지 않음)

- [ ] **Step 9: 잔존 참조 확인**

Run: `grep -n "colbert" src/__main__.py`
Expected: `--search-method colbert` choices 목록과 관련 help 문구 1곳만 남고(의도적 유지), `with_colbert`/`colbert_only`/`colbert_engine`/`colbert_stats` 등은 0 matches

- [ ] **Step 10: Commit**

```bash
git add src/__main__.py
git commit -m "$(cat <<'EOF'
refactor(cli): --with-colbert/--colbert-only 제거, search-method colbert는 hybrid로 자동 대체

reindex가 더 이상 ColBERT 인덱스를 만들지 않는다 — 이게 OOM의 직접
원인이었다(캐시 32GB 전량 메모리 적재, 2026-08-13). --search-method
colbert choice는 하위호환을 위해 남기되 normalize_search_method가
경고 후 hybrid로 처리한다.

Spec: docs/superpowers/specs/2026-08-13-colbert-removal-design.md
EOF
)"
```

---

### Task 4: ColBERT 구현체·캐시 계층·설정 삭제

**Files:**
- Delete: `src/features/colbert_search.py`
- Delete: `test_colbert.py`
- Modify: `src/core/embedding_cache.py`
- Modify: `config/settings.yaml`

- [ ] **Step 1: `colbert_search.py` 삭제**

Run: `git rm src/features/colbert_search.py`

- [ ] **Step 2: `test_colbert.py` 삭제**

Run: `git rm test_colbert.py`

- [ ] **Step 3: `embedding_cache.py`에서 ColBERT 테이블 생성 제거**

`_init_database()` 메서드에서 다음 블록 삭제:

```python
                # ColBERT 임베딩 테이블 생성
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS colbert_embeddings (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        file_path TEXT NOT NULL UNIQUE,
                        file_hash TEXT NOT NULL,
                        colbert_embedding BLOB NOT NULL,
                        token_embeddings BLOB,
                        model_name TEXT NOT NULL,
                        created_at TIMESTAMP NOT NULL,
                        file_size INTEGER NOT NULL,
                        num_tokens INTEGER,
                        embedding_dimension INTEGER NOT NULL
                    )
                """)
                
                # ColBERT 인덱스 생성
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_colbert_file_path ON colbert_embeddings(file_path)
                """)
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_colbert_file_hash ON colbert_embeddings(file_hash)
                """)
                
```

그리고 바로 아래 로그 문구:

```python
                logger.info("데이터베이스 초기화 완료 (ColBERT 테이블 포함)")
```

를

```python
                logger.info("데이터베이스 초기화 완료")
```

로 수정.

- [ ] **Step 4: `_deserialize_colbert_embedding` 삭제**

```python
    def _deserialize_colbert_embedding(self, data: bytes, num_tokens: int, embedding_dim: int) -> np.ndarray:
        """ColBERT 임베딩 전용 역직렬화 (2차원 복원)"""
        try:
            # 바이트 데이터를 float32 배열로 변환
            flat_array = np.frombuffer(data, dtype=np.float32)
            
            # 예상 크기 검증
            expected_size = num_tokens * embedding_dim
            if len(flat_array) != expected_size:
                logger.warning(f"ColBERT 배열 크기 불일치: {len(flat_array)} != {expected_size}")
                return np.zeros((num_tokens, embedding_dim), dtype=np.float32)
            
            # 2차원으로 reshape
            return flat_array.reshape(num_tokens, embedding_dim)
            
        except Exception as e:
            logger.error(f"ColBERT 임베딩 역직렬화 실패: {e}")
```

전체 삭제 (다음 메서드 정의 바로 앞까지 — 예외 처리부 마지막 줄까지 포함해서 삭제).

- [ ] **Step 5: `# ===== ColBERT 임베딩 관련 메서드 =====` 섹션 전체 삭제**

`src/core/embedding_cache.py`에서 다음 주석부터:

```python
    # ===== ColBERT 임베딩 관련 메서드 =====
    
    def store_colbert_embedding(
```

`get_colbert_statistics` 메서드가 끝나는 지점(`def test_cache():` 함수 정의 바로 앞)까지 — 즉 `store_colbert_embedding`, `get_colbert_embedding`, `has_colbert_embedding`, `remove_colbert_embedding`, `clear_colbert_cache`, `get_colbert_statistics` 6개 메서드를 통째로 삭제한다. 삭제 후 클래스는 `export_cache_info` 다음 바로 `def test_cache():` (모듈 레벨 함수)로 이어져야 한다.

- [ ] **Step 6: 문법 검증**

Run: `/Users/msbaek/.local/pipx/venvs/vault-intelligence/bin/python -c "import ast; ast.parse(open('src/core/embedding_cache.py').read())"`
Expected: 에러 없이 종료

- [ ] **Step 7: `config/settings.yaml`에서 `colbert:` 섹션 삭제**

```yaml
# ColBERT 설정 (Phase 5.2 + 증분 인덱싱)
colbert:
  model_name: "BAAI/bge-m3" # BGE-M3 ColBERT 기능 사용
  use_fp16: true
  cache_folder: "models/"
  device: "mps" # M1 Pro Metal Performance Shaders 가속
  max_length: 4096
  batch_size: 2 # 낮은 부하로 조정
  max_documents: null # 전체 문서 대상 (제한 없음)
  enable_cache: true # ColBERT 캐싱 활성화
  incremental_indexing: true # 증분 인덱싱 활성화
  auto_index_on_reindex: true # reindex 시 자동 ColBERT 인덱싱

```

전체 삭제.

- [ ] **Step 8: `enable_colbert: true` 삭제**

`config/settings.yaml`의 `caching:` 섹션에서 (Task는 이 줄이 속한 섹션 헤더 유지, 이 줄만 삭제):

```yaml
  enable_colbert: true
```

삭제.

- [ ] **Step 9: 잔존 참조 확인**

Run: `grep -rn "colbert" src/ config/ | grep -v "search_method.*colbert\|choices=\[.*colbert\|정규화\|normalize_search_method\|hybrid로 자동 대체\|hybrid로 대체"`
Expected: 0 matches (Task 1-3에서 의도적으로 남긴 정규화/폴백 관련 문자열만 제외하고 전부 제거됨)

- [ ] **Step 10: Commit**

```bash
git add -A src/features/colbert_search.py test_colbert.py src/core/embedding_cache.py config/settings.yaml
git commit -m "$(cat <<'EOF'
refactor(cache): ColBERTSearchEngine·캐시 테이블·설정 삭제

컴포넌트를 통째로 제거한다: colbert_search.py(ColBERTSearchEngine),
embedding_cache.py의 colbert_embeddings 테이블/CRUD/통계 메서드,
settings.yaml의 colbert 설정 섹션. 디스패치 레이어(Task 1-3)가
이미 hybrid로 폴백하도록 정리되어 이 구현체는 더 이상 호출되지 않는다.

Spec: docs/superpowers/specs/2026-08-13-colbert-removal-design.md
EOF
)"
```

---

### Task 5: 캐시 DB에서 ColBERT 데이터 회수 (운영 작업)

**Files:**
- Modify (in place): `cache/embeddings.db`

이 태스크는 코드가 아니라 로컬 데이터 마이그레이션이다. 커밋 대상이 아니다(`cache/`는 gitignore됨 — Step 1에서 확인).

- [ ] **Step 1: `cache/`가 git 추적 대상이 아님을 확인**

Run: `git check-ignore -v cache/embeddings.db || echo "NOT IGNORED — 확인 필요"`
Expected: `.gitignore` 규칙이 매치되어 출력됨 (추적되지 않음을 확인)

- [ ] **Step 2: 마이그레이션 전 상태 기록**

Run: `ls -la cache/embeddings.db && sqlite3 cache/embeddings.db "SELECT COUNT(*) FROM embeddings; SELECT COUNT(*) FROM colbert_embeddings;"`
Expected: 파일 크기 약 34GB, dense 4,438건 내외, colbert 4,415건 내외 (실행 시점에 따라 약간 다를 수 있음 — 기록만 해두고 다음 단계로)

- [ ] **Step 3: dense 전용 신규 DB 생성**

Run:
```bash
sqlite3 cache/embeddings_dense_only.db <<'EOF'
ATTACH DATABASE 'cache/embeddings.db' AS old;
CREATE TABLE embeddings AS SELECT * FROM old.embeddings;
CREATE INDEX idx_file_path ON embeddings(file_path);
CREATE INDEX idx_file_hash ON embeddings(file_hash);
CREATE INDEX idx_model_name ON embeddings(model_name);
DETACH DATABASE old;
EOF
```

- [ ] **Step 4: 신규 DB 무결성 확인**

Run: `sqlite3 cache/embeddings_dense_only.db "SELECT COUNT(*) FROM embeddings;" && sqlite3 cache/embeddings.db "SELECT COUNT(*) FROM embeddings;"`
Expected: 두 값이 정확히 일치 (dense 임베딩 손실 없음)

Run: `sqlite3 cache/embeddings_dense_only.db "PRAGMA integrity_check;"`
Expected: `ok`

- [ ] **Step 5: 원본을 신규 DB로 교체 (백업 없음 — spec §4.2 결정)**

Run:
```bash
rm cache/embeddings.db
mv cache/embeddings_dense_only.db cache/embeddings.db
```

- [ ] **Step 6: 회수 결과 확인**

Run: `ls -la cache/embeddings.db`
Expected: 파일 크기가 100MB 미만 (spec §5 AC4)

- [ ] **Step 7: 디스크 여유 공간 확인**

Run: `df -h /Users/msbaek | tail -1`
Expected: 마이그레이션 전 대비 여유 공간이 약 32GB 증가

---

### Task 6: 운영 스크립트에서 `--with-colbert` 제거 + launchd 재활성화

**Files:**
- Modify: `scripts/vis-nightly-reindex.sh`
- Modify: `reindex.sh`

**Interfaces:**
- Consumes: Task 3에서 정리된 `vis reindex`(더 이상 `--with-colbert`/`--colbert-only` 플래그를 받지 않음)

- [ ] **Step 1: `scripts/vis-nightly-reindex.sh`의 헤더 주석 수정**

```bash
# 동작:
#   - 평일: `vis reindex --with-colbert`      (증분, 캐시 기반)
#   - 일요일: `vis reindex --force --with-colbert` (전체 재구축)
```

를

```bash
# 동작:
#   - 평일: `vis reindex`      (증분, 캐시 기반)
#   - 일요일: `vis reindex --force` (전체 재구축)
```

로 수정.

- [ ] **Step 2: reindex 실행부에서 `--with-colbert` 제거**

```bash
if [[ "$DRYRUN" == "1" ]]; then
  echo "[$(ts)] (dry-run) vis reindex $FORCE_FLAG --with-colbert 생략" | tee -a "$RUN_LOG"
else
  echo "[$(ts)] vis reindex $FORCE_FLAG --with-colbert 실행..." >> "$RUN_LOG"
  "$VIS" reindex $FORCE_FLAG --with-colbert >> "$RUN_LOG" 2>&1
  rc=$?
  echo "[$(ts)] reindex 종료코드: $rc" >> "$RUN_LOG"
fi
```

를

```bash
if [[ "$DRYRUN" == "1" ]]; then
  echo "[$(ts)] (dry-run) vis reindex $FORCE_FLAG 생략" | tee -a "$RUN_LOG"
else
  echo "[$(ts)] vis reindex $FORCE_FLAG 실행..." >> "$RUN_LOG"
  "$VIS" reindex $FORCE_FLAG >> "$RUN_LOG" 2>&1
  rc=$?
  echo "[$(ts)] reindex 종료코드: $rc" >> "$RUN_LOG"
fi
```

로 수정.

- [ ] **Step 3: ColBERT 저장 경합 카운터 제거**

```bash
# 이번 실행 로그에서 ColBERT 저장 경합(파일 이동/삭제) 건수 집계
colbert_err=$(grep -c "ColBERT 임베딩 저장 실패" "$RUN_LOG" 2>/dev/null || true)
colbert_err=${colbert_err:-0}

```

전체 삭제.

`summary=$(cat <<EOF ... EOF)` 블록 안의:

```
ColBERT 저장실패(경합): ${colbert_err}건
```

줄 삭제.

```bash
msg="모드=$mode_ko · 문서=$docs · ${DUR}s · 데몬=$restart_ok"
[[ "$colbert_err" != "0" ]] && msg="$msg · ColBERT경합 ${colbert_err}건"
```

를

```bash
msg="모드=$mode_ko · 문서=$docs · ${DUR}s · 데몬=$restart_ok"
```

로 수정.

- [ ] **Step 4: `reindex.sh`(폴더별 재인덱싱 스크립트)에서 `--with-colbert` 제거**

```bash
    vis reindex --force --with-colbert --include-folders "$folder"
```

를

```bash
    vis reindex --force --include-folders "$folder"
```

로 수정.

- [ ] **Step 5: bash 문법 검증**

Run: `bash -n scripts/vis-nightly-reindex.sh && bash -n reindex.sh`
Expected: 에러 없이 종료

- [ ] **Step 6: dry-run으로 스크립트 로직 검증**

Run: `VIS_REINDEX_MODE=incremental scripts/vis-nightly-reindex.sh --dry-run`
Expected: 로그에 `(dry-run) vis reindex  생략` 형태로 출력되고(더 이상 `--with-colbert` 문자열 없음), 알림 요약에 `ColBERT 저장실패` 항목이 없음

- [ ] **Step 7: 잔존 참조 확인**

Run: `grep -n "colbert" scripts/vis-nightly-reindex.sh reindex.sh`
Expected: 0 matches

- [ ] **Step 8: launchd 작업 재활성화 (오늘 아침 unload한 것을 복구)**

Run: `launchctl load ~/Library/LaunchAgents/com.msbaek.vis-reindex.plist && launchctl list | grep vis-reindex`
Expected: `com.msbaek.vis-reindex`가 목록에 나타남

- [ ] **Step 9: 실제 launchd 경로로 실행 검증 (2026-07-08 cwd 버그 재발 방지 — spec §5 AC5)**

Run: `VIS_REINDEX_MODE=incremental launchctl start com.msbaek.vis-reindex`

30초 대기 후:

Run: `tail -30 ~/.claude/logs/vis-reindex/launchd.err.log`
Expected: `[Errno 30] Read-only file system` 등 cwd 관련 에러 없음. 정상적으로 reindex가 시작되었다는 로그 확인.

이 실행은 dense 전용이라 약 90분 내 완료된다 — 완료까지 기다리지 않고 다음 태스크로 진행해도 되지만, 시작 직후 에러가 없는지는 반드시 확인한다.

- [ ] **Step 10: Commit**

```bash
git add scripts/vis-nightly-reindex.sh reindex.sh
git commit -m "$(cat <<'EOF'
fix(vis-reindex): 야간 재인덱싱에서 --with-colbert 제거

야간 job이 매일 ColBERT 인덱스(당시 32GB)를 전량 메모리에 재적재해
12시간 45분 실행 끝에 시스템 스왑을 76.7GB까지 채웠다(2026-08-13).
dense 전용으로 바뀌며 예상 소요가 12시간 -> 약 90분으로 줄어든다.

Spec: docs/superpowers/specs/2026-08-13-colbert-removal-design.md
EOF
)"
```

---

### Task 7: vault-intelligence 문서 정리

**Files:**
- Modify: `CLAUDE.md`
- Modify: `README.md`
- Modify: `docs/QUICK_START.md`
- Modify: `docs/EXAMPLES.md`
- Modify: `docs/search-method-comparison.md`
- Modify: `docs/TROUBLESHOOTING.md`
- Modify: `docs/USER_GUIDE.md`

**범위 밖 (수정하지 않음):** `archive/`, `private/`, `CONTRIBUTING.md`(과거 커밋 예시), `CHANGELOG.md`(과거 릴리스 기록), `docs/superpowers/plans/2026-04-25-*`(과거 계획 문서) — spec §5 AC6.

- [ ] **Step 1: `CLAUDE.md` 수정**

`vis search "TDD" --search-method colbert    # ColBERT 토큰 검색` 줄 삭제.

`vis reindex --with-colbert     # ColBERT 포함` 줄 삭제.

`| \`colbert\` | 긴 문장, 복합 개념 | ⚡⚡ | ⭐⭐⭐⭐ |` 표 행 삭제.

`│   ├── colbert_search.py               # ColBERT 토큰 검색` 줄 삭제 (디렉토리 구조 트리).

`results = engine.colbert_search("query", top_k=10)` 를 포함한 예시 라인 삭제(주변 맥락 확인 후 예시 블록 정리).

`search_method="hybrid",  # semantic, keyword, colbert, hybrid` 를 `search_method="hybrid",  # semantic, keyword, hybrid` 로 수정.

`- **ColBERT 경고 메시지**: 캐시 초기화 후 재인덱싱 (\`rm -rf cache/ && vis reindex --with-colbert\`)` 줄 삭제.

`- **ColBERT 재순위화 오류**: 2025-08-27 수정 완료, 모든 검색 방법에서 --rerank 옵션 지원` 줄 삭제.

`- **Phase 5**: 고급 검색 (Reranking, ColBERT, 쿼리 확장)` 를 `- **Phase 5**: 고급 검색 (Reranking, 쿼리 확장)` 로 수정.

`- **긴급 수정 (2025-08-27)**: ColBERT 메타데이터 무결성 완전 해결 🔧` 줄은 **과거 이력이므로 유지** (완료된 수정 기록).

- [ ] **Step 2: `README.md` 수정**

`Obsidian vault를 위한 로컬 시맨틱 검색 엔진. BGE-M3 임베딩 기반으로 Dense, Sparse, ColBERT, Cross-encoder Reranking을 결합한 다층 하이브리드 검색을 제공합니다. 한국어 최적화 포함.` 를 `Obsidian vault를 위한 로컬 시맨틱 검색 엔진. BGE-M3 임베딩 기반으로 Dense, Sparse, Cross-encoder Reranking을 결합한 다층 하이브리드 검색을 제공합니다. 한국어 최적화 포함.` 로 수정.

`vis search "TDD" --search-method colbert      # ColBERT 토큰 검색` 줄 삭제.

`vis reindex --with-colbert     # ColBERT 포함` 줄 삭제.

- [ ] **Step 3: `docs/QUICK_START.md` 수정**

```
# ColBERT 토큰 검색
vis search "TDD" --search-method colbert
```

이 두 줄 삭제 (바로 위 `# 쿼리 확장 (최대 포괄성)` 블록과 바로 아래 `### 유사도 임계값 조정` 사이).

- [ ] **Step 4: `docs/EXAMPLES.md` 수정**

`### 예제 4: ColBERT 정밀 검색` 부터 `**사용 팁:** ColBERT는 단일 키워드보다 긴 문장에서 성능이 우수합니다.` 까지 섹션 전체 삭제. 이후 `### 예제 5: 재순위화로 정확도 향상`을 `### 예제 4: 재순위화로 정확도 향상`으로 번호 조정.

`### 예제 6: 검색 방법별 비교 테스트` 블록 안의:
```
vis search "$query" --search-method colbert    # ColBERT
```
줄 삭제. 이 섹션 번호를 `### 예제 5`로 조정.

`### 예제 7: 단일 키워드 최적 검색법`을 `### 예제 6`으로 조정. 블록 안의:
```
# ColBERT용으로 쿼리 확장
vis search "YAGNI You Aren't Going to Need It agile principle" --search-method colbert
```
두 줄 삭제. 주석 `# 단일 약어/키워드는 ColBERT보다 하이브리드가 효과적`를 `# 단일 약어/키워드는 하이브리드가 효과적`으로 수정.

`### 예제 8: 정확도 조절`을 `### 예제 7`로 조정.

이후 파일에 존재하는 (번호가 중복된 별도 섹션) `### 🆕 예제 6: ColBERT 토큰 수준 검색 (신규!)` 부터 그 안의 `ColBERT vs 다른 검색 방법 비교` 하위 블록, 그리고 바로 이어지는 `### 예제 7: 초기 ColBERT 인덱싱` 섹션까지 — `---` 구분선과 `## 🔎 중복 감지 예제` 헤딩 바로 앞까지 전체 삭제.

편집 후 파일 전체에서 예제 번호가 순서대로 이어지는지 확인하고, 끊긴 부분이 있으면 자연스럽게 재번호.

- [ ] **Step 5: `docs/search-method-comparison.md` 수정**

`Vault Intelligence는 4가지 검색 방법을 제공합니다.` 를 `Vault Intelligence는 3가지 검색 방법을 제공합니다.` 로 수정.

목차에서 `- [ColBERT 검색](#colbert-검색)` 줄 삭제.

mermaid 다이어그램:
```
    Q1 -->|"No"| Q2{"여러 개념을 나열한\n체크리스트형 쿼리인가?"}
    Q2 -->|"Yes"| ColBERT["ColBERT 검색"]
    Q2 -->|"No"| Q3{"최고 정확도가\n필요한가?"}
```
를
```
    Q1 -->|"No"| Q3{"최고 정확도가\n필요한가?"}
```
로 단순화 (Q2 분기 제거, Q1의 No가 바로 Q3로 연결).

비교 요약 표에서 ColBERT 열 전체 삭제:
```
| | Keyword | Semantic | Hybrid | ColBERT |
|---|---|---|---|---|
| **비유** | 사전에서 단어 찾기 | 사서에게 주제 설명하기 | 사서 + 사전 동시 활용 | 사서에게 체크리스트 주기 |
| **원리** | 정확한 단어 매칭 (BM25) | 의미 벡터 유사도 (Dense) | Keyword + Semantic 결합 | 토큰별 독립 매칭 |
| **최적 쿼리** | 1-3단어 | 10-15단어 | 5-15단어 | 15-25단어 |
| **속도** | 빠름 | 빠름 | 빠름 | 보통 |
| **정확도** | 중간 | 높음 | 높음 | 높음 |
| **추천 상황** | 고유명사, 파일명 | 개념적 검색 | 일반적 모든 검색 | 복합 개념 검색 |
```
를
```
| | Keyword | Semantic | Hybrid |
|---|---|---|---|
| **비유** | 사전에서 단어 찾기 | 사서에게 주제 설명하기 | 사서 + 사전 동시 활용 |
| **원리** | 정확한 단어 매칭 (BM25) | 의미 벡터 유사도 (Dense) | Keyword + Semantic 결합 |
| **최적 쿼리** | 1-3단어 | 10-15단어 | 5-15단어 |
| **속도** | 빠름 | 빠름 | 빠름 |
| **정확도** | 중간 | 높음 | 높음 |
| **추천 상황** | 고유명사, 파일명 | 개념적 검색 | 일반적 모든 검색 |
```
로 수정.

`## ColBERT 검색` 헤딩부터(원리·적합한 상황·CLI 사용법·강점과 한계·옵션별 효과 하위 섹션 포함) 바로 다음 `## 옵션 조합 가이드` 헤딩 앞까지 섹션 전체 삭제.

`--rerank` 궁합 표에서:
```
| ColBERT + Rerank | 효과적 | 복합 개념의 정밀 검색 |
```
행 삭제.

권장 조합 표에서:
```
| 복합 개념 | `vis search "개념1 개념2 개념3" --search-method colbert` | 체크리스트형 쿼리 |
```
행 삭제.

검색 방법별 최적 쿼리 길이 표에서:
```
| ColBERT | `Kent Beck TDD Red Green Refactor 리팩토링 설계 개선` (15-25단어) | 사서에게 체크리스트 주기 |
```
행 삭제.

- [ ] **Step 6: `docs/TROUBLESHOOTING.md` 수정**

`## ColBERT 관련 문제` 헤딩부터 (ColBERT 배열 크기 불일치 경고 / ColBERT + 재순위화 오류 / ColBERT 검색 결과 품질 문제 3개 하위 섹션 포함) 바로 다음 `## 서버 모드 (Daemon) 문제` 헤딩 앞까지 섹션 전체 삭제.

- [ ] **Step 7: `docs/USER_GUIDE.md` 수정**

`python -c "from src.features.colbert_search import test_colbert_search; test_colbert_search()"` — 이 줄이 파일에 2곳(52번째 줄 부근, 1703번째 줄 부근) 존재. 두 곳 모두 삭제.

```
# 4. ColBERT 토큰 수준 검색 (세밀한 매칭)
vis search "클린 코드" --search-method colbert
```
두 줄 삭제.

```
#### 5️⃣ **ColBERT 토큰 수준 검색** (`--search-method colbert`)
```bash
vis search "test driven development refactoring" --search-method colbert

# ColBERT 토큰 레벨 late interaction
# 긴 문장과 복합 개념에 최적화
# 정밀한 토큰 매칭, 2-4초 소요
```
```
섹션 전체 삭제. 이후 번호 매김(6️⃣, 7️⃣)은 그대로 두거나 자연스럽게 당겨도 무방 — 단, `#### 6️⃣ **재순위화 모드**` 블록 안의:
```
# ColBERT + 재순위화 (정밀 검색)
vis search "SOLID principles" --search-method colbert --rerank
```
두 줄은 삭제.

```
- **`colbert`**: ColBERT 토큰 수준 검색 (late interaction, 정밀 매칭)
```
줄 삭제.

```
| **ColBERT** | 긴 문장, 복합 개념 | 토큰 레벨 정밀 매칭 | 보통 🐌 |
```
표 행 삭제.

```
# 🆕 ColBERT 포함 통합 인덱싱 (권장!)
vis reindex --with-colbert

# ColBERT만 재인덱싱 (Dense 임베딩 제외)
vis reindex --colbert-only

# ColBERT 강제 재인덱싱
vis reindex --with-colbert --force

```
이 블록 전체 삭제 (뒤에 이어지는 `# 기본 재인덱싱 (Dense 임베딩만)` 줄부터는 유지).

```
### 🎯 ColBERT 증분 캐싱 시스템 (신규!)

#### 주요 장점
- **전체 문서 지원**: max_documents 제한 제거로 vault 전체에서 ColBERT 검색
- **영구 캐싱**: SQLite 기반으로 재계산 불필요 
- **증분 처리**: 변경된 문서만 자동 감지하여 재인덱싱
- **빠른 검색**: 캐시 활용으로 즉시 검색 결과 제공

#### 성능 비교
- **첫 인덱싱**: 1-2시간 (전체 vault, 1회만)
- **이후 검색**: 즉시 (캐시 활용)
- **증분 업데이트**: 변경된 파일만 처리

#### 캐시 상태 확인
```bash
vis info  # Dense + ColBERT 캐시 통계 포함
```

```
섹션 전체 삭제 (`vis info  # Dense + ColBERT 캐시 통계 포함`는 `vis info  # Dense 캐시 통계 포함`으로 대체하고 싶다면 남겨도 되지만, 이 태스크에서는 섹션째 삭제).

메모리 부족 에러 예시 블록에서:
```yaml
colbert:
  batch_size: 2
  max_documents: 10  # ColBERT 처리 문서 수 감소
```
삭제 (바로 위 `reranker:` 블록은 유지).

성능 최적화 권장 설정 3곳(소규모/중규모/대규모 vault)에서 각각:
```yaml
colbert:
  max_documents: 20
```
```yaml
colbert:
  max_documents: 20
```
```yaml
colbert:
  max_documents: 30
```
3곳 모두 삭제 (각 블록의 마지막 두 줄).

Phase 5 성능 비교 표에서:
```
| `colbert` | ⚡ | ⭐⭐⭐⭐ | 💾💾💾 | 토큰 수준 매칭 |
```
행 삭제.

```
- 다층 하이브리드 검색 (Dense + Sparse + ColBERT + Reranking)
```
를
```
- 다층 하이브리드 검색 (Dense + Sparse + Reranking)
```
로 수정.

```
- 🔍 **ColBERT Search**: 토큰 수준 late interaction 검색
```
줄 삭제 (이전 업데이트 V2.5 기록 — 과거 릴리스 히스토리이므로 삭제할지 고민될 수 있으나, USER_GUIDE.md는 현재 사용법 안내 문서이지 CHANGELOG가 아니므로 삭제한다).

- [ ] **Step 8: 잔존 참조 최종 확인 (전체 파일)**

Run: `grep -rln -i "colbert" CLAUDE.md README.md docs/QUICK_START.md docs/EXAMPLES.md docs/search-method-comparison.md docs/TROUBLESHOOTING.md docs/USER_GUIDE.md`
Expected: 출력 없음 (모든 파일에서 0 matches)

- [ ] **Step 9: markdown 링크·앵커 깨짐 확인**

Run: `grep -n "colbert-검색\|#colbert" docs/search-method-comparison.md`
Expected: 0 matches (TOC 앵커도 함께 제거되었는지 확인)

- [ ] **Step 10: Commit**

```bash
git add CLAUDE.md README.md docs/QUICK_START.md docs/EXAMPLES.md docs/search-method-comparison.md docs/TROUBLESHOOTING.md docs/USER_GUIDE.md
git commit -m "$(cat <<'EOF'
docs: ColBERT 검색 관련 안내 전면 삭제

기능 자체가 제거되었으므로(Task 1-6) 사용법 문서·예제·트러블슈팅·
비교 가이드에서도 ColBERT 참조를 걷어낸다. archive/·private/·
CHANGELOG.md·CONTRIBUTING.md의 과거 기록은 이력이므로 유지한다.

Spec: docs/superpowers/specs/2026-08-13-colbert-removal-design.md
EOF
)"
```

---

### Task 8: 최종 승인 조건 검증

**Files:** 없음 (검증 전용 태스크)

- [ ] **Step 1: AC1 — `--rerank` 정상 동작**

Run: `/Users/msbaek/.local/pipx/venvs/vault-intelligence/bin/python -m src search "TDD" --rerank --top-k 5 2>&1 | tail -30`
Expected: 5개 내외 결과가 정상 출력, 에러 없음

- [ ] **Step 2: AC2 — `--search-method colbert`가 에러 대신 경고+hybrid**

Run: `/Users/msbaek/.local/pipx/venvs/vault-intelligence/bin/python -m src search "TDD" --search-method colbert --top-k 3 2>&1`
Expected: `search_method='colbert'는 제거되었습니다` 경고 출력 + 검색 결과 정상 반환(exit code 0)

- [ ] **Step 3: AC3 — 데몬 phys_footprint가 기준선(8GB) 근처 유지**

Run: `visd restart && sleep 15`

검색 50회 반복 (다양한 쿼리·옵션):

```bash
for i in $(seq 1 50); do
  curl -s --get --data-urlencode "query=test query $i" "http://localhost:8741/search?rerank=true&top_k=10" > /dev/null
done
```

Run: `P=$(lsof -nP -iTCP:8741 -sTCP:LISTEN -t); footprint -p $P | tail -3`
Expected: `phys_footprint` 8 GB 미만

- [ ] **Step 4: AC4 — 캐시 DB 크기**

Run: `ls -la cache/embeddings.db`
Expected: 100 MB 미만 (Task 5에서 이미 확인했지만 최종 재확인)

- [ ] **Step 5: AC5 — launchd 실제 경로 실행**

Task 6 Step 9에서 이미 검증됨. 이번 단계에서는 백그라운드로 시작된 reindex가 완료되었는지 확인:

Run: `cat ~/.claude/logs/vis-reindex/latest.txt`
Expected: `[✅ 성공]` 상태, `reindex exit: 0`, ColBERT 관련 항목 없음. 아직 실행 중이면(약 90분 소요) 완료를 기다리지 않고 다음 단계로 진행해도 무방 — 이 항목은 세션 종료 전 마지막에 재확인한다.

- [ ] **Step 6: AC6 — 레포 전체 잔존 참조**

Run:
```bash
grep -rli "colbert" . \
  --include='*.py' --include='*.yaml' --include='*.sh' --include='*.md' \
  2>/dev/null | grep -v '\.venv\|node_modules\|archive/\|private/\|CHANGELOG.md\|CONTRIBUTING.md\|docs/superpowers/plans/2026-04-25\|docs/superpowers/specs/2026-08-13\|docs/superpowers/plans/2026-08-13'
```
Expected: 출력 없음

- [ ] **Step 7: 전체 pytest 재실행 (회귀 확인)**

Run: `/Users/msbaek/.local/pipx/venvs/vault-intelligence/bin/python -m pytest tests/ -v 2>&1 | tail -40`
Expected: 모든 테스트 PASS (기존 테스트 포함 회귀 없음)

- [ ] **Step 8: 결과를 spec 문서에 기록**

`docs/superpowers/specs/2026-08-13-colbert-removal-design.md`의 "5. 승인 조건" 섹션 각 항목 옆에 실측값과 함께 체크 표시를 추가(예: `1. ... ✅ 실측: phys_footprint 6.8GB (2026-08-13 검증)`).

Run: `git add docs/superpowers/specs/2026-08-13-colbert-removal-design.md && git commit -m "$(cat <<'EOF'
docs(spec): ColBERT 제거 승인 조건 6개 실측 결과 기록

Spec: docs/superpowers/specs/2026-08-13-colbert-removal-design.md
EOF
)"`

---

### Task 9: claude-config 스킬 문서 갱신 (별도 레포, 별도 커밋)

이 태스크는 `~/git/vault-intelligence`가 아니라 `~/claude-config`(stow 대상, `~/.claude/skills/`의 실제 소스) 레포에서 진행한다. 별도 git 레포이므로 커밋도 분리한다.

**Files (모두 `~/claude-config` 기준 상대 경로):**
- Modify: `.claude/skills/vis/SKILL.md`
- Modify: `.claude/skills/vis/README.md`
- Modify: `.claude/skills/vis/references/cli-reference.md`
- Modify: `.claude/skills/vis-search-strategy/SKILL.md`
- Modify: `.claude/skills/vis-orchestra/SKILL.md`

- [ ] **Step 1: colbert 언급 지점 확인**

Run: `cd ~/claude-config && grep -n -i "colbert" .claude/skills/vis/SKILL.md .claude/skills/vis/README.md .claude/skills/vis/references/cli-reference.md .claude/skills/vis-search-strategy/SKILL.md .claude/skills/vis-orchestra/SKILL.md`

- [ ] **Step 2: 각 파일에서 colbert 권장 문구 제거**

Step 1의 결과를 바탕으로 각 위치에서: `--search-method colbert` 를 사용하라는 권장·예시는 삭제하거나 `hybrid`/`--rerank` 조합으로 대체한다. "검색 방법 선택 가이드" 류의 표에 colbert 행이 있으면 삭제한다. `vis reindex --with-colbert` 예시가 있으면 `vis reindex`로 수정한다.

- [ ] **Step 3: 잔존 참조 확인**

Run: `grep -rln -i "colbert" .claude/skills/vis/ .claude/skills/vis-search-strategy/ .claude/skills/vis-orchestra/`
Expected: 출력 없음

- [ ] **Step 4: Commit (claude-config 레포)**

```bash
cd ~/claude-config
git add .claude/skills/vis/SKILL.md .claude/skills/vis/README.md .claude/skills/vis/references/cli-reference.md .claude/skills/vis-search-strategy/SKILL.md .claude/skills/vis-orchestra/SKILL.md
git commit -m "$(cat <<'EOF'
docs(vis-skills): ColBERT 검색 권장 문구 제거

vault-intelligence에서 ColBERT가 제거되었다(2026-08-13, OOM 원인 —
사용률 0.04%인데 재인덱싱마다 32GB 적재). --search-method colbert는
이제 hybrid로 자동 폴백되므로 스킬 문서의 권장 예시도 걷어낸다.
EOF
)"
```
