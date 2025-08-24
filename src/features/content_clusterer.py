#!/usr/bin/env python3
"""
Content Clusterer for Vault Intelligence System V2 - Phase 9

BGE-M3 임베딩 기반 의미적 문서 클러스터링 시스템
"""

import os
import logging
import numpy as np
from typing import List, Dict, Optional, Tuple, Union
from pathlib import Path
from dataclasses import dataclass, asdict
from datetime import datetime
from collections import Counter, defaultdict

try:
    from sklearn.cluster import KMeans, DBSCAN, AgglomerativeClustering
    from sklearn.metrics import silhouette_score
    from sklearn.preprocessing import StandardScaler
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

from ..core.vault_processor import Document
from ..core.sentence_transformer_engine import SentenceTransformerEngine
from ..core.embedding_cache import EmbeddingCache

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class DocumentCluster:
    """문서 클러스터"""
    id: str
    label: str
    documents: List[Document]
    representative_doc: Optional[Document] = None
    keywords: List[str] = None
    similarity_score: float = 0.0
    centroid: Optional[np.ndarray] = None
    size: int = 0
    
    def __post_init__(self):
        self.size = len(self.documents)


@dataclass
class ClusteringResult:
    """클러스터링 결과"""
    clusters: List[DocumentCluster]
    algorithm: str
    n_clusters: int
    silhouette_score: float
    parameters: Dict
    total_documents: int
    timestamp: datetime
    
    def get_cluster_count(self) -> int:
        """클러스터 수 반환"""
        return len(self.clusters)
    
    def get_largest_cluster(self) -> Optional[DocumentCluster]:
        """가장 큰 클러스터 반환"""
        if not self.clusters:
            return None
        return max(self.clusters, key=lambda x: x.size)
    
    def get_cluster_summary(self) -> Dict:
        """클러스터링 요약 정보"""
        return {
            "algorithm": self.algorithm,
            "total_documents": self.total_documents,
            "n_clusters": self.n_clusters,
            "silhouette_score": self.silhouette_score,
            "cluster_sizes": [cluster.size for cluster in self.clusters],
            "avg_cluster_size": sum(cluster.size for cluster in self.clusters) / len(self.clusters),
            "timestamp": self.timestamp.isoformat()
        }


