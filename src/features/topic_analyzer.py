#!/usr/bin/env python3
"""
Topic Analyzer for Vault Intelligence System V2

Sentence Transformers 임베딩을 활용한 주제 분석, 클러스터링, 지식 그래프 생성
"""

import os
import json
import logging
from typing import List, Dict, Optional, Tuple, Set, Union
from pathlib import Path
from dataclasses import dataclass, asdict
from datetime import datetime
import numpy as np
from collections import Counter, defaultdict

try:
    from sklearn.cluster import KMeans, DBSCAN, AgglomerativeClustering
    from sklearn.decomposition import PCA
    from sklearn.manifold import TSNE
    from sklearn.metrics import silhouette_score
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

try:
    import matplotlib.pyplot as plt
    import seaborn as sns
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

try:
    import networkx as nx
    NETWORKX_AVAILABLE = True
except ImportError:
    NETWORKX_AVAILABLE = False

from ..core.vault_processor import Document

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class TopicCluster:
    """주제별 클러스터"""
    id: str
    label: str
    documents: List[Document]
    centroid: Optional[np.ndarray] = None
    coherence_score: Optional[float] = None
    keywords: Optional[List[str]] = None
    representative_doc: Optional[Document] = None
    created_at: Optional[datetime] = None
    
    def get_document_count(self) -> int:
        return len(self.documents)
    
    def get_total_word_count(self) -> int:
        return sum(doc.word_count for doc in self.documents)
    
    def get_average_similarity(self) -> float:
        """클러스터 내 평균 유사도 계산"""
        if len(self.documents) < 2:
            return 1.0
        
        similarities = []
        for i, doc1 in enumerate(self.documents):
            for j, doc2 in enumerate(self.documents[i+1:], i+1):
                if doc1.embedding is not None and doc2.embedding is not None:
                    sim = np.dot(doc1.embedding, doc2.embedding)
                    similarities.append(sim)
        
        return np.mean(similarities) if similarities else 0.0
    
    def get_common_tags(self, top_k: int = 5) -> List[Tuple[str, int]]:
        """클러스터 내 공통 태그 추출"""
        tag_counter = Counter()
        for doc in self.documents:
            if doc.tags:
                tag_counter.update(doc.tags)
        return tag_counter.most_common(top_k)


@dataclass
class TopicAnalysis:
    """주제 분석 결과"""
    total_documents: int
    clusters: List[TopicCluster]
    algorithm: str
    n_clusters: int
    silhouette_score: Optional[float] = None
    analysis_date: Optional[datetime] = None
    parameters: Optional[Dict] = None
    
    def get_cluster_count(self) -> int:
        return len(self.clusters)
    
    def get_clustered_document_count(self) -> int:
        return sum(cluster.get_document_count() for cluster in self.clusters)
    
    def get_largest_cluster(self) -> Optional[TopicCluster]:
        if not self.clusters:
            return None
        return max(self.clusters, key=lambda c: c.get_document_count())
    
    def get_cluster_distribution(self) -> Dict[str, int]:
        """클러스터별 문서 수 분포"""
        return {cluster.id: cluster.get_document_count() for cluster in self.clusters}


