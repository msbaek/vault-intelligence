# vis × graphify `graph-related` Walking Skeleton Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** graphify가 오프라인으로 만든 DDD 개념 그래프(`graph.json`)를 정적 sidecar로 읽어 "개념 엣지 → 문서 관계"로 투영하고, 기존 벡터 `related`와 A/B 비교해 "벡터가 놓친 신규 이웃"을 드러내는 격리 명령 `vis graph-related` 를 신설한다.

**Architecture:** 명령 경로는 graph.json 읽기 + 1-hop 트래버설 + 기존 `RelatedDocsFinder` 재사용만(무-LLM). 모든 신규 로직은 `src/features/graph_related.py` 한 파일에 격리. 기존 search/related 코드 경로 무변경.

**Tech Stack:** Python 3.11, networkx(기존 의존성), pytest, 기존 `AdvancedSearchEngine`/`RelatedDocsFinder`.

## Global Constraints

- 명령(query) 시점 무-LLM: graph.json 읽기 + networkx 트래버설 + 기존 벡터 검색 재사용만. LLM·subagent 호출 금지.
- 기존 코드 경로 무변경: `advanced_search.py`, `related_docs_finder.py`, `vis search`, `vis related` 동작 불변.
- 완전 가역: 신규 파일 삭제 + subcommand 등록 제거 + config 키 제거 = 완전 롤백.
- 벡터 베이스라인 재사용: `RelatedDocsFinder.find_related_docs()` 호출. 재구현 금지.
- 엣지 정책: `confidence == "EXTRACTED"` OR (`confidence == "INFERRED"` AND `confidence_score >= threshold`). `AMBIGUOUS` 제외. threshold 기본 0.8.
- corpus: `003-RESOURCES/DDD`. 1-hop만. CLI 전용(HTTP/daemon 제외).
- 표본 추출은 결정적(정렬 + 균등 stride). 비결정적 난수 금지.

## File Structure

- **Create** `src/features/graph_related.py` — `GraphIndex`(load+filter), `to_vault_relative`(경로 정규화), `project`(투영+랭킹), `compute_novelty`, `generate_worksheet`, `run_graph_related`(orchestrator).
- **Modify** `src/__main__.py` — `graph-related` subparser 등록(2099행 부근, `related` 블록 직후) + 디스패치 분기(2492행 부근, `related` 분기 직후).
- **Modify** `config/settings.yaml` — `graph_related` 섹션 추가.
- **Create** `tests/test_graph_related.py` — unit + integration.
- **Offline data** `cache/graph/ddd/graph.json` — `/graphify` 산출물. `cache/` 는 이미 gitignored(.gitignore:48).

---

### Task 1: 오프라인 graph.json 빌드 + source_file 형태 확인 (prerequisite)

**비-TDD 작업** — graphify(LLM 추출)로 데이터 생성. 산출물은 gitignored 이므로 **커밋 없음**. 목적: 이후 Task 들의 fixture/정규화 규칙이 실제 데이터와 맞는지 확인.

**Files:**
- Produce: `cache/graph/ddd/graph.json` (gitignored)

- [ ] **Step 1: graphify 실행 (DDD corpus)**

graphify skill 을 main context 가 아닌 sub-agent 로 호출(skill frontmatter `model: sonnet`). 또는 수동으로:

Run: `/graphify ~/DocumentsLocal/msbaek_vault/003-RESOURCES/DDD`
Expected: `graphify-out/graph.json` 생성 (`Graph: N nodes, M edges, K communities` 출력).

- [ ] **Step 2: graph.json 을 vis cache 로 복사**

```bash
mkdir -p ~/git/vault-intelligence/cache/graph/ddd
cp graphify-out/graph.json ~/git/vault-intelligence/cache/graph/ddd/graph.json
ls -la ~/git/vault-intelligence/cache/graph/ddd/graph.json
```
Expected: 파일 존재.

- [ ] **Step 3: source_file 형태 확인 (정규화 규칙 검증)**

