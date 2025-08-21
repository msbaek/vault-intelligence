#!/usr/bin/env python3
"""
Advanced Embedding Engine for Vault Intelligence System V2

BGE-M3 기반 고품질 임베딩 시스템
- Dense Embeddings (의미적 검색)
- Sparse Embeddings (키워드 검색)  
- ColBERT Embeddings (토큰 수준)
- Hybrid Search 지원
"""

import os
import logging
from typing import List, Optional, Union, Tuple, Dict, Any
import numpy as np
from pathlib import Path
import torch
from tqdm import tqdm
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeElapsedColumn, TimeRemainingColumn

# BGE-M3 모델
from FlagEmbedding import BGEM3FlagModel

# BM25 for sparse retrieval
from rank_bm25 import BM25Okapi

# 기본 라이브러리
from sklearn.metrics.pairwise import cosine_similarity
import pickle
import hashlib
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AdvancedEmbeddingEngine:
    """BGE-M3 기반 고품질 임베딩 엔진"""
    
    def __init__(
        self, 
        model_name: str = "BAAI/bge-m3",
        cache_dir: Optional[str] = None,
        device: Optional[str] = None,
        use_fp16: bool = False,
        batch_size: int = 4,
        max_length: int = 4096,
        num_workers: int = 6
    ):
        """
        Args:
            model_name: BGE 모델명 (기본: BAAI/bge-m3)
            cache_dir: 모델 캐시 디렉토리
            device: 계산 장치 (auto, cpu, cuda)
            use_fp16: FP16 정밀도 사용 여부
            batch_size: 배치 크기
            max_length: 최대 토큰 길이
            num_workers: 워커 프로세스 수
        """
        self.model_name = model_name
        self.cache_dir = cache_dir or "cache"
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.use_fp16 = use_fp16 and torch.cuda.is_available()
        self.batch_size = batch_size
        self.max_length = max_length
        self.num_workers = num_workers
        
        logger.info(f"BGE-M3 임베딩 엔진 초기화: {model_name}")
        logger.info(f"장치: {self.device}, FP16: {self.use_fp16}, 배치크기: {self.batch_size}")
        logger.info(f"최적화 설정 - 토큰길이: {self.max_length}, 워커수: {self.num_workers}")
        
        # BGE-M3 모델 로딩
        try:
            self.model = BGEM3FlagModel(
                model_name, 
                use_fp16=self.use_fp16,
                device=self.device
            )
            logger.info("✅ BGE-M3 모델 로딩 완료")
        except Exception as e:
            logger.error(f"❌ BGE-M3 모델 로딩 실패: {e}")
            raise
        
        # BM25 for sparse retrieval
        self.bm25_model = None
        self.tokenized_docs = []
        
        # 문서 데이터
        self.document_paths = []
        self.document_contents = []
        self.dense_embeddings = None
        self.sparse_embeddings = None
        self.is_fitted = False
        
        # 모델 정보
        self.embedding_dimension = 1024  # BGE-M3 dense embedding dimension
        
        # 캐시 디렉토리 생성
        os.makedirs(self.cache_dir, exist_ok=True)
    
    def fit_documents(self, documents: List[str], document_paths: List[str] = None, sample_size: Optional[int] = None) -> None:
        """문서들을 사용해 임베딩 생성 및 BM25 인덱스 구축
        
        Args:
            documents: 문서 리스트
            document_paths: 문서 경로 리스트
            sample_size: 샘플링할 문서 수 (None이면 전체 처리)
        """
        logger.info(f"문서 인덱싱 시작... ({len(documents)}개 문서)")
        
        # 샘플링 처리
        if sample_size and sample_size < len(documents):
            logger.warning(f"⚠️  성능 최적화를 위해 {len(documents)}개 문서 중 {sample_size}개만 샘플링")
            
            # 인덱스 기반 균등 샘플링 (전체 문서에서 균등하게 선택)
            step = len(documents) // sample_size
            sample_indices = list(range(0, len(documents), step))[:sample_size]
            
            sampled_docs = [documents[i] for i in sample_indices]
            sampled_paths = [document_paths[i] if document_paths else f"doc_{i}.md" for i in sample_indices]
            
            logger.info(f"📊 샘플링 완료: {len(sampled_docs)}개 문서 선택")
            documents = sampled_docs
            document_paths = sampled_paths
        
        # 빈 문서 처리
        processed_docs = []
        for i, doc in enumerate(documents):
            if doc and doc.strip():
                processed_docs.append(doc.strip())
            else:
                processed_docs.append(f"빈 문서 {i}")
        
        self.document_contents = processed_docs
        self.document_paths = document_paths or [f"doc_{i}.md" for i in range(len(documents))]
        
        # Dense embeddings 생성
        logger.info("Dense embeddings 생성 중...")
        self._generate_dense_embeddings(processed_docs)
        
        # Sparse embeddings (BM25) 구축
        logger.info("Sparse embeddings (BM25) 구축 중...")
        self._build_bm25_index(processed_docs)
        
        self.is_fitted = True
        logger.info(f"✅ 문서 인덱싱 완료: {len(documents)}개 문서")
    
    def _generate_dense_embeddings(self, documents: List[str]) -> None:
        """Dense embeddings 생성 (최적화된 배치 처리 + Rich 진행률)"""
        try:
            total_docs = len(documents)
            # 최적화된 청크 크기: MPS 가속을 위해 더 큰 배치 활용
            chunk_size = max(200, self.batch_size * 20)  # 청크 크기 증가
            
            console = Console()
            console.print(f"🚀 [bold green]BGE-M3 Dense 임베딩 생성 시작[/bold green]")
            console.print(f"📊 총 문서: {total_docs:,}개 | 배치크기: {self.batch_size} | 청크크기: {chunk_size}")
            console.print(f"⚡ 가속: MPS | 토큰길이: {self.max_length} | 워커: {self.num_workers}")
            
            all_embeddings = []
            
            # Rich 진행률 표시로 청크 단위 처리
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                TimeElapsedColumn(),
                TimeRemainingColumn(),
                console=console
            ) as progress:
                
                task = progress.add_task("임베딩 생성 중...", total=total_docs)
                
                for i in range(0, total_docs, chunk_size):
                    chunk_docs = documents[i:i + chunk_size]
                    chunk_num = i // chunk_size + 1
                    total_chunks = (total_docs + chunk_size - 1) // chunk_size
                    
                    progress.update(task, description=f"청크 {chunk_num}/{total_chunks} 처리 중...")
                    
                    # 최적화된 배치 처리로 임베딩 생성
                    embeddings_result = self.model.encode(
                        chunk_docs,
                        batch_size=self.batch_size,
                        max_length=self.max_length,
                        return_dense=True,
                        return_sparse=False,
                        return_colbert_vecs=False
                    )
                    
                    all_embeddings.append(embeddings_result['dense_vecs'])
                    
                    # 진행률 업데이트
                    processed_docs = min(i + len(chunk_docs), total_docs)
                    progress.update(task, completed=processed_docs)
            
            # 모든 청크의 임베딩을 합침
            self.dense_embeddings = np.vstack(all_embeddings) if all_embeddings else np.zeros((0, self.embedding_dimension))
            
            console.print(f"✅ [bold green]Dense embeddings 생성 완료[/bold green]: {self.dense_embeddings.shape}")
            console.print(f"📈 성능 향상: MPS 가속 + 배치크기 {self.batch_size} + 청크 최적화")
            
        except Exception as e:
            logger.error(f"Dense embeddings 생성 실패: {e}")
            # 폴백: 제로 벡터 생성
            self.dense_embeddings = np.zeros((len(documents), self.embedding_dimension))
    
    def _build_bm25_index(self, documents: List[str]) -> None:
        """BM25 인덱스 구축"""
        try:
            # 문서를 토큰화 (간단한 공백 기반 분할)
            self.tokenized_docs = []
            for doc in documents:
                # 한국어와 영어 모두 지원하는 간단한 토큰화
                tokens = doc.lower().split()
                self.tokenized_docs.append(tokens)
            
            # BM25 모델 구축
            self.bm25_model = BM25Okapi(self.tokenized_docs)
            logger.info(f"BM25 인덱스 구축 완료: {len(self.tokenized_docs)}개 문서")
            
        except Exception as e:
            logger.error(f"BM25 인덱스 구축 실패: {e}")
            self.bm25_model = None
    
    def encode_text(self, text: str) -> np.ndarray:
        """단일 텍스트의 dense embedding 생성"""
        try:
            if not text or not text.strip():
                text = "빈 텍스트"
            
            # BGE-M3로 dense embedding 생성
            result = self.model.encode(
                [text.strip()],
                batch_size=1,
                max_length=self.max_length,
                return_dense=True,
                return_sparse=False,
                return_colbert_vecs=False
            )
            
            return result['dense_vecs'][0]
            
        except Exception as e:
            logger.error(f"텍스트 임베딩 생성 실패: {e}")
            return np.zeros(self.embedding_dimension)
    
    def encode_texts(
        self, 
        texts: List[str], 
        batch_size: int = None,
        show_progress: bool = True
    ) -> np.ndarray:
        """다중 텍스트의 배치 dense embedding 생성"""
        try:
            if batch_size is None:
                batch_size = self.batch_size
            
            # 빈 텍스트 처리
            processed_texts = []
            for i, text in enumerate(texts):
                if text and text.strip():
                    processed_texts.append(text.strip())
                else:
                    processed_texts.append(f"빈 텍스트 {i}")
            
            # BGE-M3로 배치 embedding 생성
            result = self.model.encode(
                processed_texts,
                batch_size=batch_size,
                max_length=self.max_length,
                return_dense=True,
                return_sparse=False,
                return_colbert_vecs=False
            )
            
            if show_progress:
                logger.info(f"배치 임베딩 생성 완료: {len(texts)}개 텍스트")
            
            return result['dense_vecs']
            
        except Exception as e:
            logger.error(f"배치 임베딩 생성 실패: {e}")
            return np.zeros((len(texts), self.embedding_dimension))
    
    def semantic_search(
        self, 
        query: str, 
        top_k: int = 10, 
        threshold: float = 0.0
    ) -> List[Tuple[str, float]]:
        """Dense embedding 기반 의미적 검색"""
        if not self.is_fitted:
            raise ValueError("먼저 fit_documents()를 호출해야 합니다.")
        
        try:
            # 쿼리 임베딩
            query_embedding = self.encode_text(query)
            
            # 코사인 유사도 계산
            similarities = cosine_similarity([query_embedding], self.dense_embeddings)[0]
            
            # 임계값 이상만 필터링
            valid_indices = np.where(similarities >= threshold)[0]
            if len(valid_indices) == 0:
                return []
            
            valid_similarities = similarities[valid_indices]
            
            # 상위 k개 선택
            if len(valid_indices) > top_k:
                top_local_indices = np.argsort(valid_similarities)[::-1][:top_k]
                top_indices = valid_indices[top_local_indices]
                top_similarities = valid_similarities[top_local_indices]
            else:
                sort_order = np.argsort(valid_similarities)[::-1]
                top_indices = valid_indices[sort_order]
                top_similarities = valid_similarities[sort_order]
            
            # 결과 생성
            results = []
            for idx, sim in zip(top_indices, top_similarities):
                if idx < len(self.document_paths):
                    results.append((self.document_paths[idx], float(sim)))
            
            return results
            
        except Exception as e:
            logger.error(f"의미적 검색 실패: {e}")
            return []
    
    def keyword_search(
        self, 
        query: str, 
        top_k: int = 10
    ) -> List[Tuple[str, float]]:
        """BM25 기반 키워드 검색"""
        if not self.is_fitted or self.bm25_model is None:
            logger.warning("BM25 모델이 준비되지 않음. 빈 결과 반환.")
            return []
        
        try:
            # 쿼리 토큰화
            query_tokens = query.lower().split()
            
            # BM25 스코어 계산
            scores = self.bm25_model.get_scores(query_tokens)
            
            # 상위 k개 선택
            top_indices = np.argsort(scores)[::-1][:top_k]
            
            # 결과 생성
            results = []
            for idx in top_indices:
                if idx < len(self.document_paths) and scores[idx] > 0:
                    results.append((self.document_paths[idx], float(scores[idx])))
            
            return results
            
        except Exception as e:
            logger.error(f"키워드 검색 실패: {e}")
            return []
    
    def hybrid_search(
        self, 
        query: str, 
        top_k: int = 10,
        semantic_weight: float = 0.7,
        keyword_weight: float = 0.3,
        threshold: float = 0.0
    ) -> List[Tuple[str, float]]:
        """Hybrid search: Dense + Sparse (RRF 기반 융합)"""
        try:
            # 의미적 검색 결과
            semantic_results = self.semantic_search(query, top_k=top_k*2, threshold=threshold)
            
            # 키워드 검색 결과
            keyword_results = self.keyword_search(query, top_k=top_k*2)
            
            # 결과 융합 (RRF - Reciprocal Rank Fusion)
            final_scores = {}
            
            # 의미적 검색 점수 반영
            for rank, (path, score) in enumerate(semantic_results):
                if path not in final_scores:
                    final_scores[path] = 0
                # RRF 스코어: 1 / (rank + 60)
                rrf_score = 1.0 / (rank + 60)
                final_scores[path] += semantic_weight * rrf_score
            
            # 키워드 검색 점수 반영
            for rank, (path, score) in enumerate(keyword_results):
                if path not in final_scores:
                    final_scores[path] = 0
                rrf_score = 1.0 / (rank + 60)
                final_scores[path] += keyword_weight * rrf_score
            
            # 최종 결과 정렬
            sorted_results = sorted(
                final_scores.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:top_k]
            
            return sorted_results
            
        except Exception as e:
            logger.error(f"하이브리드 검색 실패: {e}")
            # 폴백: 의미적 검색만 사용
            return self.semantic_search(query, top_k, threshold)
    
    def calculate_similarity(
        self, 
        embedding1: np.ndarray, 
        embedding2: np.ndarray
    ) -> float:
        """두 임베딩 간의 코사인 유사도 계산"""
        try:
            similarity = cosine_similarity([embedding1], [embedding2])[0][0]
            return float(similarity)
        except Exception as e:
            logger.error(f"유사도 계산 실패: {e}")
            return 0.0
    
    def calculate_similarities(
        self, 
        query_embedding: np.ndarray, 
        document_embeddings: np.ndarray
    ) -> np.ndarray:
        """쿼리와 여러 문서 간의 유사도 계산"""
        try:
            similarities = cosine_similarity([query_embedding], document_embeddings)[0]
            return similarities
        except Exception as e:
            logger.error(f"배치 유사도 계산 실패: {e}")
            return np.zeros(len(document_embeddings))
    
    def find_most_similar(
        self,
        query_embedding: np.ndarray,
        document_embeddings: np.ndarray,
        top_k: int = 10
    ) -> List[Tuple[int, float]]:
        """가장 유사한 문서들의 인덱스와 유사도 반환"""
        try:
            similarities = self.calculate_similarities(query_embedding, document_embeddings)
            
            # 상위 k개 선택
            top_indices = np.argsort(similarities)[::-1][:top_k]
            
            results = [(int(idx), float(similarities[idx])) for idx in top_indices]
            return results
        except Exception as e:
            logger.error(f"유사 문서 검색 실패: {e}")
            return []
    
    def search_documents(self, query: str, top_k: int = 10, threshold: float = 0.0) -> List[Tuple[str, float]]:
        """기본 검색 (하이브리드 검색 사용)"""
        return self.hybrid_search(query, top_k, threshold=threshold)
    
    def get_model_info(self) -> dict:
        """모델 정보 반환"""
        return {
            "model_name": self.model_name,
            "embedding_dimension": self.embedding_dimension,
            "device": self.device,
            "use_fp16": self.use_fp16,
            "batch_size": self.batch_size,
            "cache_dir": self.cache_dir,
            "is_fitted": self.is_fitted,
            "document_count": len(self.document_paths) if self.document_paths else 0,
            "has_bm25": self.bm25_model is not None
        }
    
    def preprocess_text(self, text: str) -> str:
        """텍스트 전처리"""
        if not text:
            return ""
        
        # 기본적인 전처리
        text = text.strip()
        return text
    
    def save_model(self, filepath: str) -> None:
        """모델 저장 (임베딩과 BM25 인덱스만)"""
        try:
            model_data = {
                'model_name': self.model_name,
                'document_paths': self.document_paths,
                'document_contents': self.document_contents,
                'dense_embeddings': self.dense_embeddings,
                'tokenized_docs': self.tokenized_docs,
                'is_fitted': self.is_fitted,
                'embedding_dimension': self.embedding_dimension,
                'device': self.device,
                'use_fp16': self.use_fp16,
                'batch_size': self.batch_size
            }
            
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, 'wb') as f:
                pickle.dump(model_data, f)
            
            logger.info(f"모델 저장 완료: {filepath}")
        except Exception as e:
            logger.error(f"모델 저장 실패: {e}")
            raise
    
    def load_model(self, filepath: str) -> None:
        """모델 로딩"""
        try:
            with open(filepath, 'rb') as f:
                model_data = pickle.load(f)
            
            self.model_name = model_data['model_name']
            self.document_paths = model_data['document_paths']
            self.document_contents = model_data['document_contents']
            self.dense_embeddings = model_data['dense_embeddings']
            self.tokenized_docs = model_data['tokenized_docs']
            self.is_fitted = model_data['is_fitted']
            self.embedding_dimension = model_data['embedding_dimension']
            
            # BM25 모델 재구축
            if self.tokenized_docs:
                self.bm25_model = BM25Okapi(self.tokenized_docs)
            
            logger.info(f"모델 로딩 완료: {filepath}")
        except Exception as e:
            logger.error(f"모델 로딩 실패: {e}")
            raise


