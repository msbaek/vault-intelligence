#!/usr/bin/env python3
"""
Knowledge Graph Builder for Vault Intelligence System V2

문서 간 관계를 분석하여 지식 그래프를 구축하고 시각화
"""

import os
import json
import logging
from typing import List, Dict, Optional, Tuple, Set, Any
from pathlib import Path
from dataclasses import dataclass, asdict
from datetime import datetime
import numpy as np
from collections import defaultdict, Counter

try:
    import networkx as nx
    NETWORKX_AVAILABLE = True
except ImportError:
    NETWORKX_AVAILABLE = False
    
try:
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

from ..core.vault_processor import Document

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class GraphNode:
    """그래프 노드 (문서)"""
    id: str
    title: str
    path: str
    tags: List[str]
    word_count: int
    centrality_score: Optional[float] = None
    cluster_id: Optional[str] = None
    node_type: str = "document"  # document, topic, tag
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass 
class GraphEdge:
    """그래프 엣지 (관계)"""
    source: str
    target: str
    weight: float
    relationship_type: str  # similarity, tag, reference
    metadata: Optional[Dict] = None
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class KnowledgeGraph:
    """지식 그래프"""
    nodes: List[GraphNode]
    edges: List[GraphEdge]
    communities: Optional[List[List[str]]] = None
    centrality_scores: Optional[Dict[str, float]] = None
    graph_metrics: Optional[Dict] = None
    created_at: Optional[datetime] = None
    
    def get_node_count(self) -> int:
        return len(self.nodes)
    
    def get_edge_count(self) -> int:
        return len(self.edges)
    
    def get_density(self) -> float:
        """그래프 밀도 계산"""
        n = len(self.nodes)
        if n < 2:
            return 0.0
        max_edges = n * (n - 1) / 2
        return len(self.edges) / max_edges if max_edges > 0 else 0.0