```bash
cd ~/git/vault-intelligence
python3 -c "
import json
d = json.load(open('cache/graph/ddd/graph.json'))
srcs = sorted({n.get('source_file') for n in d['nodes'] if n.get('source_file')})
print('node count:', len(d['nodes']))
print('link key present:', 'links' in d)
print('sample source_file values:')
for s in srcs[:8]: print('  ', repr(s))
ex = [e for e in d.get('links', []) if e.get('confidence')=='EXTRACTED']
inf = [e for e in d.get('links', []) if e.get('confidence')=='INFERRED']
amb = [e for e in d.get('links', []) if e.get('confidence')=='AMBIGUOUS']
print(f'edges: EXTRACTED={len(ex)} INFERRED={len(inf)} AMBIGUOUS={len(amb)}')
"
```
Expected: source_file 값들이 출력됨. **이 값의 형태(예: `Aggregate.md` vs `DDD/Aggregate.md` vs `003-RESOURCES/DDD/Aggregate.md`)를 기록**하라 — Task 3 의 `to_vault_relative` 가 이 형태를 vault-relative(`003-RESOURCES/DDD/...`)로 바꿔야 한다. INFERRED 엣지가 0이면 측정 신호가 약하므로 사용자에게 보고.

**Deliverable:** `cache/graph/ddd/graph.json` 존재 + source_file 형태 기록. (커밋 없음 — gitignored)

---

### Task 2: GraphIndex — graph.json 로드 + 엣지 정책 필터 + config

**Files:**
- Create: `src/features/graph_related.py`
- Modify: `config/settings.yaml`
- Test: `tests/test_graph_related.py`

**Interfaces:**
- Produces:
  - `class GraphIndex` with `__init__(self, graph_path: str, confidence_threshold: float = 0.8)` (로드 즉시 수행)
  - `GraphIndex.filtered_neighbors(self, node_id: str) -> list[tuple[str, float]]` — 필터 통과 엣지의 `(neighbor_id, weight*confidence_score)` 목록. 무방향(양쪽 다 탐색).
  - `GraphIndex.source_file_of(self, node_id: str) -> str | None`
  - `GraphIndex.node_ids` (property) `-> list[str]`

- [ ] **Step 1: config 키 추가**

`config/settings.yaml` 끝에 추가:
```yaml
# graph-related (vis × graphify Tier 1 walking skeleton)
graph_related:
  graph_path: "cache/graph/ddd/graph.json"
  corpus_prefix: "003-RESOURCES/DDD"
  confidence_threshold: 0.8
  default_top_k: 10
  default_sample: 8
```

- [ ] **Step 2: 합성 fixture + 실패 테스트 작성**

`tests/test_graph_related.py`:
```python
import json
import pytest
from pathlib import Path
from src.features.graph_related import GraphIndex

FIXTURE = {
    "directed": False, "multigraph": False, "graph": {},
    "nodes": [
        {"id": "aggregate_root", "label": "Aggregate Root", "source_file": "Aggregate.md"},
        {"id": "entity", "label": "Entity", "source_file": "Entity.md"},
        {"id": "value_object", "label": "Value Object", "source_file": "ValueObject.md"},
        {"id": "repository", "label": "Repository", "source_file": "Repository.md"},
    ],
    "links": [
        {"source": "aggregate_root", "target": "entity", "relation": "references",
         "confidence": "EXTRACTED", "confidence_score": 1.0, "weight": 1.0},
        {"source": "aggregate_root", "target": "value_object", "relation": "semantically_similar_to",
         "confidence": "INFERRED", "confidence_score": 0.85, "weight": 1.0},
        {"source": "aggregate_root", "target": "repository", "relation": "conceptually_related_to",
         "confidence": "INFERRED", "confidence_score": 0.6, "weight": 1.0},
    ],
}

@pytest.fixture
def graph_file(tmp_path):
    p = tmp_path / "graph.json"
    p.write_text(json.dumps(FIXTURE))
    return str(p)

def test_filter_keeps_extracted_and_high_inferred_drops_rest(graph_file):
    idx = GraphIndex(graph_file, confidence_threshold=0.8)
    neighbors = dict(idx.filtered_neighbors("aggregate_root"))
    assert "entity" in neighbors            # EXTRACTED
    assert "value_object" in neighbors      # INFERRED 0.85 >= 0.8
    assert "repository" not in neighbors    # INFERRED 0.6 < 0.8
    assert neighbors["entity"] == pytest.approx(1.0)
    assert neighbors["value_object"] == pytest.approx(0.85)

def test_source_file_lookup(graph_file):
    idx = GraphIndex(graph_file, confidence_threshold=0.8)
    assert idx.source_file_of("entity") == "Entity.md"
```

- [ ] **Step 3: 테스트 실패 확인**

Run: `pytest tests/test_graph_related.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'src.features.graph_related'`