class ContentClusterer:
    """BGE-M3 기반 의미적 문서 클러스터링"""
    
    def __init__(self, 
                 embedding_engine: SentenceTransformerEngine,
                 embedding_cache: EmbeddingCache,
                 config: dict):
        """
        ContentClusterer 초기화
        
        Args:
            embedding_engine: BGE-M3 임베딩 엔진
            embedding_cache: 임베딩 캐시
            config: 설정 정보
        """
        if not SKLEARN_AVAILABLE:
            raise ImportError("scikit-learn이 필요합니다: pip install scikit-learn")
            
        self.embedding_engine = embedding_engine
        self.embedding_cache = embedding_cache
        self.config = config
        
        # 클러스터링 설정 로드
        clustering_config = config.get('clustering', {})
        self.default_algorithm = clustering_config.get('default_algorithm', 'kmeans')
        self.auto_k = clustering_config.get('auto_k', True)
        self.min_cluster_size = clustering_config.get('min_cluster_size', 2)
        self.max_clusters = clustering_config.get('max_clusters', 20)
        self.silhouette_threshold = clustering_config.get('silhouette_threshold', 0.5)
        
        logger.info(f"ContentClusterer 초기화 완료 - 기본 알고리즘: {self.default_algorithm}")
    
    def cluster_documents(self,
                         documents: List[Document],
                         algorithm: str = None,
                         n_clusters: int = None,
                         **kwargs) -> ClusteringResult:
        """
        문서 클러스터링 수행
        
        Args:
            documents: 클러스터링할 문서 리스트
            algorithm: 클러스터링 알고리즘 ('kmeans', 'dbscan', 'agglomerative')
            n_clusters: 클러스터 수 (None이면 자동 결정)
            **kwargs: 알고리즘별 추가 파라미터
            
        Returns:
            ClusteringResult: 클러스터링 결과
        """
        if len(documents) < self.min_cluster_size:
            logger.warning(f"문서 수가 부족합니다 (최소 {self.min_cluster_size}개 필요): {len(documents)}개")
            return self._create_single_cluster(documents)
        
        algorithm = algorithm or self.default_algorithm
        logger.info(f"문서 클러스터링 시작: {len(documents)}개 문서, {algorithm} 알고리즘")
        
        # 1. 임베딩 벡터 준비
        embeddings = self._get_document_embeddings(documents)
        
        # 2. 클러스터 수 결정 (필요한 경우)
        if n_clusters is None and algorithm in ['kmeans', 'agglomerative']:
            n_clusters = self._determine_optimal_clusters(embeddings, documents)
            logger.info(f"자동 결정된 클러스터 수: {n_clusters}")
        
        # 3. 클러스터링 수행
        cluster_labels = self._perform_clustering(embeddings, algorithm, n_clusters, **kwargs)
        
        # 4. 클러스터 생성 및 분석
        clusters = self._create_clusters(documents, embeddings, cluster_labels)
        
        # 5. 실루엣 점수 계산
        silhouette_avg = self._calculate_silhouette_score(embeddings, cluster_labels)
        
        # 6. 결과 반환
        result = ClusteringResult(
            clusters=clusters,
            algorithm=algorithm,
            n_clusters=len(clusters),
            silhouette_score=silhouette_avg,
            parameters=kwargs,
            total_documents=len(documents),
            timestamp=datetime.now()
        )
        
        logger.info(f"클러스터링 완료: {len(clusters)}개 클러스터, 실루엣 점수: {silhouette_avg:.3f}")
        return result
    
    def _get_document_embeddings(self, documents: List[Document]) -> np.ndarray:
        """문서들의 임베딩 벡터 가져오기"""
        embeddings = []
        
        logger.info("문서 임베딩 벡터 로딩 중...")
        for doc in documents:
            try:
                # 캐시에서 임베딩 조회
                cached_embedding = self.embedding_cache.get_embedding(doc.path)
                if cached_embedding:
                    embeddings.append(cached_embedding.embedding)
                else:
                    # 임베딩이 없는 경우 생성
                    logger.warning(f"임베딩이 없는 문서: {doc.path}")
                    embedding = self.embedding_engine.encode([doc.content])[0]
                    embeddings.append(embedding)
                    
            except Exception as e:
                logger.error(f"임베딩 로딩 실패 ({doc.path}): {e}")
                # 기본값으로 영벡터 사용
                embeddings.append(np.zeros(self.embedding_engine.model.get_sentence_embedding_dimension()))
        
        return np.array(embeddings)
    
    def _determine_optimal_clusters(self, embeddings: np.ndarray, documents: List[Document]) -> int:
        """최적 클러스터 수 자동 결정 (Elbow method + Silhouette analysis)"""
        n_docs = len(documents)
        max_k = min(self.max_clusters, n_docs // 2)  # 최대 클러스터 수 제한
        
        if max_k < 2:
            return 2
        
        logger.info(f"최적 클러스터 수 결정 중 (2~{max_k})...")
        
        # K-means로 여러 k값 테스트
        silhouette_scores = []
        inertias = []
        k_range = range(2, max_k + 1)
        
        for k in k_range:
            try:
                kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
                cluster_labels = kmeans.fit_predict(embeddings)
                
                # 실루엣 점수 계산
                silhouette_avg = silhouette_score(embeddings, cluster_labels)
                silhouette_scores.append(silhouette_avg)
                inertias.append(kmeans.inertia_)
                
                logger.debug(f"k={k}: 실루엣 점수 {silhouette_avg:.3f}")
                
            except Exception as e:
                logger.warning(f"k={k}에서 클러스터링 실패: {e}")
                silhouette_scores.append(0.0)
                inertias.append(float('inf'))
        
        # 최고 실루엣 점수를 가진 k 선택
        if silhouette_scores:
            best_k_idx = np.argmax(silhouette_scores)
            best_k = k_range[best_k_idx]
            best_score = silhouette_scores[best_k_idx]
            
            logger.info(f"최적 클러스터 수: {best_k} (실루엣 점수: {best_score:.3f})")
            
            # 임계값 이하면 기본값 사용
            if best_score < self.silhouette_threshold:
                logger.warning(f"실루엣 점수가 낮음 ({best_score:.3f} < {self.silhouette_threshold}), 기본값 사용")
                return min(5, max_k)  # 기본값
            
            return best_k
        
        return min(5, max_k)  # 기본값
    
    def _perform_clustering(self, embeddings: np.ndarray, algorithm: str, n_clusters: int, **kwargs) -> np.ndarray:
        """실제 클러스터링 수행"""
        logger.info(f"{algorithm} 클러스터링 수행 중...")
        
        if algorithm == 'kmeans':
            clusterer = KMeans(
                n_clusters=n_clusters, 
                random_state=42, 
                n_init=10,
                **kwargs
            )
        elif algorithm == 'dbscan':
            eps = kwargs.get('eps', 0.5)
            min_samples = kwargs.get('min_samples', 5)
            clusterer = DBSCAN(eps=eps, min_samples=min_samples, **kwargs)
        elif algorithm == 'agglomerative':
            clusterer = AgglomerativeClustering(n_clusters=n_clusters, **kwargs)
        else:
            raise ValueError(f"지원하지 않는 알고리즘: {algorithm}")
        
        try:
            cluster_labels = clusterer.fit_predict(embeddings)
            return cluster_labels
        except Exception as e:
            logger.error(f"클러스터링 실패: {e}")
            # 기본값으로 모든 문서를 하나의 클러스터에 할당
            return np.zeros(len(embeddings), dtype=int)
    
    def _create_clusters(self, documents: List[Document], embeddings: np.ndarray, cluster_labels: np.ndarray) -> List[DocumentCluster]:
        """클러스터 객체 생성 및 분석"""
        clusters_dict = defaultdict(list)
        embeddings_dict = defaultdict(list)
        
        # 클러스터별로 문서와 임베딩 그룹화
        for doc, embedding, label in zip(documents, embeddings, cluster_labels):
            if label != -1:  # DBSCAN의 노이즈 포인트 제외
                clusters_dict[label].append(doc)
                embeddings_dict[label].append(embedding)
        
        clusters = []
        for cluster_id, cluster_docs in clusters_dict.items():
            cluster_embeddings = np.array(embeddings_dict[cluster_id])
            
            # 클러스터 중심점 계산
            centroid = np.mean(cluster_embeddings, axis=0)
            
            # 대표 문서 선정 (중심점에 가장 가까운 문서)
            distances = [np.linalg.norm(emb - centroid) for emb in cluster_embeddings]
            representative_idx = np.argmin(distances)
            representative_doc = cluster_docs[representative_idx]
            
            # 클러스터 내 유사도 계산
            similarity_score = self._calculate_cluster_similarity(cluster_embeddings)
            
            # 키워드 추출
            keywords = self._extract_cluster_keywords(cluster_docs)
            
            # 클러스터 라벨 생성
            label = self._generate_cluster_label(representative_doc, keywords)
            
            cluster = DocumentCluster(
                id=f"cluster_{cluster_id}",
                label=label,
                documents=cluster_docs,
                representative_doc=representative_doc,
                keywords=keywords,
                similarity_score=similarity_score,
                centroid=centroid
            )
            
            clusters.append(cluster)
        
        # 클러스터 크기순 정렬
        clusters.sort(key=lambda x: x.size, reverse=True)
        
        return clusters
    
    def _calculate_silhouette_score(self, embeddings: np.ndarray, cluster_labels: np.ndarray) -> float:
        """실루엣 점수 계산"""
        try:
            # 노이즈 포인트(-1) 제거
            valid_indices = cluster_labels != -1
            if np.sum(valid_indices) < 2:
                return 0.0
            
            valid_embeddings = embeddings[valid_indices]
            valid_labels = cluster_labels[valid_indices]
            
            # 유효한 클러스터가 2개 이상인지 확인
            unique_labels = np.unique(valid_labels)
            if len(unique_labels) < 2:
                return 0.0
            
            return silhouette_score(valid_embeddings, valid_labels)
        except Exception as e:
            logger.warning(f"실루엣 점수 계산 실패: {e}")
            return 0.0
    
    def _calculate_cluster_similarity(self, cluster_embeddings: np.ndarray) -> float:
        """클러스터 내 문서 간 평균 유사도 계산"""
        if len(cluster_embeddings) < 2:
            return 1.0
        
        try:
            from sklearn.metrics.pairwise import cosine_similarity
            similarities = cosine_similarity(cluster_embeddings)
            # 대각선(자기 자신과의 유사도) 제외하고 평균 계산
            mask = ~np.eye(similarities.shape[0], dtype=bool)
            return np.mean(similarities[mask])
        except Exception as e:
            logger.warning(f"클러스터 유사도 계산 실패: {e}")
            return 0.0
    
    def _extract_cluster_keywords(self, documents: List[Document], top_k: int = 5) -> List[str]:
        """클러스터 키워드 추출 (TF-IDF 기반)"""
        try:
            # 모든 문서의 제목과 태그에서 키워드 추출
            all_text = []
            for doc in documents:
                text_parts = [doc.title]
                if doc.tags:
                    text_parts.extend(doc.tags)
                all_text.append(" ".join(text_parts))
            
            # 간단한 키워드 추출 (빈도 기반)
            word_freq = Counter()
            for text in all_text:
                words = text.lower().split()
                # 의미있는 단어만 추출 (길이 2 이상)
                words = [w for w in words if len(w) >= 2 and not w.startswith('#')]
                word_freq.update(words)
            
            # 상위 키워드 반환
            return [word for word, freq in word_freq.most_common(top_k)]
            
        except Exception as e:
            logger.warning(f"키워드 추출 실패: {e}")
            return []
    
    def _generate_cluster_label(self, representative_doc: Document, keywords: List[str]) -> str:
        """클러스터 라벨 생성"""
        # 대표 문서 제목 기반 + 키워드
        title_words = representative_doc.title.split()[:3]  # 제목의 처음 3단어
        
        if keywords:
            # 키워드가 있으면 조합
            label_parts = title_words + keywords[:2]
        else:
            label_parts = title_words
        
        return " ".join(label_parts)
    
    def _create_single_cluster(self, documents: List[Document]) -> ClusteringResult:
        """문서가 부족할 때 단일 클러스터 생성"""
        cluster = DocumentCluster(
            id="cluster_0",
            label="전체 문서",
            documents=documents,
            representative_doc=documents[0] if documents else None,
            keywords=[],
            similarity_score=1.0
        )
        
        return ClusteringResult(
            clusters=[cluster],
            algorithm="single",
            n_clusters=1,
            silhouette_score=1.0,
            parameters={},
            total_documents=len(documents),
            timestamp=datetime.now()
        )


def test_content_clusterer():
    """ContentClusterer 테스트"""
    print("🧪 ContentClusterer 테스트 시작...")
    
    if not SKLEARN_AVAILABLE:
        print("❌ scikit-learn이 필요합니다")
        return False
    
    try:
        # 테스트용 문서 생성
        from datetime import datetime
        test_documents = [
            Document(
                path="test1.md",
                title="TDD 기초",
                content="테스트 주도 개발의 기본 원칙",
                tags=["tdd", "testing"],
                frontmatter={},
                word_count=10,
                char_count=50,
                file_size=100,
                modified_at=datetime.now(),
                file_hash="test1_hash"
            ),
            Document(
                path="test2.md", 
                title="리팩토링 기법",
                content="코드 개선을 위한 리팩토링 방법",
                tags=["refactoring", "clean-code"],
                frontmatter={},
                word_count=12,
                char_count=60,
                file_size=120,
                modified_at=datetime.now(),
                file_hash="test2_hash"
            ),
            Document(
                path="test3.md",
                title="단위 테스트",
                content="효과적인 단위 테스트 작성법",
                tags=["testing", "unit-test"],
                frontmatter={},
                word_count=8,
                char_count=40,
                file_size=80,
                modified_at=datetime.now(),
                file_hash="test3_hash"
            )
        ]
        
        # Mock 설정 (실제 구현에서는 실제 객체 사용)
        class MockEmbeddingEngine:
            def encode(self, texts):
                # 더미 임베딩 (실제로는 BGE-M3)
                return [np.random.rand(1024) for _ in texts]
            
            @property
            def model(self):
                class MockModel:
                    def get_sentence_embedding_dimension(self):
                        return 1024
                return MockModel()
        
        class MockEmbeddingCache:
            def get_embedding(self, path):
                # 더미 캐시된 임베딩
                from ..core.embedding_cache import CachedEmbedding
                return CachedEmbedding(
                    file_path=path,
                    file_hash="dummy",
                    embedding=np.random.rand(1024),
                    model_name="test",
                    embedding_dimension=1024,
                    created_at=datetime.now(),
                    file_size=100
                )
        
        # ContentClusterer 생성
        config = {
            'clustering': {
                'default_algorithm': 'kmeans',
                'auto_k': True,
                'min_cluster_size': 2,
                'max_clusters': 10,
                'silhouette_threshold': 0.3
            }
        }
        
        clusterer = ContentClusterer(
            embedding_engine=MockEmbeddingEngine(),
            embedding_cache=MockEmbeddingCache(),
            config=config
        )
        
        # 클러스터링 테스트
        result = clusterer.cluster_documents(test_documents, n_clusters=2)
        
        # 결과 검증
        assert len(result.clusters) > 0, "클러스터가 생성되지 않음"
        assert result.total_documents == len(test_documents), "문서 수 불일치"
        assert result.silhouette_score >= 0, "실루엣 점수 오류"
        
        print(f"✅ 클러스터링 성공: {result.n_clusters}개 클러스터")
        print(f"   실루엣 점수: {result.silhouette_score:.3f}")
        
        return True
        
    except Exception as e:
        print(f"❌ ContentClusterer 테스트 실패: {e}")
        return False


if __name__ == "__main__":
    test_content_clusterer()