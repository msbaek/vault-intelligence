"""vis × graphify Tier 1 walking skeleton — graph.json 을 정적 sidecar 로 읽어
개념 엣지를 문서 관계로 투영하고 벡터 related 와 비교한다. 명령 시점 무-LLM."""

import json
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path

import networkx as nx
from networkx.readwrite import json_graph

logger = logging.getLogger(__name__)

_KEEP_EXTRACTED = "EXTRACTED"
_KEEP_INFERRED = "INFERRED"


class GraphIndex:
    """graph.json 로드 + 엣지 정책 필터. 무방향 1-hop 인접 제공."""

    def __init__(self, graph_path: str, confidence_threshold: float = 0.8):
        self.confidence_threshold = confidence_threshold
        data = json.loads(Path(graph_path).read_text())
        g = json_graph.node_link_graph(data, edges="links")
        # Normalize to simple undirected graph so filtered_neighbors works
        # bidirectionally regardless of the graphify output format.
        if g.is_multigraph():
            # Collapse parallel edges; keep the edge with highest confidence_score.
            simple = nx.DiGraph() if g.is_directed() else nx.Graph()
            simple.add_nodes_from(g.nodes(data=True))
            for u, v, edata in g.edges(data=True):
                if simple.has_edge(u, v):
                    if edata.get("confidence_score", 0.0) > simple[u][v].get("confidence_score", 0.0):
                        simple[u][v].update(edata)
                else:
                    simple.add_edge(u, v, **edata)
            g = simple
        if g.is_directed():
            g = g.to_undirected()
        self._graph = g

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


def to_absolute(vault_path: str, vault_relative: str) -> str:
    """vault-relative 경로를 절대 경로로 변환.

    AdvancedSearchEngine 의 doc.path 는 절대 경로이므로,
    find_related_docs 에 vault-relative 를 직접 전달하면 매칭에 실패한다.
    """
    return str(Path(vault_path) / vault_relative)


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


def compute_novelty(graph_docs: list, vector_docs: list) -> list:
    """graph 에는 있고 vector top-k 에는 없는 문서(graph 순서 보존)."""
    vset = set(vector_docs)
    return [d for d in graph_docs if d not in vset]


def vector_paths_vault_relative(results: list, vault_path: str) -> list:
    """벡터 SearchResult 의 document.path 를 vault-relative 로 정규화."""
    out = []
    for r in results:
        p = r.document.path
        if os.path.isabs(p):
            p = os.path.relpath(p, vault_path)
        out.append(p.lstrip("./"))
    return out


def deterministic_sample(docs: list, n: int) -> list:
    """Sort then pick N items at even stride — result is input-order-independent."""
    uniq = sorted(set(docs))
    if n <= 0 or len(uniq) <= n:
        return uniq
    step = len(uniq) / n
    return [uniq[int(i * step)] for i in range(n)]


def run_graph_related_worksheet(vault_path: str, config: dict, data_dir,
                                sample_n: int = 8, top_k: int = 10, output=None) -> bool:
    """Sample N corpus docs, compute novel neighbors for each, write markdown judgment worksheet."""
    gconf = config.get("graph_related", {})
    corpus_prefix = gconf.get("corpus_prefix", "003-RESOURCES/DDD")
    threshold = gconf.get("confidence_threshold", 0.8)
    graph_path = Path(data_dir) / gconf.get("graph_path", "cache/graph/ddd/graph.json")
    if not graph_path.exists():
        print(f"graph.json not found: {graph_path} — run /graphify first")
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
        vector_results = finder.find_related_docs(to_absolute(vault_path, doc), top_k=top_k)
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


def run_graph_related(vault_path: str, file_path: str, config: dict, data_dir, top_k: int = 10) -> bool:
    """graph-related 단일 문서 A/B 뷰: vector / graph / novel 3블록 출력."""
    gconf = config.get("graph_related", {})
    corpus_prefix = gconf.get("corpus_prefix", "003-RESOURCES/DDD")
    threshold = gconf.get("confidence_threshold", 0.8)
    graph_path = Path(data_dir) / gconf.get("graph_path", "cache/graph/ddd/graph.json")

    target = to_vault_relative(file_path, corpus_prefix) if not file_path.startswith(corpus_prefix) else file_path.lstrip("./")

    # Vector baseline (reuse existing engine)
    from .advanced_search import AdvancedSearchEngine
    from .related_docs_finder import RelatedDocsFinder
    cache_dir = str(Path(data_dir) / "cache")
    engine = AdvancedSearchEngine(vault_path, cache_dir, config)
    if not engine.indexed:
        engine.build_index()
    finder = RelatedDocsFinder(engine, config)
    vector_results = finder.find_related_docs(to_absolute(vault_path, target), top_k=top_k)
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