- [ ] **Step 4: GraphIndex 구현**

`src/features/graph_related.py`:
```python
"""vis × graphify Tier 1 walking skeleton — graph.json 을 정적 sidecar 로 읽어
개념 엣지를 문서 관계로 투영하고 벡터 related 와 비교한다. 명령 시점 무-LLM."""

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path

from networkx.readwrite import json_graph

logger = logging.getLogger(__name__)

_KEEP_EXTRACTED = "EXTRACTED"
_KEEP_INFERRED = "INFERRED"


class GraphIndex:
    """graph.json 로드 + 엣지 정책 필터. 무방향 1-hop 인접 제공."""

    def __init__(self, graph_path: str, confidence_threshold: float = 0.8):
        self.confidence_threshold = confidence_threshold
        data = json.loads(Path(graph_path).read_text())
        self._graph = json_graph.node_link_graph(data, edges="links")

    @property
    def node_ids(self) -> list:
        return list(self._graph.nodes())

    def source_file_of(self, node_id: str):
        if node_id not in self._graph:
            return None
        return self._graph.nodes[node_id].get("source_file")

    def _edge_passes(self, edata: dict) -> bool:
        conf = edata.get("confidence")
        if conf == _KEEP_EXTRACTED:
            return True
        if conf == _KEEP_INFERRED:
            return float(edata.get("confidence_score", 0.0)) >= self.confidence_threshold
        return False  # AMBIGUOUS 등 제외

    def filtered_neighbors(self, node_id: str) -> list:
        if node_id not in self._graph:
            return []
        out = []
        for nbr in self._graph.neighbors(node_id):
            edata = self._graph.get_edge_data(node_id, nbr)
            if self._edge_passes(edata):
                score = float(edata.get("weight", 1.0)) * float(edata.get("confidence_score", 1.0))
                out.append((nbr, score))
        return out
```

- [ ] **Step 5: 테스트 통과 확인**

Run: `pytest tests/test_graph_related.py -v`
Expected: PASS (2 passed)

- [ ] **Step 6: 커밋**

```bash
git add src/features/graph_related.py tests/test_graph_related.py config/settings.yaml
git commit -F - <<'EOF'
feat(graph-related): GraphIndex — graph.json 로드 + 엣지 정책 필터

EXTRACTED + INFERRED>=threshold 만 통과, AMBIGUOUS 제외. graph_related config 추가.
EOF
```
(한글 깨짐 우려 시 임시 파일 + `git commit -F <file>` 사용.)

---

### Task 3: 경로 정규화 (graphify source_file → vault-relative)

**Files:**
- Modify: `src/features/graph_related.py`
- Test: `tests/test_graph_related.py`

**Interfaces:**
- Produces: `to_vault_relative(source_file: str, corpus_prefix: str) -> str`

- [ ] **Step 1: 실패 테스트 작성**

`tests/test_graph_related.py` 에 추가:
```python
from src.features.graph_related import to_vault_relative

def test_to_vault_relative_bare_filename():
    assert to_vault_relative("Aggregate.md", "003-RESOURCES/DDD") == "003-RESOURCES/DDD/Aggregate.md"

def test_to_vault_relative_already_prefixed():
    assert to_vault_relative("003-RESOURCES/DDD/Aggregate.md", "003-RESOURCES/DDD") == "003-RESOURCES/DDD/Aggregate.md"

def test_to_vault_relative_partial_prefix():
    assert to_vault_relative("DDD/Aggregate.md", "003-RESOURCES/DDD") == "003-RESOURCES/DDD/Aggregate.md"

def test_to_vault_relative_strips_leading_dotslash():
    assert to_vault_relative("./Aggregate.md", "003-RESOURCES/DDD") == "003-RESOURCES/DDD/Aggregate.md"
```

- [ ] **Step 2: 테스트 실패 확인**

Run: `pytest tests/test_graph_related.py -k to_vault_relative -v`
Expected: FAIL — `ImportError: cannot import name 'to_vault_relative'`

- [ ] **Step 3: 구현 추가**