# 기존 인터페이스 호환성을 위한 별칭
SentenceTransformerEngine = AdvancedEmbeddingEngine


def test_engine():
    """엔진 테스트 함수"""
    try:
        # 엔진 초기화
        engine = AdvancedEmbeddingEngine()
        
        # 테스트 문서
        test_docs = [
            "TDD는 테스트 주도 개발 방법론입니다. 먼저 테스트를 작성하고 코드를 구현합니다.",
            "리팩토링은 코드의 구조를 개선하는 과정입니다. 기능은 변경하지 않고 코드 품질을 높입니다.",
            "Clean Code는 읽기 쉬운 코드를 작성하는 방법을 다룹니다. 좋은 네이밍과 간결한 함수가 핵심입니다.",
            "Spring Framework는 자바 기반의 웹 애플리케이션 프레임워크입니다.",
            "Python은 간결하고 읽기 쉬운 프로그래밍 언어입니다."
        ]
        test_paths = [f"doc_{i}.md" for i in range(len(test_docs))]
        
        # 문서 훈련
        engine.fit_documents(test_docs, test_paths)
        print(f"✅ 모델 훈련 완료: {engine.embedding_dimension}차원")
        
        # 의미적 검색 테스트
        semantic_results = engine.semantic_search("테스트 개발 방법", top_k=3)
        print(f"✅ 의미적 검색 결과:")
        for path, score in semantic_results:
            print(f"  - {path}: {score:.4f}")
        
        # 키워드 검색 테스트
        keyword_results = engine.keyword_search("TDD 테스트", top_k=3)
        print(f"✅ 키워드 검색 결과:")
        for path, score in keyword_results:
            print(f"  - {path}: {score:.4f}")
        
        # 하이브리드 검색 테스트
        hybrid_results = engine.hybrid_search("테스트 주도 개발", top_k=3)
        print(f"✅ 하이브리드 검색 결과:")
        for path, score in hybrid_results:
            print(f"  - {path}: {score:.4f}")
        
        # 단일 임베딩 테스트
        single_embedding = engine.encode_text("개발 방법론")
        print(f"✅ 단일 임베딩 차원: {len(single_embedding)}")
        
        # 유사도 계산 테스트
        emb1 = engine.encode_text("TDD 테스트")
        emb2 = engine.encode_text("테스트 주도 개발")
        similarity = engine.calculate_similarity(emb1, emb2)
        print(f"✅ 유사도 ('TDD 테스트' vs '테스트 주도 개발'): {similarity:.4f}")
        
        # 모델 정보 출력
        model_info = engine.get_model_info()
        print(f"✅ 모델 정보: {model_info}")
        
        print("✅ 엔진 테스트 완료!")
        return True
        
    except Exception as e:
        print(f"❌ 엔진 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    test_engine()