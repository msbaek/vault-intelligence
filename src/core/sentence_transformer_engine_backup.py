#!/usr/bin/env python3
"""
Sentence Transformer Engine for Vault Intelligence System V2

TF-IDF 기반 임베딩을 통한 의미적 검색 엔진 (임시 구현)
패키지 의존성 문제 해결 후 Sentence Transformers로 전환 예정
"""

import os
import logging
from typing import List, Optional, Union, Tuple
import numpy as np
from pathlib import Path

# TF-IDF 기반 임시 구현
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pickle
import hashlib

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SentenceTransformerEngine:
    """TF-IDF 기반 임베딩 엔진 (임시 구현)"""
    
    def __init__(
        self, 
        model_name: str = "tfidf",
        cache_dir: Optional[str] = None,
        device: Optional[str] = None
    ):
        """
        Args:
            model_name: 임베딩 모델명 (현재는 tfidf만 지원)
            cache_dir: 모델 캐시 디렉토리
            device: 계산 장치 (TF-IDF에서는 무시됨)
        """
        self.model_name = model_name
        self.cache_dir = cache_dir or "cache"
        
        logger.info(f"TF-IDF 임베딩 엔진 초기화 (임시 구현)")
        
        # TF-IDF vectorizer 초기화
        self.vectorizer = TfidfVectorizer(
            max_features=5000,
            stop_words=None,  # 한국어 지원을 위해 None
            ngram_range=(1, 2),
            min_df=1,  # 최소 문서 빈도를 1로 낮춤
            max_df=0.95
        )
        
        self.document_vectors = None
        self.document_paths = []
        self.is_fitted = False
        self.embedding_dimension = 5000  # TF-IDF 최대 피처 수
        
        # 캐시 디렉토리 생성
        os.makedirs(self.cache_dir, exist_ok=True)
    
    def fit_documents(self, documents: List[str], document_paths: List[str] = None) -> None:
        """문서들을 사용해 TF-IDF 벡터라이저 훈련"""
        logger.info(f"TF-IDF 벡터라이저 훈련 중... ({len(documents)}개 문서)")
        
        # 빈 문서 처리
        processed_docs = []
        for doc in documents:
            if doc and doc.strip():
                processed_docs.append(doc.strip())
            else:
                processed_docs.append("빈 문서")  # 빈 문서 대체
        
        # TF-IDF 훈련 및 변환
        self.document_vectors = self.vectorizer.fit_transform(processed_docs)
        self.document_paths = document_paths or [f"doc_{i}" for i in range(len(documents))]
        self.is_fitted = True
        
        # 실제 차원 수 업데이트
        self.embedding_dimension = self.document_vectors.shape[1]
        
        logger.info(f"TF-IDF 훈련 완료: {self.embedding_dimension}차원")
    
    def encode_text(self, text: str) -> np.ndarray:
        """단일 텍스트의 임베딩 생성"""
        if not self.is_fitted:
            raise ValueError("먼저 fit_documents()를 호출해야 합니다.")
        
        try:
            if not text or not text.strip():
                text = "빈 텍스트"
            
            # TF-IDF 변환
            vector = self.vectorizer.transform([text.strip()])
            return vector.toarray()[0]
        except Exception as e:
            logger.error(f"텍스트 임베딩 생성 실패: {e}")
            return np.zeros(self.embedding_dimension)
    
    def encode_texts(
        self, 
        texts: List[str], 
        batch_size: int = 32,
        show_progress: bool = True
    ) -> np.ndarray:
        """다중 텍스트의 배치 임베딩 생성"""
        if not self.is_fitted:
            raise ValueError("먼저 fit_documents()를 호출해야 합니다.")
        
        try:
            # 빈 텍스트 처리
            processed_texts = []
            for text in texts:
                if text and text.strip():
                    processed_texts.append(text.strip())
                else:
                    processed_texts.append("빈 텍스트")
            
            # TF-IDF 변환
            vectors = self.vectorizer.transform(processed_texts)
            
            if show_progress:
                logger.info(f"배치 임베딩 생성 완료: {len(texts)}개 텍스트")
            
            return vectors.toarray()
        except Exception as e:
            logger.error(f"배치 임베딩 생성 실패: {e}")
            return np.zeros((len(texts), self.embedding_dimension))
    
    def calculate_similarity(
        self, 
        embedding1: np.ndarray, 
        embedding2: np.ndarray
    ) -> float:
        """두 임베딩 간의 코사인 유사도 계산"""
        try:
            # 코사인 유사도 계산
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
            # 배치 코사인 유사도 계산
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
        """문서 검색 (경로와 유사도 반환)"""
        if not self.is_fitted:
            raise ValueError("먼저 fit_documents()를 호출해야 합니다.")
        
        try:
            # 쿼리 임베딩
            query_embedding = self.encode_text(query)
            
            # 문서와의 유사도 계산
            similarities = cosine_similarity([query_embedding], self.document_vectors)[0]
            
            # 임계값 이상만 필터링
            valid_indices = np.where(similarities >= threshold)[0]
            valid_similarities = similarities[valid_indices]
            
            # 상위 k개 선택
            if len(valid_indices) > top_k:
                top_local_indices = np.argsort(valid_similarities)[::-1][:top_k]
                top_indices = valid_indices[top_local_indices]
                top_similarities = valid_similarities[top_local_indices]
            else:
                top_indices = valid_indices[np.argsort(valid_similarities)[::-1]]
                top_similarities = valid_similarities[np.argsort(valid_similarities)[::-1]]
            
            # 결과 생성
            results = []
            for idx, sim in zip(top_indices, top_similarities):
                if idx < len(self.document_paths):
                    results.append((self.document_paths[idx], float(sim)))
            
            return results
            
        except Exception as e:
            logger.error(f"문서 검색 실패: {e}")
            return []
    
    def get_model_info(self) -> dict:
        """모델 정보 반환"""
        return {
            "model_name": self.model_name,
            "embedding_dimension": self.embedding_dimension,
            "device": "cpu",  # TF-IDF는 CPU만 사용
            "cache_dir": self.cache_dir,
            "is_fitted": self.is_fitted,
            "document_count": len(self.document_paths) if self.document_paths else 0
        }
    
    def preprocess_text(self, text: str) -> str:
        """텍스트 전처리"""
        if not text:
            return ""
        
        # 기본적인 전처리
        text = text.strip()
        return text
    
    def save_model(self, filepath: str) -> None:
        """모델 저장"""
        try:
            model_data = {
                'vectorizer': self.vectorizer,
                'document_vectors': self.document_vectors,
                'document_paths': self.document_paths,
                'is_fitted': self.is_fitted,
                'embedding_dimension': self.embedding_dimension,
                'model_name': self.model_name
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
            
            self.vectorizer = model_data['vectorizer']
            self.document_vectors = model_data['document_vectors']
            self.document_paths = model_data['document_paths']
            self.is_fitted = model_data['is_fitted']
            self.embedding_dimension = model_data['embedding_dimension']
            self.model_name = model_data.get('model_name', 'tfidf')
            
            logger.info(f"모델 로딩 완료: {filepath}")
        except Exception as e:
            logger.error(f"모델 로딩 실패: {e}")
            raise


def test_engine():
    """엔진 테스트 함수"""
    try:
        # 엔진 초기화
        engine = SentenceTransformerEngine()
        
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
        
        # 검색 테스트
        search_results = engine.search_documents("테스트 개발 방법", top_k=3)
        print(f"✅ 검색 결과:")
        for path, score in search_results:
            print(f"  - {path}: {score:.4f}")
        
        # 단일 임베딩 테스트
        single_embedding = engine.encode_text("개발 방법론")
        print(f"✅ 단일 임베딩 차원: {len(single_embedding)}")
        
        # 유사도 계산 테스트
        emb1 = engine.encode_text("TDD 테스트")
        emb2 = engine.encode_text("테스트 주도 개발")
        similarity = engine.calculate_similarity(emb1, emb2)
        print(f"✅ 유사도 ('TDD 테스트' vs '테스트 주도 개발'): {similarity:.4f}")
        
        print("✅ 엔진 테스트 완료!")
        return True
        
    except Exception as e:
        print(f"❌ 엔진 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    test_engine()