`src/features/graph_related.py` 에 추가:
```python
def to_vault_relative(source_file: str, corpus_prefix: str) -> str:
    """graphify source_file 을 vault-relative 경로로 정규화.

    graphify 는 입력 디렉토리 기준 상대경로를 저장한다(bare filename / 부분 prefix /
    full prefix 모두 가능). corpus_prefix(vault-relative)를 기준으로 일관된
    vault-relative 경로를 만든다. Task 1 에서 확인한 실제 형태에 맞춰 조정할 것.
    """
    s = source_file.strip().lstrip("./")
    prefix = corpus_prefix.strip("/")
    if s == prefix or s.startswith(prefix + "/"):
        return s
    # 부분 prefix(예: 'DDD/...') 처리: corpus_prefix 의 마지막 segment 와 겹치면 제거
    last_seg = prefix.split("/")[-1]
    if s.startswith(last_seg + "/"):
        s = s[len(last_seg) + 1:]
    return f"{prefix}/{s}"
```

- [ ] **Step 4: 테스트 통과 확인**

Run: `pytest tests/test_graph_related.py -k to_vault_relative -v`
Expected: PASS (4 passed)

- [ ] **Step 5: 커밋**

```bash
git add src/features/graph_related.py tests/test_graph_related.py
git commit -m "feat(graph-related): to_vault_relative 경로 정규화"
```

---

### Task 4: project — 개념→문서 투영 + 랭킹

**Files:**
- Modify: `src/features/graph_related.py`
- Test: `tests/test_graph_related.py`

**Interfaces:**
- Consumes: `GraphIndex.filtered_neighbors`, `GraphIndex.source_file_of`, `GraphIndex.node_ids`, `to_vault_relative`
- Produces:
  - `@dataclass GraphRelatedDoc: doc_path: str; score: float; contributors: list`
  - `project(index: GraphIndex, target_doc: str, corpus_prefix: str, top_k: int = 10) -> list[GraphRelatedDoc]`
  - (`target_doc` 는 vault-relative; 반환 `doc_path` 도 vault-relative, target 자신 제외, score 내림차순)

- [ ] **Step 1: 실패 테스트 작성**

`tests/test_graph_related.py` 에 추가:
```python
from src.features.graph_related import project, GraphRelatedDoc

def test_project_maps_concepts_to_docs_and_ranks(graph_file):
    idx = GraphIndex(graph_file, confidence_threshold=0.8)
    results = project(idx, "003-RESOURCES/DDD/Aggregate.md", "003-RESOURCES/DDD", top_k=10)
    paths = [r.doc_path for r in results]
    # entity(1.0), value_object(0.85) 포함; repository(0.6<0.8) 제외; 자기 자신 제외
    assert "003-RESOURCES/DDD/Entity.md" in paths
    assert "003-RESOURCES/DDD/ValueObject.md" in paths
    assert "003-RESOURCES/DDD/Repository.md" not in paths
    assert "003-RESOURCES/DDD/Aggregate.md" not in paths
    # 점수 내림차순
    assert results[0].doc_path == "003-RESOURCES/DDD/Entity.md"
    assert results[0].score >= results[1].score

def test_project_unknown_doc_returns_empty(graph_file):
    idx = GraphIndex(graph_file, confidence_threshold=0.8)
    assert project(idx, "003-RESOURCES/DDD/Nonexistent.md", "003-RESOURCES/DDD") == []
```

- [ ] **Step 2: 테스트 실패 확인**

Run: `pytest tests/test_graph_related.py -k project -v`
Expected: FAIL — `ImportError: cannot import name 'project'`

- [ ] **Step 3: 구현 추가**

`src/features/graph_related.py` 에 추가:
```python
@dataclass
class GraphRelatedDoc:
    doc_path: str
    score: float
    contributors: list = field(default_factory=list)


def project(index, target_doc: str, corpus_prefix: str, top_k: int = 10) -> list:
    """대상 문서 D 의 개념 엣지를 문서 관계로 투영.

    1) seed = source_file 이 D 인 노드들
    2) 각 seed 의 1-hop 필터 통과 이웃
    3) 이웃 개념 → source_file 문서로 역매핑 (D 자신 제외)
    4) 문서별 score 합산 (weight*confidence_score)
    """
    seeds = [n for n in index.node_ids
             if index.source_file_of(n)
             and to_vault_relative(index.source_file_of(n), corpus_prefix) == target_doc]
    if not seeds:
        return []

    doc_score: dict = {}
    doc_contrib: dict = {}
    for seed in seeds:
        for nbr, score in index.filtered_neighbors(seed):
            src = index.source_file_of(nbr)
            if not src:
                continue
            doc = to_vault_relative(src, corpus_prefix)
            if doc == target_doc:
                continue
            doc_score[doc] = doc_score.get(doc, 0.0) + score
            doc_contrib.setdefault(doc, []).append(f"{seed} -> {nbr} ({score:.2f})")

    ranked = sorted(doc_score.items(), key=lambda kv: kv[1], reverse=True)[:top_k]
    return [GraphRelatedDoc(doc_path=d, score=s, contributors=doc_contrib[d]) for d, s in ranked]
```