class KnowledgeGraphBuilder:
    """지식 그래프 구축기"""
    
    def __init__(
        self,
        search_engine,
        config: Dict = None
    ):
        """
        Args:
            search_engine: AdvancedSearchEngine 인스턴스
            config: 그래프 구축 설정
        """
        self.search_engine = search_engine
        self.config = config or {}
        
        # 기본 설정
        self.similarity_threshold = self.config.get('graph', {}).get(
            'similarity_threshold', 0.4
        )
        self.max_edges_per_node = self.config.get('graph', {}).get(
            'max_edges_per_node', 10
        )
        self.include_tag_nodes = self.config.get('graph', {}).get(
            'include_tag_nodes', True
        )
        self.min_word_count = self.config.get('graph', {}).get(
            'min_word_count', 50
        )
        
        logger.info(f"지식 그래프 구축기 초기화 - 임계값: {self.similarity_threshold}")
    
    def build_graph(
        self,
        documents: Optional[List[Document]] = None,
        similarity_threshold: Optional[float] = None,
        include_tag_nodes: Optional[bool] = None
    ) -> KnowledgeGraph:
        """지식 그래프 구축"""
        try:
            if not self.search_engine.indexed:
                logger.warning("검색 엔진이 인덱싱되지 않았습니다.")
                return self._create_empty_graph()
            
            # 설정값 사용
            similarity_threshold = similarity_threshold or self.similarity_threshold
            include_tag_nodes = include_tag_nodes if include_tag_nodes is not None else self.include_tag_nodes
            
            # 문서 필터링
            if documents is None:
                documents = self._filter_documents(self.search_engine.documents)
            else:
                documents = self._filter_documents(documents)
            
            if len(documents) < 2:
                logger.warning("그래프를 구축하기에 문서가 부족합니다.")
                return self._create_empty_graph()
            
            logger.info(f"지식 그래프 구축 시작 - {len(documents)}개 문서")
            
            # 노드 생성
            nodes = self._create_document_nodes(documents)
            
            # 태그 노드 추가
            if include_tag_nodes:
                tag_nodes = self._create_tag_nodes(documents)
                nodes.extend(tag_nodes)
            
            # 엣지 생성
            edges = []
            
            # 유사도 기반 엣지
            similarity_edges = self._create_similarity_edges(documents, similarity_threshold)
            edges.extend(similarity_edges)
            
            # 태그 기반 엣지
            if include_tag_nodes:
                tag_edges = self._create_tag_edges(documents, tag_nodes)
                edges.extend(tag_edges)
            
            # 참조 기반 엣지 (Obsidian 링크)
            reference_edges = self._create_reference_edges(documents)
            edges.extend(reference_edges)
            
            logger.info(f"그래프 구축 완료 - 노드: {len(nodes)}개, 엣지: {len(edges)}개")
            
            # 그래프 분석
            graph_metrics = self._analyze_graph(nodes, edges)
            centrality_scores = self._calculate_centrality(nodes, edges)
            communities = self._detect_communities(nodes, edges)
            
            # 지식 그래프 생성
            knowledge_graph = KnowledgeGraph(
                nodes=nodes,
                edges=edges,
                communities=communities,
                centrality_scores=centrality_scores,
                graph_metrics=graph_metrics,
                created_at=datetime.now()
            )
            
            return knowledge_graph
            
        except Exception as e:
            logger.error(f"지식 그래프 구축 실패: {e}")
            return self._create_empty_graph()
    
    def _filter_documents(self, documents: List[Document]) -> List[Document]:
        """문서 필터링"""
        filtered = []
        
        for doc in documents:
            logger.info(f"문서 체크: {doc.title} - 단어수: {doc.word_count}, 임베딩: {doc.embedding is not None}")
            
            # 최소 단어 수 확인
            if doc.word_count < self.min_word_count:
                logger.info(f"  -> 단어수 부족 (최소: {self.min_word_count})")
                continue
            
            # 임베딩 존재 확인
            if doc.embedding is None:
                logger.info(f"  -> 임베딩 없음")
                continue
            
            if np.allclose(doc.embedding, 0):
                logger.info(f"  -> 임베딩이 모두 0")
                continue
            
            filtered.append(doc)
            logger.info(f"  -> 필터링 통과")
        
        logger.info(f"필터링된 문서: {len(filtered)}개 (원본: {len(documents)}개)")
        return filtered
    
    def _create_document_nodes(self, documents: List[Document]) -> List[GraphNode]:
        """문서 노드 생성"""
        nodes = []
        
        for doc in documents:
            node = GraphNode(
                id=f"doc_{len(nodes)}",
                title=doc.title,
                path=doc.path,
                tags=doc.tags,
                word_count=doc.word_count,
                node_type="document"
            )
            nodes.append(node)
        
        return nodes
    
    def _create_tag_nodes(self, documents: List[Document]) -> List[GraphNode]:
        """태그 노드 생성"""
        tag_counter = Counter()
        
        # 태그 빈도 계산
        for doc in documents:
            if doc.tags:
                tag_counter.update(doc.tags)
        
        # 빈도 2 이상인 태그만 노드로 생성
        tag_nodes = []
        for tag, count in tag_counter.items():
            if count >= 2:
                node = GraphNode(
                    id=f"tag_{tag.replace('/', '_')}",
                    title=f"#{tag}",
                    path=f"tag:{tag}",
                    tags=[],
                    word_count=count,  # 태그의 경우 언급 횟수
                    node_type="tag"
                )
                tag_nodes.append(node)
        
        logger.info(f"태그 노드 생성: {len(tag_nodes)}개")
        return tag_nodes
    
    def _create_similarity_edges(
        self, 
        documents: List[Document], 
        threshold: float
    ) -> List[GraphEdge]:
        """유사도 기반 엣지 생성"""
        edges = []
        
        try:
            # 임베딩 추출
            embeddings = np.array([doc.embedding for doc in documents])
            
            # 유사도 매트릭스 계산
            similarities = np.dot(embeddings, embeddings.T)
            
            for i in range(len(documents)):
                # 현재 문서와 유사한 문서들 찾기
                similar_indices = []
                for j in range(len(documents)):
                    if i != j and similarities[i, j] >= threshold:
                        similar_indices.append((j, similarities[i, j]))
                
                # 상위 k개만 선택 (너무 많은 엣지 방지)
                similar_indices.sort(key=lambda x: x[1], reverse=True)
                similar_indices = similar_indices[:self.max_edges_per_node]
                
                for j, similarity in similar_indices:
                    edge = GraphEdge(
                        source=f"doc_{i}",
                        target=f"doc_{j}",
                        weight=float(similarity),
                        relationship_type="similarity",
                        metadata={
                            "source_title": documents[i].title,
                            "target_title": documents[j].title,
                            "similarity_score": float(similarity)
                        }
                    )
                    edges.append(edge)
            
            logger.info(f"유사도 엣지 생성: {len(edges)}개")
            return edges
            
        except Exception as e:
            logger.error(f"유사도 엣지 생성 실패: {e}")
            return []
    
    def _create_tag_edges(
        self, 
        documents: List[Document], 
        tag_nodes: List[GraphNode]
    ) -> List[GraphEdge]:
        """태그 기반 엣지 생성"""
        edges = []
        
        try:
            # 태그 ID 매핑
            tag_id_map = {node.title[1:]: node.id for node in tag_nodes}  # '#' 제거
            
            for i, doc in enumerate(documents):
                if doc.tags:
                    for tag in doc.tags:
                        if tag in tag_id_map:
                            edge = GraphEdge(
                                source=f"doc_{i}",
                                target=tag_id_map[tag],
                                weight=1.0,
                                relationship_type="tag",
                                metadata={
                                    "document_title": doc.title,
                                    "tag": tag
                                }
                            )
                            edges.append(edge)
            
            logger.info(f"태그 엣지 생성: {len(edges)}개")
            return edges
            
        except Exception as e:
            logger.error(f"태그 엣지 생성 실패: {e}")
            return []
    
    def _create_reference_edges(self, documents: List[Document]) -> List[GraphEdge]:
        """참조 기반 엣지 생성 (Obsidian 내부 링크)"""
        edges = []
        
        try:
            # 문서 경로 to 인덱스 매핑
            path_to_index = {doc.path: i for i, doc in enumerate(documents)}
            
            for i, doc in enumerate(documents):
                # 내부 링크 패턴 찾기 [[문서명]]
                import re
                
                link_pattern = r'\[\[([^\]]+)\]\]'
                matches = re.findall(link_pattern, doc.content)
                
                for link in matches:
                    # 링크를 실제 파일 경로로 변환
                    possible_paths = [
                        f"{link}.md",
                        link,
                        f"{link}.markdown"
                    ]
                    
                    target_index = None
                    for path in possible_paths:
                        if path in path_to_index:
                            target_index = path_to_index[path]
                            break
                    
                    if target_index is not None and target_index != i:
                        edge = GraphEdge(
                            source=f"doc_{i}",
                            target=f"doc_{target_index}",
                            weight=2.0,  # 명시적 참조는 높은 가중치
                            relationship_type="reference",
                            metadata={
                                "source_title": doc.title,
                                "target_title": documents[target_index].title,
                                "link_text": link
                            }
                        )
                        edges.append(edge)
            
            logger.info(f"참조 엣지 생성: {len(edges)}개")
            return edges
            
        except Exception as e:
            logger.error(f"참조 엣지 생성 실패: {e}")
            return []
    
    def _analyze_graph(self, nodes: List[GraphNode], edges: List[GraphEdge]) -> Dict:
        """그래프 분석"""
        try:
            if not NETWORKX_AVAILABLE:
                logger.warning("NetworkX가 설치되지 않아 그래프 분석을 건너뜁니다.")
                return {}
            
            # NetworkX 그래프 생성
            G = nx.Graph()
            
            # 노드 추가
            for node in nodes:
                G.add_node(node.id, **node.to_dict())
            
            # 엣지 추가
            for edge in edges:
                G.add_edge(edge.source, edge.target, weight=edge.weight)
            
            # 기본 메트릭 계산
            metrics = {
                "node_count": G.number_of_nodes(),
                "edge_count": G.number_of_edges(),
                "density": nx.density(G),
                "is_connected": nx.is_connected(G),
                "number_of_components": nx.number_connected_components(G),
                "average_clustering": nx.average_clustering(G),
                "transitivity": nx.transitivity(G)
            }
            
            # 연결된 그래프인 경우 추가 메트릭
            if nx.is_connected(G):
                metrics["diameter"] = nx.diameter(G)
                metrics["average_shortest_path_length"] = nx.average_shortest_path_length(G)
            
            return metrics
            
        except Exception as e:
            logger.error(f"그래프 분석 실패: {e}")
            return {}
    
    def _calculate_centrality(
        self, 
        nodes: List[GraphNode], 
        edges: List[GraphEdge]
    ) -> Dict[str, float]:
        """중심성 점수 계산"""
        try:
            if not NETWORKX_AVAILABLE:
                return {}
            
            # NetworkX 그래프 생성
            G = nx.Graph()
            for node in nodes:
                G.add_node(node.id)
            for edge in edges:
                G.add_edge(edge.source, edge.target, weight=edge.weight)
            
            # 다양한 중심성 계산
            centrality_scores = {}
            
            # 차수 중심성
            degree_centrality = nx.degree_centrality(G)
            
            # 근접 중심성 (연결된 그래프인 경우만)
            if nx.is_connected(G):
                closeness_centrality = nx.closeness_centrality(G)
                betweenness_centrality = nx.betweenness_centrality(G)
            else:
                closeness_centrality = {}
                betweenness_centrality = {}
            
            # PageRank
            pagerank = nx.pagerank(G, weight='weight')
            
            # 통합 점수 계산 (여러 중심성의 평균)
            for node_id in G.nodes():
                scores = [
                    degree_centrality.get(node_id, 0),
                    closeness_centrality.get(node_id, 0),
                    betweenness_centrality.get(node_id, 0),
                    pagerank.get(node_id, 0)
                ]
                centrality_scores[node_id] = sum(scores) / len(scores)
            
            return centrality_scores
            
        except Exception as e:
            logger.error(f"중심성 계산 실패: {e}")
            return {}
    
    def _detect_communities(
        self, 
        nodes: List[GraphNode], 
        edges: List[GraphEdge]
    ) -> List[List[str]]:
        """커뮤니티 탐지"""
        try:
            if not NETWORKX_AVAILABLE:
                return []
            
            # NetworkX 그래프 생성
            G = nx.Graph()
            for node in nodes:
                G.add_node(node.id)
            for edge in edges:
                G.add_edge(edge.source, edge.target, weight=edge.weight)
            
            # 연결 컴포넌트 기반 커뮤니티
            communities = []
            for component in nx.connected_components(G):
                if len(component) >= 2:  # 최소 2개 노드
                    communities.append(list(component))
            
            # 큰 컴포넌트의 경우 추가 분할 시도
            large_communities = []
            for community in communities:
                if len(community) > 10:
                    # 서브그래프 생성
                    subG = G.subgraph(community)
                    
                    # 모듈성 기반 분할 시도
                    try:
                        import networkx.algorithms.community as nx_comm
                        sub_communities = nx_comm.greedy_modularity_communities(subG)
                        large_communities.extend([list(c) for c in sub_communities if len(c) >= 2])
                    except:
                        large_communities.append(community)
                else:
                    large_communities.append(community)
            
            logger.info(f"커뮤니티 탐지: {len(large_communities)}개")
            return large_communities
            
        except Exception as e:
            logger.error(f"커뮤니티 탐지 실패: {e}")
            return []
    
    def _create_empty_graph(self) -> KnowledgeGraph:
        """빈 그래프 생성"""
        return KnowledgeGraph(
            nodes=[],
            edges=[],
            created_at=datetime.now()
        )
    
    def visualize_graph(
        self, 
        knowledge_graph: KnowledgeGraph,
        output_file: Optional[str] = None,
        layout: str = "spring",
        node_size_attr: str = "word_count",
        show_labels: bool = True
    ) -> bool:
        """지식 그래프 시각화"""
        try:
            if not NETWORKX_AVAILABLE or not MATPLOTLIB_AVAILABLE:
                logger.error("NetworkX 또는 Matplotlib가 설치되지 않았습니다.")
                return False
            
            if not knowledge_graph.nodes:
                logger.warning("시각화할 노드가 없습니다.")
                return False
            
            # 한글 폰트 설정
            import matplotlib.font_manager as fm
            import platform
            
            if platform.system() == 'Darwin':  # macOS
                font_path = '/System/Library/Fonts/Supplemental/AppleGothic.ttf'
                if os.path.exists(font_path):
                    font_prop = fm.FontProperties(fname=font_path)
                    plt.rcParams['font.family'] = font_prop.get_name()
                    plt.rcParams['axes.unicode_minus'] = False
            elif platform.system() == 'Windows':
                plt.rcParams['font.family'] = 'Malgun Gothic'
                plt.rcParams['axes.unicode_minus'] = False
            else:  # Linux
                plt.rcParams['font.family'] = 'DejaVu Sans'
            
            # NetworkX 그래프 생성
            G = nx.Graph()
            
            # 노드 추가
            for node in knowledge_graph.nodes:
                G.add_node(
                    node.id, 
                    title=node.title,
                    node_type=node.node_type,
                    word_count=node.word_count,
                    centrality=knowledge_graph.centrality_scores.get(node.id, 0) if knowledge_graph.centrality_scores else 0
                )
            
            # 엣지 추가
            for edge in knowledge_graph.edges:
                G.add_edge(edge.source, edge.target, weight=edge.weight, rel_type=edge.relationship_type)
            
            # 레이아웃 선택
            if layout == "spring":
                pos = nx.spring_layout(G, k=1, iterations=50)
            elif layout == "circular":
                pos = nx.circular_layout(G)
            elif layout == "kamada_kawai":
                pos = nx.kamada_kawai_layout(G)
            else:
                pos = nx.spring_layout(G)
            
            # 플롯 설정
            plt.figure(figsize=(16, 12))
            
            # 노드 타입별 색상
            node_colors = []
            node_sizes = []
            
            for node_id in G.nodes():
                node_data = G.nodes[node_id]
                
                # 노드 색상 (타입별)
                if node_data['node_type'] == 'document':
                    node_colors.append('lightblue')
                elif node_data['node_type'] == 'tag':
                    node_colors.append('lightgreen')
                else:
                    node_colors.append('lightgray')
                
                # 노드 크기 (속성 기반)
                size_value = node_data.get(node_size_attr, 1)
                if node_data['node_type'] == 'document':
                    node_sizes.append(max(100, min(1000, size_value * 2)))  # 단어 수 기반
                else:
                    node_sizes.append(max(200, min(800, size_value * 100)))  # 태그 빈도 기반
            
            # 엣지 그리기 (타입별)
            similarity_edges = [(u, v) for u, v, d in G.edges(data=True) if d.get('rel_type') == 'similarity']
            tag_edges = [(u, v) for u, v, d in G.edges(data=True) if d.get('rel_type') == 'tag']
            reference_edges = [(u, v) for u, v, d in G.edges(data=True) if d.get('rel_type') == 'reference']
            
            # 유사도 엣지 (회색, 얇음)
            if similarity_edges:
                nx.draw_networkx_edges(G, pos, edgelist=similarity_edges, 
                                     edge_color='gray', alpha=0.3, width=0.5)
            
            # 태그 엣지 (초록, 중간)
            if tag_edges:
                nx.draw_networkx_edges(G, pos, edgelist=tag_edges, 
                                     edge_color='green', alpha=0.6, width=1.0)
            
            # 참조 엣지 (빨강, 굵음)
            if reference_edges:
                nx.draw_networkx_edges(G, pos, edgelist=reference_edges, 
                                     edge_color='red', alpha=0.8, width=2.0)
            
            # 노드 그리기
            nx.draw_networkx_nodes(G, pos, node_color=node_colors, 
                                 node_size=node_sizes, alpha=0.8, linewidths=1, edgecolors='black')
            
            # 라벨 그리기
            if show_labels:
                # 제목 라벨 (짧게 자르기)
                labels = {}
                for node_id in G.nodes():
                    title = G.nodes[node_id]['title']
                    if len(title) > 20:
                        title = title[:17] + "..."
                    labels[node_id] = title
                
                # 한글 폰트 적용을 위한 설정
                if platform.system() == 'Darwin' and os.path.exists('/System/Library/Fonts/Supplemental/AppleGothic.ttf'):
                    nx.draw_networkx_labels(G, pos, labels, font_size=8, font_weight='bold', 
                                          font_family='AppleGothic')
                else:
                    nx.draw_networkx_labels(G, pos, labels, font_size=8, font_weight='bold')
            
            # 범례
            legend_elements = [
                mpatches.Patch(color='lightblue', label='문서'),
                mpatches.Patch(color='lightgreen', label='태그'),
                plt.Line2D([0], [0], color='gray', alpha=0.5, label='유사도'),
                plt.Line2D([0], [0], color='green', alpha=0.6, label='태그 연결'),
                plt.Line2D([0], [0], color='red', alpha=0.8, label='참조')
            ]
            plt.legend(handles=legend_elements, loc='upper left', bbox_to_anchor=(0, 1))
            
            # 제목 및 정보
            metrics = knowledge_graph.graph_metrics or {}
            plt.title(f'지식 그래프\n노드: {knowledge_graph.get_node_count()}개, '
                     f'엣지: {knowledge_graph.get_edge_count()}개, '
                     f'밀도: {knowledge_graph.get_density():.3f}', 
                     fontsize=14, pad=20)
            
            plt.axis('off')
            plt.tight_layout()
            
            # 저장 또는 표시
            if output_file:
                plt.savefig(output_file, dpi=300, bbox_inches='tight')
                logger.info(f"그래프 시각화 저장: {output_file}")
            else:
                plt.show()
            
            plt.close()
            return True
            
        except Exception as e:
            logger.error(f"그래프 시각화 실패: {e}")
            return False
    
    def export_graph(self, knowledge_graph: KnowledgeGraph, output_file: str) -> bool:
        """그래프를 JSON으로 내보내기"""
        try:
            export_data = {
                "graph_info": {
                    "node_count": knowledge_graph.get_node_count(),
                    "edge_count": knowledge_graph.get_edge_count(),
                    "density": knowledge_graph.get_density(),
                    "created_at": knowledge_graph.created_at.isoformat() if knowledge_graph.created_at else None,
                    "metrics": knowledge_graph.graph_metrics
                },
                "nodes": [node.to_dict() for node in knowledge_graph.nodes],
                "edges": [edge.to_dict() for edge in knowledge_graph.edges],
                "communities": knowledge_graph.communities or [],
                "centrality_scores": knowledge_graph.centrality_scores or {}
            }
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"그래프 내보내기 완료: {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"그래프 내보내기 실패: {e}")
            return False