class TopicAnalyzer:
    """주제 분석기"""
    
    def __init__(
        self,
        search_engine,
        config: Dict = None
    ):
        """
        Args:
            search_engine: AdvancedSearchEngine 인스턴스
            config: 분석 설정
        """
        self.search_engine = search_engine
        self.config = config or {}
        
        # 기본 설정
        self.default_n_clusters = self.config.get('clustering', {}).get(
            'default_n_clusters', 5
        )
        self.min_cluster_size = self.config.get('clustering', {}).get(
            'min_cluster_size', 3
        )
        self.algorithm = self.config.get('clustering', {}).get(
            'algorithm', 'kmeans'
        )
        self.random_state = self.config.get('clustering', {}).get(
            'random_state', 42
        )
        
        # 개발 관련 주요 주제들 정의
        self.development_topics = [
            "TDD", "refactoring", "AI", "Spring", "DDD", "Clean Code", 
            "Architecture", "Testing", "Docker", "Kubernetes", "React",
            "JavaScript", "Python", "Java", "Database", "API",
            "Microservices", "Design Patterns", "Agile", "DevOps",
            "Kent Beck", "Uncle Bob", "Martin Fowler"
        ]
        
        logger.info(f"주제 분석기 초기화 - 기본 클러스터 수: {self.default_n_clusters}")
    
    def analyze_topics(
        self,
        topic_query: Optional[str] = None,
        n_clusters: Optional[int] = None,
        algorithm: Optional[str] = None,
        min_cluster_size: Optional[int] = None
    ) -> TopicAnalysis:
        """주제별 클러스터링 분석"""
        try:
            if not self.search_engine.indexed:
                logger.warning("검색 엔진이 인덱싱되지 않았습니다.")
                return self._create_empty_analysis()
            
            # 설정값 사용
            n_clusters = n_clusters or self.default_n_clusters
            algorithm = algorithm or self.algorithm
            min_cluster_size = min_cluster_size or self.min_cluster_size
            
            logger.info(f"주제 분석 시작 - 알고리즘: {algorithm}, 클러스터: {n_clusters}")
            
            # 분석할 문서 필터링
            documents = self._filter_documents_for_analysis(topic_query)
            
            if len(documents) < n_clusters:
                logger.warning(f"문서가 너무 적습니다: {len(documents)} < {n_clusters}")
                n_clusters = max(1, len(documents) // 2)
            
            logger.info(f"분석 대상 문서: {len(documents)}개")
            
            # 임베딩 추출
            embeddings = self._extract_embeddings(documents)
            
            if embeddings is None or len(embeddings) == 0:
                logger.error("유효한 임베딩이 없습니다.")
                return self._create_empty_analysis()
            
            # 클러스터링 실행
            cluster_labels = self._perform_clustering(
                embeddings, algorithm, n_clusters
            )
            
            # 클러스터 생성
            clusters = self._create_clusters(documents, embeddings, cluster_labels)
            
            # 실루엣 점수 계산
            silhouette = self._calculate_silhouette_score(embeddings, cluster_labels)
            
            logger.info(f"클러스터링 완료 - {len(clusters)}개 클러스터, 실루엣: {silhouette:.3f}")
            
            # 분석 결과 생성
            analysis = TopicAnalysis(
                total_documents=len(documents),
                clusters=clusters,
                algorithm=algorithm,
                n_clusters=len(clusters),
                silhouette_score=silhouette,
                analysis_date=datetime.now(),
                parameters={
                    "n_clusters": n_clusters,
                    "min_cluster_size": min_cluster_size,
                    "topic_query": topic_query
                }
            )
            
            return analysis
            
        except Exception as e:
            logger.error(f"주제 분석 실패: {e}")
            return self._create_empty_analysis()
    
    def analyze_topics_by_predefined_subjects(self, min_docs_per_topic: int = 10) -> TopicAnalysis:
        """미리 정의된 주제들로 문서를 분류하는 주제 기반 분석"""
        try:
            logger.info(f"주제 기반 분석 시작 - {len(self.development_topics)}개 주제")
            
            topic_clusters = []
            analyzed_docs = set()  # 이미 분석된 문서들 추적
            
            # 각 주제별로 관련 문서 수집
            for topic in self.development_topics:
                logger.info(f"주제 '{topic}' 분석 중...")
                
                # collect 기능을 활용해서 관련 문서 찾기
                try:
                    from ..features.topic_collector import TopicCollector
                    collector = TopicCollector(self.search_engine, self.config)
                    collection = collector.collect_topic(topic, top_k=min_docs_per_topic * 2)
                    
                    if collection and len(collection.documents) >= min_docs_per_topic:
                        # 이미 다른 주제에 분류된 문서는 제외 (중복 방지)
                        unique_docs = []
                        for doc in collection.documents[:min_docs_per_topic * 3]:  # 여유있게 가져와서 필터링
                            if doc.path not in analyzed_docs:
                                unique_docs.append(doc)
                                analyzed_docs.add(doc.path)
                            if len(unique_docs) >= min_docs_per_topic:
                                break
                        
                        if len(unique_docs) >= min_docs_per_topic:
                            # 클러스터 생성
                            cluster = TopicCluster(
                                id=f"topic_{topic.lower().replace(' ', '_')}",
                                label=topic,
                                documents=unique_docs
                            )
                            
                            # 클러스터 분석
                            self._analyze_cluster(cluster)
                            topic_clusters.append(cluster)
                            
                            logger.info(f"주제 '{topic}': {len(unique_docs)}개 문서 발견")
                        else:
                            logger.info(f"주제 '{topic}': 문서 수 부족 ({len(unique_docs)}개 < {min_docs_per_topic}개)")
                    else:
                        logger.info(f"주제 '{topic}': 관련 문서 없음")
                        
                except Exception as e:
                    logger.warning(f"주제 '{topic}' 분석 중 오류: {e}")
                    continue
            
            # 분석 결과 생성
            total_analyzed = sum(len(cluster.documents) for cluster in topic_clusters)
            
            analysis = TopicAnalysis(
                clusters=topic_clusters,
                total_documents=total_analyzed,
                algorithm="topic-based",
                n_clusters=len(topic_clusters),  # 실제 생성된 클러스터 수
                silhouette_score=None,  # 주제 기반 분석에서는 적용되지 않음
                analysis_date=datetime.now(),  # 분석 날짜 추가
                parameters={
                    "min_docs_per_topic": min_docs_per_topic,
                    "total_topics_analyzed": len(self.development_topics),
                    "topics_found": len(topic_clusters),
                    "analysis_coverage": f"{total_analyzed}/{len(self.search_engine.documents)} ({total_analyzed/len(self.search_engine.documents)*100:.1f}%)"
                }
            )
            
            logger.info(f"주제 기반 분석 완료: {len(topic_clusters)}개 주제, {total_analyzed}개 문서")
            return analysis
            
        except Exception as e:
            logger.error(f"주제 기반 분석 실패: {e}")
            return self._create_empty_analysis()
    
    def _analyze_cluster(self, cluster: TopicCluster):
        """클러스터의 키워드, 대표 문서, 일관성 점수 등을 분석"""
        try:
            # 키워드 추출
            cluster.keywords = self._extract_cluster_keywords(cluster.documents)
            
            # 대표 문서 선정 (가장 긴 문서 또는 첫 번째 문서)
            if cluster.documents:
                # 단어 수가 가장 많은 문서를 대표 문서로 선정
                cluster.representative_doc = max(cluster.documents, key=lambda doc: doc.word_count or 0)
            
            # 생성 시간 설정
            cluster.created_at = datetime.now()
            
            # 임베딩이 있는 경우 일관성 점수 계산
            embeddings = []
            for doc in cluster.documents:
                if hasattr(doc, 'embedding') and doc.embedding is not None:
                    embeddings.append(doc.embedding)
            
            if len(embeddings) > 1:
                cluster.coherence_score = self._calculate_cluster_coherence(np.array(embeddings))
            else:
                cluster.coherence_score = 1.0
                
        except Exception as e:
            logger.warning(f"클러스터 분석 중 오류: {e}")
            # 기본값 설정
            cluster.keywords = []
            cluster.representative_doc = cluster.documents[0] if cluster.documents else None
            cluster.coherence_score = 0.0
            cluster.created_at = datetime.now()
    
    def _filter_documents_for_analysis(self, topic_query: Optional[str]) -> List[Document]:
        """분석할 문서 필터링"""
        documents = self.search_engine.documents
        
        if topic_query:
            # 주제 관련 문서만 필터링
            filtered_docs = []
            query_lower = topic_query.lower()
            
            for doc in documents:
                # 제목, 태그, 내용에서 주제 검색
                if (query_lower in doc.title.lower() or
                    any(query_lower in tag.lower() for tag in doc.tags) or
                    query_lower in doc.content.lower()):
                    filtered_docs.append(doc)
            
            documents = filtered_docs
            logger.info(f"주제 '{topic_query}' 관련 문서: {len(documents)}개")
        
        # 임베딩이 있는 문서만
        valid_docs = []
        total_checked = 0
        has_embedding_attr = 0
        embedding_not_none = 0
        
        for doc in documents:
            total_checked += 1
            if hasattr(doc, 'embedding'):
                has_embedding_attr += 1
                if doc.embedding is not None:
                    embedding_not_none += 1
                    # numpy 배열인지 확인하고 0이 아닌지 체크
                    if isinstance(doc.embedding, np.ndarray) and doc.embedding.size > 0:
                        if not np.allclose(doc.embedding, 0):
                            valid_docs.append(doc)
                    elif hasattr(doc.embedding, '__len__') and len(doc.embedding) > 0:
                        # 리스트나 다른 형태의 배열인 경우
                        valid_docs.append(doc)
        
        logger.info(f"임베딩 체크 결과: 전체={total_checked}, embedding 속성={has_embedding_attr}, "
                   f"None이 아님={embedding_not_none}, 유효={len(valid_docs)}")
        
        logger.info(f"유효한 임베딩을 가진 문서: {len(valid_docs)}개")
        return valid_docs
    
    def _extract_embeddings(self, documents: List[Document]) -> Optional[np.ndarray]:
        """문서들의 임베딩 추출"""
        try:
            embeddings = []
            for doc in documents:
                if doc.embedding is not None:
                    embeddings.append(doc.embedding)
                else:
                    # 빈 임베딩으로 대체
                    empty_embedding = np.zeros(self.search_engine.engine.embedding_dimension)
                    embeddings.append(empty_embedding)
            
            return np.array(embeddings) if embeddings else None
            
        except Exception as e:
            logger.error(f"임베딩 추출 실패: {e}")
            return None
    
    def _perform_clustering(
        self,
        embeddings: np.ndarray,
        algorithm: str,
        n_clusters: int
    ) -> np.ndarray:
        """클러스터링 실행"""
        try:
            if not SKLEARN_AVAILABLE:
                logger.error("scikit-learn이 설치되지 않았습니다.")
                return np.zeros(len(embeddings))
            
            if algorithm.lower() == "kmeans":
                clusterer = KMeans(
                    n_clusters=n_clusters,
                    random_state=self.random_state,
                    n_init=10
                )
            elif algorithm.lower() == "dbscan":
                # DBSCAN의 경우 eps 자동 추정
                eps = self._estimate_dbscan_eps(embeddings)
                clusterer = DBSCAN(eps=eps, min_samples=self.min_cluster_size)
            elif algorithm.lower() == "hierarchical":
                clusterer = AgglomerativeClustering(
                    n_clusters=n_clusters,
                    linkage='ward'
                )
            else:
                logger.warning(f"알 수 없는 알고리즘: {algorithm}, KMeans 사용")
                clusterer = KMeans(
                    n_clusters=n_clusters,
                    random_state=self.random_state
                )
            
            cluster_labels = clusterer.fit_predict(embeddings)
            logger.info(f"클러스터링 완료: {len(set(cluster_labels))}개 클러스터")
            
            return cluster_labels
            
        except Exception as e:
            logger.error(f"클러스터링 실행 실패: {e}")
            return np.zeros(len(embeddings))
    
    def _estimate_dbscan_eps(self, embeddings: np.ndarray) -> float:
        """DBSCAN eps 파라미터 자동 추정"""
        try:
            from sklearn.neighbors import NearestNeighbors
            
            # k-distance 그래프로 eps 추정
            k = min(4, len(embeddings) - 1)
            nbrs = NearestNeighbors(n_neighbors=k).fit(embeddings)
            distances, _ = nbrs.kneighbors(embeddings)
            
            # k번째 가까운 이웃까지의 평균 거리
            k_distances = np.sort(distances[:, k-1])
            
            # 급격한 변화가 있는 지점을 eps로 사용
            # 간단한 방법: 상위 20% 지점
            eps = k_distances[int(len(k_distances) * 0.8)]
            
            logger.info(f"DBSCAN eps 추정값: {eps:.4f}")
            return eps
            
        except Exception as e:
            logger.error(f"DBSCAN eps 추정 실패: {e}")
            return 0.5  # 기본값
    
    def _create_clusters(
        self,
        documents: List[Document],
        embeddings: np.ndarray,
        cluster_labels: np.ndarray
    ) -> List[TopicCluster]:
        """클러스터 객체 생성"""
        try:
            clusters = []
            unique_labels = set(cluster_labels)
            
            for label in unique_labels:
                if label == -1:  # DBSCAN 노이즈
                    continue
                
                # 클러스터에 속한 문서들
                cluster_indices = np.where(cluster_labels == label)[0]
                cluster_docs = [documents[i] for i in cluster_indices]
                cluster_embeddings = embeddings[cluster_indices]
                
                # 최소 크기 확인
                if len(cluster_docs) < self.min_cluster_size:
                    continue
                
                # 클러스터 중심 계산
                centroid = np.mean(cluster_embeddings, axis=0)
                
                # 대표 문서 선정 (중심에 가장 가까운 문서)
                representative_doc = self._find_representative_document(
                    cluster_docs, cluster_embeddings, centroid
                )
                
                # 클러스터 라벨 생성
                cluster_label = self._generate_cluster_label(cluster_docs, representative_doc)
                
                # 키워드 추출
                keywords = self._extract_cluster_keywords(cluster_docs)
                
                # 일관성 점수 계산
                coherence_score = self._calculate_cluster_coherence(cluster_embeddings)
                
                cluster = TopicCluster(
                    id=f"cluster_{label}",
                    label=cluster_label,
                    documents=cluster_docs,
                    centroid=centroid,
                    coherence_score=coherence_score,
                    keywords=keywords,
                    representative_doc=representative_doc,
                    created_at=datetime.now()
                )
                
                clusters.append(cluster)
            
            # 크기순으로 정렬
            clusters.sort(key=lambda c: c.get_document_count(), reverse=True)
            
            return clusters
            
        except Exception as e:
            logger.error(f"클러스터 생성 실패: {e}")
            return []
    
    def _find_representative_document(
        self,
        docs: List[Document],
        embeddings: np.ndarray,
        centroid: np.ndarray
    ) -> Document:
        """대표 문서 찾기 (중심에 가장 가까운 문서)"""
        try:
            similarities = np.dot(embeddings, centroid)
            best_idx = np.argmax(similarities)
            return docs[best_idx]
        except Exception as e:
            logger.error(f"대표 문서 찾기 실패: {e}")
            return docs[0] if docs else None
    
    def _generate_cluster_label(
        self,
        docs: List[Document],
        representative_doc: Document
    ) -> str:
        """클러스터 라벨 생성"""
        try:
            # 1순위: 대표 문서 제목
            if representative_doc and representative_doc.title:
                return representative_doc.title[:50]
            
            # 2순위: 가장 빈번한 태그
            tag_counter = Counter()
            for doc in docs:
                if doc.tags:
                    tag_counter.update(doc.tags)
            
            if tag_counter:
                most_common_tag = tag_counter.most_common(1)[0][0]
                return f"주제: {most_common_tag}"
            
            # 3순위: 첫 번째 문서 제목
            if docs and docs[0].title:
                return docs[0].title[:50]
            
            return "미분류 주제"
            
        except Exception as e:
            logger.error(f"클러스터 라벨 생성 실패: {e}")
            return "알 수 없는 주제"
    
    def _extract_cluster_keywords(self, docs: List[Document]) -> List[str]:
        """클러스터 키워드 추출"""
        try:
            # 태그 기반 키워드 추출
            tag_counter = Counter()
            for doc in docs:
                if doc.tags:
                    tag_counter.update(doc.tags)
            
            keywords = [tag for tag, count in tag_counter.most_common(10)]
            
            # 제목에서 공통 단어 추출
            title_words = []
            for doc in docs:
                if doc.title:
                    words = doc.title.split()
                    title_words.extend([w.lower().strip('.,!?') for w in words if len(w) > 2])
            
            word_counter = Counter(title_words)
            common_words = [word for word, count in word_counter.most_common(5) if count > 1]
            
            keywords.extend(common_words)
            
            return list(set(keywords))[:15]  # 중복 제거 후 상위 15개
            
        except Exception as e:
            logger.error(f"키워드 추출 실패: {e}")
            return []
    
    def _calculate_cluster_coherence(self, embeddings: np.ndarray) -> float:
        """클러스터 일관성 점수 계산"""
        try:
            if len(embeddings) < 2:
                return 1.0
            
            # 클러스터 내 평균 유사도
            similarities = []
            for i in range(len(embeddings)):
                for j in range(i + 1, len(embeddings)):
                    sim = np.dot(embeddings[i], embeddings[j])
                    similarities.append(sim)
            
            return np.mean(similarities) if similarities else 0.0
            
        except Exception as e:
            logger.error(f"일관성 점수 계산 실패: {e}")
            return 0.0
    
    def _calculate_silhouette_score(
        self,
        embeddings: np.ndarray,
        labels: np.ndarray
    ) -> float:
        """실루엣 점수 계산"""
        try:
            if not SKLEARN_AVAILABLE:
                return 0.0
            
            if len(set(labels)) < 2:
                return 0.0
            
            return silhouette_score(embeddings, labels)
            
        except Exception as e:
            logger.error(f"실루엣 점수 계산 실패: {e}")
            return 0.0
    
    def _create_empty_analysis(self) -> TopicAnalysis:
        """빈 분석 결과 생성"""
        return TopicAnalysis(
            total_documents=0,
            clusters=[],
            algorithm=self.algorithm,
            n_clusters=0,
            analysis_date=datetime.now()
        )
    
    def visualize_clusters(
        self,
        analysis: TopicAnalysis,
        output_file: Optional[str] = None,
        method: str = "pca"
    ) -> bool:
        """클러스터 시각화"""
        try:
            if not SKLEARN_AVAILABLE:
                logger.error("scikit-learn이 설치되지 않았습니다.")
                return False
            
            if not MATPLOTLIB_AVAILABLE:
                logger.error("matplotlib이 설치되지 않았습니다.")
                return False
            
            if not analysis.clusters:
                logger.warning("시각화할 클러스터가 없습니다.")
                return False
            
            # 모든 임베딩과 라벨 수집
            all_embeddings = []
            all_labels = []
            all_titles = []
            
            for i, cluster in enumerate(analysis.clusters):
                for doc in cluster.documents:
                    if doc.embedding is not None:
                        all_embeddings.append(doc.embedding)
                        all_labels.append(i)
                        all_titles.append(doc.title[:30])
            
            if not all_embeddings:
                logger.warning("시각화할 임베딩이 없습니다.")
                return False
            
            embeddings_array = np.array(all_embeddings)
            
            # 차원 축소
            if method.lower() == "pca":
                reducer = PCA(n_components=2, random_state=self.random_state)
            elif method.lower() == "tsne":
                reducer = TSNE(n_components=2, random_state=self.random_state, perplexity=min(30, len(embeddings_array)-1))
            else:
                logger.warning(f"알 수 없는 차원축소 방법: {method}, PCA 사용")
                reducer = PCA(n_components=2, random_state=self.random_state)
            
            reduced_embeddings = reducer.fit_transform(embeddings_array)
            
            # 플롯 생성
            plt.figure(figsize=(12, 8))
            
            colors = plt.cm.Set3(np.linspace(0, 1, len(analysis.clusters)))
            
            for i, cluster in enumerate(analysis.clusters):
                cluster_points = reduced_embeddings[np.array(all_labels) == i]
                if len(cluster_points) > 0:
                    plt.scatter(
                        cluster_points[:, 0],
                        cluster_points[:, 1],
                        c=[colors[i]],
                        label=f"{cluster.label} ({len(cluster.documents)}개)",
                        alpha=0.7,
                        s=50
                    )
            
            plt.title(f'문서 클러스터 시각화 ({method.upper()})\n'
                     f'총 {analysis.total_documents}개 문서, {len(analysis.clusters)}개 클러스터')
            plt.xlabel(f'{method.upper()} Component 1')
            plt.ylabel(f'{method.upper()} Component 2')
            plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
            plt.grid(True, alpha=0.3)
            plt.tight_layout()
            
            if output_file:
                plt.savefig(output_file, dpi=300, bbox_inches='tight')
                logger.info(f"클러스터 시각화 저장: {output_file}")
            else:
                plt.show()
            
            plt.close()
            return True
            
        except Exception as e:
            logger.error(f"클러스터 시각화 실패: {e}")
            return False
    
    def export_analysis(self, analysis: TopicAnalysis, output_file: str) -> bool:
        """분석 결과를 파일로 내보내기"""
        try:
            export_data = {
                "analysis_info": {
                    "total_documents": analysis.total_documents,
                    "cluster_count": analysis.get_cluster_count(),
                    "clustered_documents": analysis.get_clustered_document_count(),
                    "algorithm": analysis.algorithm,
                    "silhouette_score": analysis.silhouette_score,
                    "analysis_date": analysis.analysis_date.isoformat() if analysis.analysis_date else None,
                    "parameters": analysis.parameters
                },
                "clusters": []
            }
            
            for cluster in analysis.clusters:
                cluster_data = {
                    "id": cluster.id,
                    "label": cluster.label,
                    "document_count": cluster.get_document_count(),
                    "total_word_count": cluster.get_total_word_count(),
                    "coherence_score": cluster.coherence_score,
                    "keywords": cluster.keywords,
                    "representative_document": {
                        "path": cluster.representative_doc.path,
                        "title": cluster.representative_doc.title
                    } if cluster.representative_doc else None,
                    "common_tags": cluster.get_common_tags(10),
                    "average_similarity": cluster.get_average_similarity(),
                    "documents": [
                        {
                            "path": doc.path,
                            "title": doc.title,
                            "word_count": doc.word_count,
                            "tags": doc.tags,
                            "modified_at": doc.modified_at.isoformat()
                        }
                        for doc in cluster.documents
                    ]
                }
                export_data["clusters"].append(cluster_data)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"주제 분석 결과 내보내기 완료: {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"분석 결과 내보내기 실패: {e}")
            return False
    
    def export_markdown_report(self, analysis: TopicAnalysis, output_file: str) -> bool:
        """분석 결과를 마크다운 보고서로 내보내기"""
        try:
            from datetime import datetime
            
            # 마크다운 보고서 생성
            markdown_content = []
            
            # 헤더
            markdown_content.append("# 📊 Vault 주제 분석 보고서")
            markdown_content.append("")
            markdown_content.append(f"**생성일시**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            markdown_content.append("")
            
            # 전체 통계
            markdown_content.append("## 📈 전체 통계")
            markdown_content.append("")
            markdown_content.append(f"- **분석 문서 수**: {analysis.total_documents:,}개")
            markdown_content.append(f"- **발견 클러스터 수**: {analysis.get_cluster_count()}개")
            markdown_content.append(f"- **클러스터링 알고리즘**: {analysis.algorithm}")
            if analysis.silhouette_score is not None:
                markdown_content.append(f"- **실루엣 점수**: {analysis.silhouette_score:.3f}")
            markdown_content.append("")
            
            # 클러스터별 분포
            if analysis.clusters:
                markdown_content.append("## 📊 클러스터 분포")
                markdown_content.append("")
                markdown_content.append("| 순위 | 클러스터명 | 문서 수 | 비율 | 일관성 점수 |")
                markdown_content.append("|------|------------|---------|------|-------------|")
                
                for i, cluster in enumerate(analysis.clusters, 1):
                    percentage = (cluster.get_document_count() / analysis.total_documents) * 100
                    coherence = f"{cluster.coherence_score:.3f}" if cluster.coherence_score else "N/A"
                    cluster_name = cluster.label[:50] + ("..." if len(cluster.label) > 50 else "")
                    markdown_content.append(
                        f"| {i} | {cluster_name} | {cluster.get_document_count():,} | {percentage:.1f}% | {coherence} |"
                    )
                
                markdown_content.append("")
                
                # 각 클러스터 상세 정보
                markdown_content.append("## 🏷️ 클러스터 상세 분석")
                markdown_content.append("")
                
                for i, cluster in enumerate(analysis.clusters, 1):
                    markdown_content.append(f"### {i}. {cluster.label}")
                    markdown_content.append("")
                    markdown_content.append(f"**📊 기본 정보**")
                    markdown_content.append(f"- 문서 수: **{cluster.get_document_count():,}개**")
                    markdown_content.append(f"- 총 단어 수: {cluster.get_total_word_count():,}개")
                    if cluster.coherence_score is not None:
                        markdown_content.append(f"- 일관성 점수: {cluster.coherence_score:.3f}")
                    markdown_content.append("")
                    
                    # 주요 키워드
                    if cluster.keywords:
                        markdown_content.append("**🔑 주요 키워드**")
                        keywords_str = ", ".join([f"`{kw}`" for kw in cluster.keywords[:10]])
                        markdown_content.append(f"{keywords_str}")
                        markdown_content.append("")
                    
                    # 대표 문서
                    if cluster.representative_doc:
                        markdown_content.append("**📄 대표 문서**")
                        markdown_content.append(f"- [{cluster.representative_doc.title}]({cluster.representative_doc.path})")
                        markdown_content.append("")
                    
                    # 공통 태그
                    common_tags = cluster.get_common_tags(10)
                    if common_tags:
                        markdown_content.append("**🏷️ 공통 태그**")
                        tags_info = []
                        for tag, count in common_tags:
                            tags_info.append(f"`{tag}` ({count})")
                        markdown_content.append(", ".join(tags_info))
                        markdown_content.append("")
                    
                    # 문서 목록 (상위 10개)
                    markdown_content.append("**📚 주요 문서들** (상위 10개)")
                    markdown_content.append("")
                    for j, doc in enumerate(cluster.documents[:10], 1):
                        word_count = f"({doc.word_count}단어)" if doc.word_count else ""
                        markdown_content.append(f"{j}. [{doc.title}]({doc.path}) {word_count}")
                    
                    if len(cluster.documents) > 10:
                        remaining = len(cluster.documents) - 10
                        markdown_content.append(f"... 외 {remaining}개 문서")
                    
                    markdown_content.append("")
                    markdown_content.append("---")
                    markdown_content.append("")
            
            # 분석 매개변수
            if analysis.parameters:
                markdown_content.append("## ⚙️ 분석 매개변수")
                markdown_content.append("")
                for key, value in analysis.parameters.items():
                    markdown_content.append(f"- **{key}**: {value}")
                markdown_content.append("")
            
            # 파일에 저장
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(markdown_content))
            
            logger.info(f"마크다운 보고서 저장 완료: {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"마크다운 보고서 생성 실패: {e}")
            return False


def test_topic_analyzer():
    """주제 분석기 테스트"""
    import tempfile
    import shutil
    from ..features.advanced_search import AdvancedSearchEngine
    
    try:
        # 임시 vault 및 캐시 생성
        temp_vault = tempfile.mkdtemp()
        temp_cache = tempfile.mkdtemp()
        
        # 다양한 주제의 테스트 문서들 생성
        test_docs = [
            ("tdd1.md", "# TDD 기본 개념\n\nTDD는 테스트 주도 개발 방법론입니다.\nRed-Green-Refactor 사이클을 따릅니다."),
            ("tdd2.md", "# TDD 실습\n\n테스트를 먼저 작성하고 구현하는 방법을 연습합니다.\n단위 테스트와 통합 테스트를 작성합니다."),
            ("refactoring1.md", "# 리팩토링 기법\n\n코드의 구조를 개선하는 다양한 방법들입니다.\n메서드 추출, 클래스 분리 등의 기법이 있습니다."),
            ("refactoring2.md", "# 안전한 리팩토링\n\n테스트가 있을 때 안전하게 리팩토링할 수 있습니다.\n회귀 버그를 방지하는 것이 중요합니다."),
            ("clean_code1.md", "# Clean Code 원칙\n\n깨끗한 코드 작성의 기본 원칙들입니다.\n의미 있는 이름, 작은 함수, 명확한 의도 표현이 중요합니다."),
            ("clean_code2.md", "# 코드 품질\n\n좋은 코드는 읽기 쉽고 이해하기 쉬워야 합니다.\n주석보다는 코드 자체가 설명되어야 합니다."),
            ("architecture1.md", "# 소프트웨어 아키텍처\n\n시스템의 전체적인 구조를 설계하는 방법입니다.\n계층화, 모듈화, 의존성 관리가 핵심입니다."),
            ("architecture2.md", "# 마이크로서비스 아키텍처\n\n작은 서비스들로 시스템을 구성하는 패턴입니다.\n독립적 배포와 확장이 가능합니다.")
        ]
        
        for filename, content in test_docs:
            with open(Path(temp_vault) / filename, 'w', encoding='utf-8') as f:
                f.write(content)
        
        # 검색 엔진 초기화 및 인덱싱
        config = {
            "model": {"name": "paraphrase-multilingual-mpnet-base-v2"},
            "vault": {"excluded_dirs": [], "file_extensions": [".md"]},
            "clustering": {
                "default_n_clusters": 4,
                "min_cluster_size": 2,
                "algorithm": "kmeans"
            }
        }
        
        search_engine = AdvancedSearchEngine(temp_vault, temp_cache, config)
        print("검색 엔진 인덱싱 중...")
        if not search_engine.build_index():
            print("❌ 인덱싱 실패")
            return False
        
        # 주제 분석기 초기화
        analyzer = TopicAnalyzer(search_engine, config)
        
        # 전체 문서 주제 분석
        print("\n🔍 전체 문서 주제 분석 중...")
        analysis = analyzer.analyze_topics(n_clusters=4)
        
        print(f"\n📊 주제 분석 결과:")
        print(f"- 총 문서: {analysis.total_documents}개")
        print(f"- 클러스터: {analysis.get_cluster_count()}개")
        print(f"- 실루엣 점수: {analysis.silhouette_score:.3f}")
        
        # 클러스터 세부 정보
        for i, cluster in enumerate(analysis.clusters):
            print(f"\n📁 클러스터 {i+1}: {cluster.label}")
            print(f"   문서 수: {cluster.get_document_count()}개")
            print(f"   일관성: {cluster.coherence_score:.3f}")
            print(f"   키워드: {cluster.keywords[:5]}")
            print(f"   문서들:")
            for doc in cluster.documents:
                print(f"     - {doc.path}")
        
        # 특정 주제 분석
        print(f"\n🔍 'TDD' 주제 분석 중...")
        tdd_analysis = analyzer.analyze_topics(topic_query="TDD", n_clusters=2)
        
        print(f"\n📊 TDD 주제 분석 결과:")
        print(f"- TDD 관련 문서: {tdd_analysis.total_documents}개")
        print(f"- 클러스터: {tdd_analysis.get_cluster_count()}개")
        
        for cluster in tdd_analysis.clusters:
            print(f"  - {cluster.label}: {cluster.get_document_count()}개 문서")
        
        # 결과 내보내기 테스트
        output_file = Path(temp_cache) / "topic_analysis.json"
        if analyzer.export_analysis(analysis, str(output_file)):
            print(f"\n💾 분석 결과 저장: {output_file}")
        
        # 시각화 테스트 (matplotlib 사용 가능한 경우)
        if SKLEARN_AVAILABLE:
            viz_file = Path(temp_cache) / "cluster_visualization.png"
            try:
                if analyzer.visualize_clusters(analysis, str(viz_file)):
                    print(f"📈 클러스터 시각화 저장: {viz_file}")
            except:
                print("📈 시각화는 건너뜀 (matplotlib 없음)")
        
        # 정리
        shutil.rmtree(temp_vault)
        shutil.rmtree(temp_cache)
        
        print("✅ 주제 분석기 테스트 완료!")
        return True
        
    except Exception as e:
        print(f"❌ 주제 분석기 테스트 실패: {e}")
        return False


if __name__ == "__main__":
    test_topic_analyzer()