- [ ] **Step 4: 테스트 통과 확인**

Run: `pytest tests/test_graph_related.py -k project -v`
Expected: PASS (2 passed)

- [ ] **Step 5: 커밋**

```bash
git add src/features/graph_related.py tests/test_graph_related.py
git commit -m "feat(graph-related): project 개념→문서 투영+랭킹"
```

---

### Task 5: compute_novelty — graph − vector top-k

**Files:**
- Modify: `src/features/graph_related.py`
- Test: `tests/test_graph_related.py`

**Interfaces:**
- Produces: `compute_novelty(graph_docs: list[str], vector_docs: list[str]) -> list[str]` — graph 에 있고 vector 에 없는 문서(graph 순서 보존)

- [ ] **Step 1: 실패 테스트 작성**

```python
from src.features.graph_related import compute_novelty

def test_compute_novelty_returns_graph_minus_vector():
    graph = ["a.md", "b.md", "c.md"]
    vector = ["b.md", "x.md"]
    assert compute_novelty(graph, vector) == ["a.md", "c.md"]

def test_compute_novelty_preserves_graph_order():
    assert compute_novelty(["c.md", "a.md"], []) == ["c.md", "a.md"]
```

- [ ] **Step 2: 테스트 실패 확인**

Run: `pytest tests/test_graph_related.py -k novelty -v`
Expected: FAIL — `ImportError: cannot import name 'compute_novelty'`

- [ ] **Step 3: 구현 추가**

```python
def compute_novelty(graph_docs: list, vector_docs: list) -> list:
    """graph 에는 있고 vector top-k 에는 없는 문서(graph 순서 보존)."""
    vset = set(vector_docs)
    return [d for d in graph_docs if d not in vset]
```

- [ ] **Step 4: 테스트 통과 확인**

Run: `pytest tests/test_graph_related.py -k novelty -v`
Expected: PASS (2 passed)

- [ ] **Step 5: 커밋**

```bash
git add src/features/graph_related.py tests/test_graph_related.py
git commit -m "feat(graph-related): compute_novelty"
```

---

### Task 6: run_graph_related orchestrator + CLI `vis graph-related <doc>`

**Files:**
- Modify: `src/features/graph_related.py`
- Modify: `src/__main__.py`
- Test: `tests/test_graph_related.py`

**Interfaces:**
- Consumes: `GraphIndex`, `project`, `compute_novelty`, `to_vault_relative`, 기존 `RelatedDocsFinder.find_related_docs() -> list[SearchResult]` (`SearchResult.document.path`, `.similarity_score`).
- Produces: `run_graph_related(vault_path: str, file_path: str, config: dict, data_dir: Path, top_k: int = 10) -> bool` (3블록 출력, graph.json 없거나 corpus 밖이면 안내 후 graph/novel 빈 처리).

- [ ] **Step 1: orchestrator 헬퍼(벡터 경로 정규화) 실패 테스트**

```python
from src.features.graph_related import vector_paths_vault_relative

class _Doc:
    def __init__(self, path): self.path = path
class _Res:
    def __init__(self, path, score): self.document = _Doc(path); self.similarity_score = score

def test_vector_paths_vault_relative_strips_vault_prefix():
    vault = "/Users/x/vault"
    results = [_Res("/Users/x/vault/003-RESOURCES/DDD/Entity.md", 0.7),
               _Res("003-RESOURCES/DDD/Repository.md", 0.6)]
    assert vector_paths_vault_relative(results, vault) == [
        "003-RESOURCES/DDD/Entity.md", "003-RESOURCES/DDD/Repository.md"]
```

- [ ] **Step 2: 테스트 실패 확인**

Run: `pytest tests/test_graph_related.py -k vector_paths -v`
Expected: FAIL — `ImportError: cannot import name 'vector_paths_vault_relative'`

- [ ] **Step 3: orchestrator 구현**

