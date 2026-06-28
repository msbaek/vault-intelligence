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
