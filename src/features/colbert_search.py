#!/usr/bin/env python3
"""
ColBERT Search Engine for Vault Intelligence System V2

BGE-M3 ColBERT 임베딩 기반 토큰 수준 late interaction 검색
"""

import os
import logging
from typing import List, Dict, Optional, Tuple, Union
from dataclasses import dataclass
import numpy as np
import torch

try:
    from FlagEmbedding import BGEM3FlagModel
    BGE_AVAILABLE = True
except ImportError:
    BGE_AVAILABLE = False
    logging.warning("FlagEmbedding not available. ColBERT functionality will be disabled.")

from .advanced_search import SearchResult, Document

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ColBERTResult:
    """ColBERT 검색 결과"""
    document: Document
    colbert_score: float
    token_similarities: List[Tuple[str, str, float]]  # (query_token, doc_token, similarity)
    max_sim_per_query_token: List[float]  # 각 쿼리 토큰의 최대 유사도
    rank: int = 0


class ColBERTSearchEngine:
    """BGE-M3 ColBERT 기반 토큰 수준 late interaction 검색 엔진"""
    
    def __init__(
        self,
        model_name: str = "BAAI/bge-m3",
        device: Optional[str] = None,
        use_fp16: bool = True,
        cache_folder: Optional[str] = None,
        max_length: int = 4096,
        cache_dir: Optional[str] = None,
        enable_cache: bool = True
    ):
        """
        Args:
            model_name: BGE-M3 모델명
            device: 사용할 디바이스
            use_fp16: FP16 정밀도 사용
            cache_folder: 모델 캐시 폴더
            max_length: 최대 토큰 길이
            cache_dir: 임베딩 캐시 디렉토리
            enable_cache: 캐싱 활성화 여부
        """
        self.model_name = model_name
        self.device = device
        self.use_fp16 = use_fp16
        self.cache_folder = cache_folder
        self.max_length = max_length
        self.model = None
        self.is_initialized = False
        self.enable_cache = enable_cache
        
        # ColBERT 임베딩 저장소
        self.documents: List[Document] = []
        self.colbert_embeddings: List[np.ndarray] = []  # 문서별 ColBERT 임베딩
        self.document_tokens: List[List[str]] = []  # 문서별 토큰
        self.is_indexed = False
        
        # 캐시 시스템 초기화
        self.cache = None
        if cache_dir and enable_cache:
            try:
                from ..core.embedding_cache import EmbeddingCache
                self.cache = EmbeddingCache(cache_dir)
                logger.info("ColBERT 캐시 시스템 활성화")
            except Exception as e:
                logger.warning(f"캐시 시스템 초기화 실패: {e}")
                self.cache = None
        
        # 사용 가능 여부 확인
        if not BGE_AVAILABLE:
            logger.warning("FlagEmbedding 미설치로 인해 ColBERT 기능이 비활성화됩니다.")
            return
        
        logger.info(f"ColBERT 검색 엔진 초기화: {model_name}")
        self._initialize_model()
    
    def _initialize_model(self):
        """BGE-M3 모델 초기화"""
        if not BGE_AVAILABLE:
            return
        
        try:
            # 캐시 폴더 설정
            if self.cache_folder:
                os.environ['HF_HOME'] = self.cache_folder
                os.environ['TRANSFORMERS_CACHE'] = self.cache_folder
            
            # 디바이스 자동 감지
            if self.device is None:
                if torch.cuda.is_available():
                    self.device = "cuda"
                elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                    self.device = "mps"
                else:
                    self.device = "cpu"
            
            logger.info(f"ColBERT 디바이스: {self.device}")
            
            # BGE-M3 모델 로드
            self.model = BGEM3FlagModel(
                self.model_name,
                use_fp16=self.use_fp16,
                device=self.device
            )
            
            self.is_initialized = True
            logger.info("ColBERT BGE-M3 모델 로드 완료")
            
        except Exception as e:
            logger.error(f"ColBERT 모델 초기화 실패: {e}")
            self.is_initialized = False
    
    def is_available(self) -> bool:
        """ColBERT 엔진 사용 가능 여부"""
        return BGE_AVAILABLE and self.is_initialized
    
    def build_index(self, documents: List[Document], batch_size: int = 4, max_documents: Optional[int] = None, force_rebuild: bool = False) -> bool:
        """
        ColBERT 인덱스 구축 (캐시 지원)
        
        Args:
            documents: 인덱싱할 문서 목록
            batch_size: 배치 크기
            max_documents: 최대 문서 수 제한 (None이면 제한 없음)
            force_rebuild: 강제 재구축 여부
            
        Returns:
            인덱싱 성공 여부
        """
        if not self.is_available():
            logger.warning("ColBERT 엔진이 사용 불가능합니다.")
            return False
        
        if not documents:
            logger.warning("인덱싱할 문서가 없습니다.")
            return False
        
        logger.info(f"ColBERT 인덱스 구축 시작: {len(documents)}개 문서")
        
        # max_documents가 설정된 경우에만 제한
        if max_documents and len(documents) > max_documents:
            logger.warning(f"⚠️  문서 수 제한: {max_documents}개만 처리합니다.")
            documents = documents[:max_documents]
        
        try:
            self.documents = documents
            self.colbert_embeddings = []
            self.document_tokens = []
            
            cached_count = 0
            new_count = 0
            
            # 배치 단위로 처리
            for i in range(0, len(documents), batch_size):
                batch_docs = documents[i:i + batch_size]
                batch_to_process = []
                batch_indices = []
                
                # 캐시 확인
                for idx, doc in enumerate(batch_docs):
                    if self.cache and not force_rebuild and hasattr(doc, 'path') and doc.path:
                        # 파일 해시 계산
                        file_hash = self.cache._calculate_file_hash(doc.path)
                        cached = self.cache.get_colbert_embedding(doc.path, file_hash)
                        
                        if cached:
                            # 캐시된 임베딩 사용
                            self.colbert_embeddings.append(cached['colbert_embedding'])
                            tokens = self._approximate_tokens(doc.content) if cached.get('token_embeddings') is None else cached.get('token_embeddings', ["[CACHED]"])
                            self.document_tokens.append(tokens)
                            cached_count += 1
                            logger.debug(f"캐시 사용: {doc.path}")
                        else:
                            # 새로 처리 필요
                            batch_to_process.append(doc)
                            batch_indices.append(i + idx)
                    else:
                        # 캐시 비활성화 또는 강제 재구축
                        batch_to_process.append(doc)
                        batch_indices.append(i + idx)
                
                # 새로운 문서들만 처리
                if batch_to_process:
                    batch_texts = [doc.content for doc in batch_to_process]
                    
                    logger.info(f"ColBERT 배치 {i//batch_size + 1} 처리 중... (캐시: {cached_count}, 신규: {new_count})")
                    
                    try:
                        # BGE-M3로 ColBERT 임베딩 생성
                        result = self.model.encode(
                            batch_texts,
                            batch_size=len(batch_texts),
                            max_length=self.max_length,
                            return_dense=False,
                            return_sparse=False,
                            return_colbert_vecs=True  # ColBERT 임베딩 활성화
                        )
                        
                        # ColBERT 벡터와 토큰 정보 저장
                        colbert_vecs = result['colbert_vecs']
                        
                        for j, (colbert_vec, doc) in enumerate(zip(colbert_vecs, batch_to_process)):
                            self.colbert_embeddings.append(colbert_vec)
                            
                            # 토큰 정보 생성
                            tokens = self._approximate_tokens(doc.content)
                            self.document_tokens.append(tokens)
                            new_count += 1
                            
                            # 캐시에 저장
                            if self.cache and hasattr(doc, 'path') and doc.path:
                                self.cache.store_colbert_embedding(
                                    file_path=doc.path,
                                    colbert_embedding=colbert_vec,
                                    token_embeddings=None,  # 토큰 임베딩은 별도 저장하지 않음
                                    model_name=self.model_name,
                                    num_tokens=len(tokens)
                                )
                                logger.debug(f"캐시 저장: {doc.path}")
                        
                        logger.info(f"배치 {i//batch_size + 1} 완료: {len(batch_to_process)}개 문서 처리")
                        
                    except Exception as e:
                        logger.error(f"배치 {i//batch_size + 1} 처리 실패: {e}")
                        # 폴백: 빈 임베딩
                        for doc in batch_to_process:
                            self.colbert_embeddings.append(np.zeros((10, 1024)))  # 임시 크기
                            self.document_tokens.append(["[EMPTY]"])
                            new_count += 1
            
            self.is_indexed = True
            logger.info(f"✅ ColBERT 인덱스 구축 완료: 총 {len(self.colbert_embeddings)}개 (캐시: {cached_count}, 신규: {new_count})")
            return True
            
        except Exception as e:
            logger.error(f"ColBERT 인덱스 구축 실패: {e}")
            return False
    
    def _approximate_tokens(self, text: str, max_tokens: int = 512) -> List[str]:
        """
        텍스트를 대략적인 토큰으로 분할
        (실제로는 BGE-M3 tokenizer를 사용해야 하지만 간단한 근사치 사용)
        """
        # 간단한 토큰화 (공백 및 구두점 기준)
        import re
        tokens = re.findall(r'\b\w+\b', text.lower())
        return tokens[:max_tokens]  # 최대 토큰 수 제한
    
    def search(
        self,
        query: str,
        top_k: int = 10,
        similarity_threshold: float = 0.0
    ) -> List[ColBERTResult]:
        """
        ColBERT 기반 late interaction 검색
        
        Args:
            query: 검색 쿼리
            top_k: 반환할 상위 결과 수
            similarity_threshold: 유사도 임계값
            
        Returns:
            ColBERT 검색 결과 목록
        """
        if not self.is_available() or not self.is_indexed:
            logger.warning("ColBERT 엔진이 초기화되지 않았거나 인덱스가 없습니다.")
            return []
        
        if not query.strip():
            logger.warning("빈 쿼리입니다.")
            return []
        
        logger.info(f"ColBERT 검색 시작: '{query}'")
        
        try:
            # 쿼리 ColBERT 임베딩 생성
            query_result = self.model.encode(
                [query],
                batch_size=1,
                max_length=self.max_length,
                return_dense=False,
                return_sparse=False,
                return_colbert_vecs=True
            )
            
            query_colbert = query_result['colbert_vecs'][0]  # (query_tokens, dim)
            query_tokens = self._approximate_tokens(query)
            
            logger.info(f"쿼리 ColBERT 임베딩: {query_colbert.shape}, 토큰 수: {len(query_tokens)}")
            
            # 각 문서와의 late interaction 계산
            results = []
            
            for i, (doc, doc_colbert, doc_tokens) in enumerate(zip(
                self.documents, self.colbert_embeddings, self.document_tokens
            )):
                try:
                    # Late interaction: max_sim 계산
                    score, token_similarities, max_sims = self._compute_late_interaction(
                        query_colbert, doc_colbert, query_tokens, doc_tokens
                    )
                    
                    if score >= similarity_threshold:
                        result = ColBERTResult(
                            document=doc,
                            colbert_score=score,
                            token_similarities=token_similarities,
                            max_sim_per_query_token=max_sims,
                            rank=0  # 임시, 정렬 후 업데이트
                        )
                        results.append(result)
                
                except Exception as e:
                    logger.warning(f"문서 {i} 처리 실패: {e}")
                    continue
            
            # 점수 순으로 정렬
            results.sort(key=lambda x: x.colbert_score, reverse=True)
            
            # 상위 K개 선택 및 순위 업데이트
            top_results = results[:top_k]
            for rank, result in enumerate(top_results):
                result.rank = rank + 1
            
            logger.info(f"ColBERT 검색 완료: {len(top_results)}개 결과")
            return top_results
            
        except Exception as e:
            logger.error(f"ColBERT 검색 실패: {e}")
            return []
    
    def _compute_late_interaction(
        self,
        query_embeddings: np.ndarray,  # (query_tokens, dim)
        doc_embeddings: np.ndarray,    # (doc_tokens, dim)
        query_tokens: List[str],
        doc_tokens: List[str]
    ) -> Tuple[float, List[Tuple[str, str, float]], List[float]]:
        """
        ColBERT late interaction 계산
        
        Returns:
            (전체_점수, 토큰_유사도_쌍, 쿼리토큰별_최대유사도)
        """
        try:
            # 코사인 유사도 행렬 계산 (query_tokens x doc_tokens)
            similarities = np.dot(query_embeddings, doc_embeddings.T)
            
            # 각 쿼리 토큰에 대해 문서 토큰 중 최대 유사도 계산
            max_similarities = np.max(similarities, axis=1)  # (query_tokens,)
            
            # 전체 점수: 쿼리 토큰별 최대 유사도의 평균
            total_score = float(np.mean(max_similarities))
            
            # 상위 토큰 유사도 쌍 추출 (디버깅용)
            token_similarities = []
            for i, query_token in enumerate(query_tokens[:len(max_similarities)]):
                # 해당 쿼리 토큰과 가장 유사한 문서 토큰 찾기
                best_doc_idx = np.argmax(similarities[i])
                if best_doc_idx < len(doc_tokens):
                    best_doc_token = doc_tokens[best_doc_idx]
                    best_similarity = similarities[i, best_doc_idx]
                    
                    token_similarities.append((
                        query_token, 
                        best_doc_token, 
                        float(best_similarity)
                    ))
            
            return total_score, token_similarities, max_similarities.tolist()
            
        except Exception as e:
            logger.error(f"Late interaction 계산 실패: {e}")
            return 0.0, [], []
    
    def convert_to_search_results(self, colbert_results: List[ColBERTResult]) -> List[SearchResult]:
        """ColBERT 결과를 SearchResult 형태로 변환"""
        search_results = []
        
        for colbert_result in colbert_results:
            # 토큰 매칭 정보를 문자열로 변환
            matched_keywords = [
                f"{query_token}→{doc_token}({sim:.3f})"
                for query_token, doc_token, sim in colbert_result.token_similarities[:3]
            ]
            
            # 스니펫 생성 (최고 유사도 토큰 주변 텍스트)
            snippet = self._generate_colbert_snippet(
                colbert_result.document.content,
                colbert_result.token_similarities
            )
            
            search_result = SearchResult(
                document=colbert_result.document,
                similarity_score=colbert_result.colbert_score,
                match_type="colbert",
                matched_keywords=matched_keywords,
                snippet=snippet,
                rank=colbert_result.rank
            )
            search_results.append(search_result)
        
        return search_results
    
    def _generate_colbert_snippet(
        self, 
        content: str, 
        token_similarities: List[Tuple[str, str, float]],
        context_window: int = 100
    ) -> str:
        """ColBERT 토큰 매칭 기반 스니펫 생성"""
        if not token_similarities or not content:
            return content[:200] + "..." if len(content) > 200 else content
        
        # 가장 높은 유사도를 가진 토큰 찾기
        best_match = max(token_similarities, key=lambda x: x[2])
        best_doc_token = best_match[1]
        
        # 해당 토큰 주변 텍스트 추출
        content_lower = content.lower()
        token_pos = content_lower.find(best_doc_token.lower())
        
        if token_pos != -1:
            start = max(0, token_pos - context_window)
            end = min(len(content), token_pos + len(best_doc_token) + context_window)
            snippet = content[start:end]
            
            # 앞뒤 생략 표시
            if start > 0:
                snippet = "..." + snippet
            if end < len(content):
                snippet = snippet + "..."
                
            return snippet
        
        # 폴백: 문서 시작 부분
        return content[:200] + "..." if len(content) > 200 else content


def test_colbert_search():
    """ColBERT 검색 엔진 테스트"""
    print("🧪 ColBERT 검색 엔진 테스트")
    
    # 의존성 체크
    if not BGE_AVAILABLE:
        print("❌ FlagEmbedding이 설치되지 않아 테스트를 건너뜁니다.")
        return False
    
    try:
        # ColBERT 엔진 초기화
        engine = ColBERTSearchEngine(device="cpu")  # 테스트용 CPU 사용
        
        if not engine.is_available():
            print("❌ ColBERT 엔진 초기화 실패")
            return False
        
        print("✅ ColBERT 엔진 초기화 성공")
        print(f"   모델: {engine.model_name}")
        print(f"   디바이스: {engine.device}")
        
        return True
        
    except Exception as e:
        print(f"❌ 테스트 실패: {e}")
        return False


if __name__ == "__main__":
    test_colbert_search()