`src/features/graph_related.py` 에 추가:
```python
import os


def vector_paths_vault_relative(results: list, vault_path: str) -> list:
    """벡터 SearchResult 의 document.path 를 vault-relative 로 정규화."""
    out = []
    for r in results:
        p = r.document.path
        if os.path.isabs(p):
            p = os.path.relpath(p, vault_path)
        out.append(p.lstrip("./"))
    return out


def run_graph_related(vault_path: str, file_path: str, config: dict, data_dir, top_k: int = 10) -> bool:
    """graph-related 단일 문서 A/B 뷰: vector / graph / novel 3블록 출력."""
    gconf = config.get("graph_related", {})
    corpus_prefix = gconf.get("corpus_prefix", "003-RESOURCES/DDD")
    threshold = gconf.get("confidence_threshold", 0.8)
    graph_path = Path(data_dir) / gconf.get("graph_path", "cache/graph/ddd/graph.json")

    target = to_vault_relative(file_path, corpus_prefix) if not file_path.startswith(corpus_prefix) else file_path.lstrip("./")

    # 벡터 베이스라인 (기존 엔진 재사용)
    from .advanced_search import AdvancedSearchEngine
    from .related_docs_finder import RelatedDocsFinder
    cache_dir = str(Path(data_dir) / "cache")
    engine = AdvancedSearchEngine(vault_path, cache_dir, config)
    if not engine.indexed:
        engine.build_index()
    finder = RelatedDocsFinder(engine, config)
    vector_results = finder.find_related_docs(file_path, top_k=top_k)
    vector_docs = vector_paths_vault_relative(vector_results, vault_path)

    print(f"\n=== graph-related: {target} ===")
    print(f"\n[VECTOR top-{top_k}]  (기존 vis related)")
    for d in vector_docs:
        print(f"  - {d}")

    if not graph_path.exists():
        print(f"\n[GRAPH] graph.json 없음: {graph_path}")
        print("  → /graphify 003-RESOURCES/DDD 먼저 실행 후 cache/graph/ddd/ 에 배치")
        return True

    index = GraphIndex(str(graph_path), confidence_threshold=threshold)
    graph_results = project(index, target, corpus_prefix, top_k=top_k)
    if not graph_results:
        print(f"\n[GRAPH] 이 문서는 graph corpus 에 없음 (개념 노드 없음): {target}")
        return True

    graph_docs = [r.doc_path for r in graph_results]
    print(f"\n[GRAPH top-{top_k}]  (개념 엣지 투영)")
    for r in graph_results:
        print(f"  - {r.doc_path}  (score={r.score:.2f})  via {', '.join(r.contributors[:3])}")

    novel = compute_novelty(graph_docs, vector_docs)
    print(f"\n[NOVEL]  graph 에만 있고 vector top-{top_k} 엔 없는 이웃 (판정 대상)")
    if not novel:
        print("  (없음 — 이 문서에선 graph 가 새 연결을 추가하지 못함)")
    for d in novel:
        gr = next(r for r in graph_results if r.doc_path == d)
        print(f"  - {d}  via {', '.join(gr.contributors[:3])}")
    return True
```

- [ ] **Step 4: 헬퍼 테스트 통과 확인**

Run: `pytest tests/test_graph_related.py -k vector_paths -v`
Expected: PASS (1 passed)

- [ ] **Step 5: CLI subparser 등록**

`src/__main__.py` 의 `related` subparser 블록(약 2097행) 직후에 추가:
```python
    # --- graph-related (vis × graphify Tier 1) ---
    p = subparsers.add_parser("graph-related", help="개념 그래프 기반 관련 문서 (vector A/B 비교)")
    p.add_argument("file", help="기준 파일 경로 (vault-relative)")
    p.add_argument("--top-k", type=int, default=10, help="상위 K개 (기본 10)")
    p.add_argument("--sample", type=int, default=0, help="N개 표본 판정 워크시트 생성")
    p.add_argument("--output", default=None, help="워크시트 출력 경로 (--sample 과 함께)")
```

- [ ] **Step 6: CLI 디스패치 분기 등록**

