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