def test_knowledge_graph():
    """지식 그래프 테스트"""
    import tempfile
    import shutil
    from ..features.advanced_search import AdvancedSearchEngine
    
    try:
        # 임시 vault 및 캐시 생성
        temp_vault = tempfile.mkdtemp()
        temp_cache = tempfile.mkdtemp()
        
        # 상호 연결된 테스트 문서들 생성
        test_docs = [
            ("tdd_basics.md", """---
tags:
  - development/tdd
  - testing/unit
---

# TDD 기본 개념

TDD는 테스트 주도 개발 방법론입니다.
[[TDD 실습]] 문서를 참고하세요.
[[리팩토링]]과 함께 사용하면 효과적입니다."""),
            
            ("tdd_practice.md", """---
tags:
  - development/tdd  
  - practice/hands-on
---

# TDD 실습

[[TDD 기본 개념]]에서 배운 내용을 실습해봅시다.
Red-Green-Refactor 사이클을 따르며 개발합니다.
[[Clean Code]] 원칙도 함께 적용해보세요."""),
            
            ("refactoring.md", """---
tags:
  - development/refactoring
  - code-quality/improvement
---

# 리팩토링

코드의 구조를 개선하는 과정입니다.
[[TDD 기본 개념]]과 함께 사용하면 안전합니다.
[[Clean Code]] 원칙에 따라 진행하세요."""),
            
            ("clean_code.md", """---
tags:
  - development/clean-code
  - best-practices/coding
---

# Clean Code

깨끗한 코드 작성의 기본 원칙들입니다.
[[TDD 실습]]과 [[리팩토링]]을 통해 달성할 수 있습니다.
가독성과 유지보수성이 중요합니다."""),
            
            ("testing_principles.md", """---
tags:
  - testing/principles
  - development/testing
---

# 테스팅 원칙

효과적인 테스트 작성을 위한 원칙들입니다.
단위 테스트, 통합 테스트, E2E 테스트가 있습니다."""),
            
            ("architecture.md", """---
tags:
  - architecture/software
  - design/patterns
---

# 소프트웨어 아키텍처

시스템의 전체적인 구조를 설계합니다.
모듈화와 의존성 관리가 핵심입니다.
확장 가능하고 유지보수가 쉬운 구조를 만드는 것이 목표입니다.""")
        ]
        
        for filename, content in test_docs:
            with open(Path(temp_vault) / filename, 'w', encoding='utf-8') as f:
                f.write(content)
        
        # 검색 엔진 초기화 및 인덱싱
        config = {
            "model": {"name": "BAAI/bge-m3"},
            "vault": {"excluded_dirs": [], "file_extensions": [".md"]},
            "graph": {
                "similarity_threshold": 0.3,
                "max_edges_per_node": 5,
                "include_tag_nodes": True,
                "min_word_count": 10  # 테스트용으로 낮춤
            }
        }
        
        search_engine = AdvancedSearchEngine(temp_vault, temp_cache, config)
        print("검색 엔진 인덱싱 중...")
        if not search_engine.build_index():
            print("❌ 인덱싱 실패")
            return False
        
        # 지식 그래프 구축기 초기화
        graph_builder = KnowledgeGraphBuilder(search_engine, config)
        
        # 지식 그래프 구축
        print("\n🕸️ 지식 그래프 구축 중...")
        knowledge_graph = graph_builder.build_graph()
        
        print(f"\n📊 지식 그래프 결과:")
        print(f"- 노드: {knowledge_graph.get_node_count()}개")
        print(f"- 엣지: {knowledge_graph.get_edge_count()}개")
        print(f"- 밀도: {knowledge_graph.get_density():.3f}")
        
        # 메트릭 출력
        if knowledge_graph.graph_metrics:
            metrics = knowledge_graph.graph_metrics
            print(f"- 연결된 그래프: {metrics.get('is_connected', False)}")
            print(f"- 컴포넌트 수: {metrics.get('number_of_components', 0)}")
            print(f"- 평균 클러스터링: {metrics.get('average_clustering', 0):.3f}")
        
        # 중심성 점수 (상위 5개)
        if knowledge_graph.centrality_scores:
            print(f"\n🎯 높은 중심성 점수 노드:")
            sorted_centrality = sorted(
                knowledge_graph.centrality_scores.items(), 
                key=lambda x: x[1], reverse=True
            )[:5]
            
            for node_id, score in sorted_centrality:
                # 노드 정보 찾기
                node = next((n for n in knowledge_graph.nodes if n.id == node_id), None)
                if node:
                    print(f"  - {node.title} ({node.node_type}): {score:.3f}")
        
        # 커뮤니티 정보
        if knowledge_graph.communities:
            print(f"\n🏘️ 탐지된 커뮤니티: {len(knowledge_graph.communities)}개")
            for i, community in enumerate(knowledge_graph.communities):
                print(f"  커뮤니티 {i+1}: {len(community)}개 노드")
                
                # 노드 이름 출력
                community_nodes = [
                    n.title for n in knowledge_graph.nodes 
                    if n.id in community
                ][:3]  # 상위 3개만
                print(f"    - {', '.join(community_nodes)}...")
        
        # 엣지 타입별 통계
        edge_types = {}
        for edge in knowledge_graph.edges:
            edge_types[edge.relationship_type] = edge_types.get(edge.relationship_type, 0) + 1
        
        print(f"\n🔗 엣지 타입별 분포:")
        for edge_type, count in edge_types.items():
            print(f"  - {edge_type}: {count}개")
        
        # JSON 내보내기 테스트
        output_file = Path(temp_cache) / "knowledge_graph.json"
        if graph_builder.export_graph(knowledge_graph, str(output_file)):
            print(f"\n💾 그래프 저장: {output_file}")
        
        # 시각화 테스트 (matplotlib 사용 가능한 경우)
        if MATPLOTLIB_AVAILABLE and NETWORKX_AVAILABLE:
            viz_file = Path(temp_cache) / "knowledge_graph.png"
            try:
                if graph_builder.visualize_graph(knowledge_graph, str(viz_file)):
                    print(f"📈 그래프 시각화 저장: {viz_file}")
            except:
                print("📈 시각화는 건너뜀 (의존성 없음)")
        
        # 정리
        shutil.rmtree(temp_vault)
        shutil.rmtree(temp_cache)
        
        print("✅ 지식 그래프 테스트 완료!")
        return True
        
    except Exception as e:
        print(f"❌ 지식 그래프 테스트 실패: {e}")
        return False


if __name__ == "__main__":
    test_knowledge_graph()