`src/__main__.py` 의 `elif args.command == "related":` 블록(약 2476행) 직후에 추가:
```python
    elif args.command == "graph-related":
        if args.sample and args.sample > 0:
            # lazy import — run_graph_related_worksheet 는 Task 7 에서 정의됨.
            # --sample 분기 진입 시에만 import 하여 Task 6 단독 스모크(--sample 없이)가
            # ImportError 없이 동작하도록 한다.
            from src.features.graph_related import run_graph_related_worksheet
            run_graph_related_worksheet(
                vault_path=vault_path, config=config, data_dir=data_dir,
                sample_n=args.sample, top_k=args.top_k, output=args.output,
            )
        else:
            from src.features.graph_related import run_graph_related
            run_graph_related(
                vault_path=vault_path, file_path=args.file, config=config,
                data_dir=data_dir, top_k=args.top_k,
            )
```
(주의: `vault_path`, `config`, `data_dir` 는 main() 내에서 이미 정의된 변수 — `related` 분기와 동일하게 참조. worksheet import 는 `--sample` 분기 안에서만 실행되므로 Task 6 단계에서 `run_graph_related_worksheet` 미정의여도 안전.)

- [ ] **Step 7: 실제 graph.json 으로 integration 스모크 (수동)**

Run: `vis graph-related "003-RESOURCES/DDD/<Task1에서 확인한 실제 파일>.md" --top-k 10`
Expected: VECTOR / GRAPH / NOVEL 3블록 출력. 명령 중 LLM 호출 없음(즉시 반환). graph.json 있으면 GRAPH 블록 비어있지 않음.

- [ ] **Step 8: 커밋**

```bash
git add src/features/graph_related.py src/__main__.py tests/test_graph_related.py
git commit -m "feat(graph-related): run_graph_related orchestrator + CLI graph-related"
```

---

### Task 7: `--sample N --output` 결정적 판정 워크시트 생성

**Files:**
- Modify: `src/features/graph_related.py`
- Test: `tests/test_graph_related.py`

**Interfaces:**
- Consumes: `GraphIndex`, `project`, `compute_novelty`, `to_vault_relative`, `vector_paths_vault_relative`, `RelatedDocsFinder`.
- Produces:
  - `deterministic_sample(docs: list[str], n: int) -> list[str]` (정렬 + 균등 stride)
  - `run_graph_related_worksheet(vault_path: str, config: dict, data_dir, sample_n: int = 8, top_k: int = 10, output: str | None = None) -> bool`

- [ ] **Step 1: 결정적 샘플 실패 테스트**

```python
from src.features.graph_related import deterministic_sample

def test_deterministic_sample_is_stable_and_even():
    docs = [f"{i}.md" for i in range(20)]
    s1 = deterministic_sample(docs, 4)
    s2 = deterministic_sample(list(reversed(docs)), 4)
    assert s1 == s2            # 입력 순서 무관(정렬 기반)
    assert len(s1) == 4
    assert s1 == sorted(s1)    # 정렬됨

def test_deterministic_sample_n_larger_than_corpus():
    docs = ["b.md", "a.md"]
    assert deterministic_sample(docs, 8) == ["a.md", "b.md"]
```

- [ ] **Step 2: 테스트 실패 확인**

Run: `pytest tests/test_graph_related.py -k deterministic_sample -v`
Expected: FAIL — `ImportError: cannot import name 'deterministic_sample'`

- [ ] **Step 3: 구현 추가**

```python
def deterministic_sample(docs: list, n: int) -> list:
    """정렬 후 균등 stride 로 N개 결정적 추출."""
    uniq = sorted(set(docs))
    if n <= 0 or len(uniq) <= n:
        return uniq
    step = len(uniq) / n
    return [uniq[int(i * step)] for i in range(n)]


def run_graph_related_worksheet(vault_path: str, config: dict, data_dir,
                                sample_n: int = 8, top_k: int = 10, output=None) -> bool:
    """표본 N개 문서의 novel 쌍을 모아 판정 워크시트(markdown) 생성."""
    gconf = config.get("graph_related", {})
    corpus_prefix = gconf.get("corpus_prefix", "003-RESOURCES/DDD")
    threshold = gconf.get("confidence_threshold", 0.8)
    graph_path = Path(data_dir) / gconf.get("graph_path", "cache/graph/ddd/graph.json")
    if not graph_path.exists():
        print(f"graph.json 없음: {graph_path} — /graphify 먼저 실행")
        return False

    index = GraphIndex(str(graph_path), confidence_threshold=threshold)
    corpus_docs = sorted({to_vault_relative(index.source_file_of(n), corpus_prefix)
                          for n in index.node_ids if index.source_file_of(n)})
    sample = deterministic_sample(corpus_docs, sample_n)

    from .advanced_search import AdvancedSearchEngine
    from .related_docs_finder import RelatedDocsFinder
    cache_dir = str(Path(data_dir) / "cache")
    engine = AdvancedSearchEngine(vault_path, cache_dir, config)
    if not engine.indexed:
        engine.build_index()
    finder = RelatedDocsFinder(engine, config)

    lines = ["# graph-related 판정 워크시트",
             "",
             f"corpus: {corpus_prefix} · 표본 {len(sample)}개 · threshold {threshold}",
             "각 행의 [판정] 칸에 O(관련) / X(무관) 입력 후 채팅에 보고.",
             "",
             "| 대상문서 | 신규이웃(graph만) | 기여 개념·엣지 | 판정 |",
             "|---|---|---|---|"]
    total_novel = 0
    for doc in sample:
        graph_results = project(index, doc, corpus_prefix, top_k=top_k)
        if not graph_results:
            continue
        vector_results = finder.find_related_docs(doc, top_k=top_k)
        vector_docs = vector_paths_vault_relative(vector_results, vault_path)
        novel = compute_novelty([r.doc_path for r in graph_results], vector_docs)
        for d in novel:
            gr = next(r for r in graph_results if r.doc_path == d)
            contrib = "; ".join(gr.contributors[:2])
            lines.append(f"| {doc} | {d} | {contrib} | |")
            total_novel += 1
    lines += ["", f"총 신규이웃 쌍: {total_novel}"]
    content = "\n".join(lines)

    if output:
        Path(output).write_text(content)
        print(f"워크시트 생성: {output} (신규이웃 {total_novel}쌍)")
    else:
        print(content)
    return True
```

- [ ] **Step 4: 테스트 통과 확인**

Run: `pytest tests/test_graph_related.py -k deterministic_sample -v`
Expected: PASS (2 passed)

- [ ] **Step 5: 전체 테스트 통과 확인**

Run: `pytest tests/test_graph_related.py -v`
Expected: 모든 테스트 PASS.

- [ ] **Step 6: 워크시트 스모크 (수동)**

Run: `vis graph-related dummy --sample 8 --output /tmp/graph-worksheet.md`
Expected: `워크시트 생성: /tmp/graph-worksheet.md (신규이웃 N쌍)` 출력. 파일에 표 생성됨.

- [ ] **Step 7: 커밋**

```bash
git add src/features/graph_related.py tests/test_graph_related.py
git commit -m "feat(graph-related): 결정적 표본 판정 워크시트 생성"
```

---

## Self-Review

**1. Spec coverage:**
- spec §2.1 graph.json 오프라인 빌드 → Task 1 ✓
- spec §2.2 vector/graph/novel 3블록 + 무-LLM → Task 6 ✓
- spec §2.3 엣지 정책 unit-tested → Task 2 ✓
- spec §2.4 `--sample` 워크시트 → Task 7 ✓
- spec §2.5 측정 진술(신규이웃 집계) → Task 7 워크시트 `총 신규이웃 쌍` + 사용자 판정 ✓
- spec §7 경로 정규화 함정 → Task 3 ✓
- spec §9 에러 처리(graph 없음/corpus 밖/정규화 실패) → Task 6 graph 없음·corpus 밖 처리, Task 3 정규화 ✓
- spec §10 테스트(필터/투영/novelty/정규화/integration/smoke) → Task 2~7 ✓
- spec §12 실패 조건(무-LLM·회귀·정규화·필터·근거·결정적표본) → 제약으로 각 Task 반영 ✓

**2. Placeholder scan:** TBD/TODO 없음. 모든 코드 step 에 실제 코드 포함.

**3. Type consistency:** `GraphIndex.filtered_neighbors -> list[(id, score)]`, `source_file_of -> str|None`, `project -> list[GraphRelatedDoc]`, `compute_novelty -> list[str]`, `vector_paths_vault_relative -> list[str]`, `deterministic_sample -> list[str]`, `run_graph_related`/`run_graph_related_worksheet -> bool`. Task 6 디스패치가 두 orchestrator 를 호출하며 시그니처 일치. ✓

**알려진 위험(실행 중 확인 필요):** Task 1 의 source_file 실제 형태가 Task 3 `to_vault_relative` 가정과 다르면 정규화 규칙을 조정해야 함(Task 1 Step 3 에서 기록·검증). networkx `node_link_graph(data, edges="links")` 는 graphify 와 동일 호출 — 설치된 버전이 graphify 를 실행하므로 호환 보장.
