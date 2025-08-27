#!/usr/bin/env python3
"""
Cross-encoder Reranker for Vault Intelligence System V2

BGE Reranker V2-M3 기반 정밀 검색 결과 재순위화
"""

import os
import logging
from typing import List, Dict, Optional, Tuple, Union
from dataclasses import dataclass
import numpy as np

try:
    from FlagEmbedding import FlagReranker
    RERANKER_AVAILABLE = True
except ImportError:
    RERANKER_AVAILABLE = False
    logging.warning("FlagEmbedding not available. Reranker functionality will be disabled.")

from .advanced_search import SearchResult

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class RerankResult:
    """재순위화 결과"""
    search_result: SearchResult
    rerank_score: float
    original_rank: int
    new_rank: int


class BGEReranker:
    """BGE Reranker V2-M3 기반 재순위화 시스템"""
    
    def __init__(
        self,
        model_name: str = "BAAI/bge-reranker-v2-m3",
        use_fp16: bool = True,
        cache_folder: Optional[str] = None,
        device: Optional[str] = None
    ):
        """
        Args:
            model_name: Reranker 모델명
            use_fp16: FP16 정밀도 사용 여부
            cache_folder: 모델 캐시 폴더
            device: 사용할 디바이스 ('cuda', 'mps', 'cpu')
        """
        self.model_name = model_name
        self.use_fp16 = use_fp16
        self.cache_folder = cache_folder or "models"
        self.device = device
        self.model = None
        self.is_initialized = False
        
        # 사용 가능 여부 확인
        if not RERANKER_AVAILABLE:
            logger.warning("FlagEmbedding 미설치로 인해 Reranker 기능이 비활성화됩니다.")
            return
        
        logger.info(f"BGE Reranker 초기화: {model_name}")
        self._initialize_model()
    
    def _initialize_model(self):
        """모델 초기화"""
        if not RERANKER_AVAILABLE:
            return
        
        try:
            # 캐시 폴더 설정
            if self.cache_folder:
                os.environ['HF_HOME'] = self.cache_folder
                os.environ['TRANSFORMERS_CACHE'] = self.cache_folder
            
            # 디바이스 자동 감지
            if self.device is None:
                import torch
                if torch.cuda.is_available():
                    self.device = "cuda"
                elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                    self.device = "mps"
                else:
                    self.device = "cpu"
            
            logger.info(f"Reranker 디바이스: {self.device}")
            
            # 모델 로드
            self.model = FlagReranker(
                self.model_name,
                use_fp16=self.use_fp16,
                device=self.device
            )
            
            self.is_initialized = True
            logger.info("BGE Reranker 모델 로드 완료")
            
        except Exception as e:
            logger.error(f"Reranker 모델 초기화 실패: {e}")
            self.is_initialized = False
    
    def is_available(self) -> bool:
        """Reranker 사용 가능 여부"""
        return RERANKER_AVAILABLE and self.is_initialized
    
    def rerank(
        self,
        query: str,
        search_results: List[SearchResult],
        top_k: int = 10,
        batch_size: int = 4
    ) -> List[RerankResult]:
        """
        검색 결과를 재순위화
        
        Args:
            query: 검색 쿼리
            search_results: 초기 검색 결과
            top_k: 재순위화할 상위 K개
            batch_size: 배치 크기
            
        Returns:
            재순위화된 결과 목록
        """
        if not self.is_available():
            logger.warning("Reranker가 사용 불가능합니다. 원본 순위를 반환합니다.")
            return [
                RerankResult(
                    search_result=result,
                    rerank_score=result.similarity_score,
                    original_rank=i,
                    new_rank=i
                )
                for i, result in enumerate(search_results[:top_k])
            ]
        
        if not search_results:
            return []
        
        # 재순위화할 결과 선택 (상위 후보)
        candidates = search_results[:min(len(search_results), top_k * 3)]  # 3배수 후보
        logger.info(f"재순위화 대상: {len(candidates)}개 문서")
        
        try:
            # 쿼리-문서 페어 준비
            pairs = []
            for result in candidates:
                # 문서 요약 생성 (긴 문서 처리)
                content = self._prepare_document_text(result.document.content)
                pairs.append([query, content])
            
            # 배치 단위로 재순위화 점수 계산
            rerank_scores = []
            
            for i in range(0, len(pairs), batch_size):
                batch_pairs = pairs[i:i + batch_size]
                try:
                    batch_scores = self.model.compute_score(batch_pairs)
                    
                    # 단일 점수인 경우 리스트로 변환
                    if not isinstance(batch_scores, list):
                        batch_scores = [batch_scores]
                    
                    rerank_scores.extend(batch_scores)
                    
                except Exception as e:
                    logger.warning(f"배치 {i//batch_size + 1} 재순위화 실패: {e}")
                    # 폴백: 원본 점수 사용
                    for j in range(len(batch_pairs)):
                        if i + j < len(candidates):
                            rerank_scores.append(candidates[i + j].similarity_score)
            
            # 결과 생성 및 정렬
            rerank_results = []
            for i, (result, score) in enumerate(zip(candidates, rerank_scores)):
                rerank_results.append(RerankResult(
                    search_result=result,
                    rerank_score=float(score),
                    original_rank=i,
                    new_rank=0  # 임시, 정렬 후 업데이트
                ))
            
            # 재순위화 점수로 정렬
            rerank_results.sort(key=lambda x: x.rerank_score, reverse=True)
            
            # 새로운 순위 업데이트
            for new_rank, result in enumerate(rerank_results):
                result.new_rank = new_rank
            
            # 상위 K개 반환
            final_results = rerank_results[:top_k]
            
            logger.info(f"재순위화 완료: {len(final_results)}개 결과")
            
            # 순위 변화 로깅
            self._log_rank_changes(final_results)
            
            return final_results
            
        except Exception as e:
            logger.error(f"재순위화 처리 실패: {e}")
            # 폴백: 원본 순위 반환
            return [
                RerankResult(
                    search_result=result,
                    rerank_score=result.similarity_score,
                    original_rank=i,
                    new_rank=i
                )
                for i, result in enumerate(search_results[:top_k])
            ]
    
    def _prepare_document_text(self, content: str, max_length: int = 2048) -> str:
        """
        문서 텍스트 전처리
        
        Args:
            content: 원본 문서 내용
            max_length: 최대 문자 길이
            
        Returns:
            전처리된 텍스트
        """
        if not content:
            return ""
        
        # 기본 정리
        text = content.strip()
        
        # 너무 긴 경우 요약
        if len(text) > max_length:
            # 시작 부분과 끝 부분을 결합
            start_part = text[:max_length // 2]
            end_part = text[-(max_length // 2):]
            text = f"{start_part}...\n\n...{end_part}"
        
        return text
    
    def _log_rank_changes(self, rerank_results: List[RerankResult], top_n: int = 5):
        """순위 변화 로깅"""
        significant_changes = []
        
        for result in rerank_results[:top_n]:
            rank_change = result.original_rank - result.new_rank
            if abs(rank_change) > 0:
                significant_changes.append((
                    result.search_result.document.title or result.search_result.document.path,
                    result.original_rank,
                    result.new_rank,
                    rank_change,
                    result.rerank_score
                ))
        
        if significant_changes:
            logger.info("🔄 주요 순위 변화:")
            for title, old_rank, new_rank, change, score in significant_changes[:3]:
                direction = "⬆️" if change > 0 else "⬇️"
                logger.info(f"  {direction} '{title[:50]}...': {old_rank} → {new_rank} (점수: {score:.3f})")


class RerankerPipeline:
    """검색 + 재순위화 통합 파이프라인"""
    
    def __init__(
        self,
        search_engine,
        reranker: Optional[BGEReranker] = None,
        config: Optional[Dict] = None
    ):
        """
        Args:
            search_engine: AdvancedSearchEngine 인스턴스
            reranker: BGEReranker 인스턴스 (None이면 자동 생성)
            config: 파이프라인 설정
        """
        self.search_engine = search_engine
        self.config = config or {}
        
        # Reranker 초기화
        if reranker is None:
            reranker_config = self.config.get('reranker', {})
            self.reranker = BGEReranker(
                model_name=reranker_config.get('model_name', 'BAAI/bge-reranker-v2-m3'),
                use_fp16=reranker_config.get('use_fp16', True),
                cache_folder=reranker_config.get('cache_folder'),
                device=reranker_config.get('device')
            )
        else:
            self.reranker = reranker
        
        logger.info("검색 + 재순위화 파이프라인 초기화 완료")
    
    def search_and_rerank(
        self,
        query: str,
        search_method: str = "hybrid",
        initial_k: int = 100,
        final_k: int = 10,
        similarity_threshold: float = 0.0,
        **search_kwargs
    ) -> List[RerankResult]:
        """
        검색 + 재순위화 통합 실행
        
        Args:
            query: 검색 쿼리
            search_method: 검색 방법 ("semantic", "keyword", "hybrid")
            initial_k: 1차 검색에서 가져올 후보 수
            final_k: 최종 반환할 결과 수
            similarity_threshold: 유사도 임계값
            **search_kwargs: 추가 검색 매개변수
            
        Returns:
            재순위화된 검색 결과
        """
        logger.info(f"통합 검색 시작: '{query}' (방법: {search_method})")
        
        # 1단계: 초기 검색
        if search_method == "semantic":
            initial_results = self.search_engine.semantic_search(
                query, top_k=initial_k, threshold=similarity_threshold, **search_kwargs
            )
        elif search_method == "keyword":
            initial_results = self.search_engine.keyword_search(
                query, top_k=initial_k, **search_kwargs
            )
        elif search_method == "colbert":
            initial_results = self.search_engine.colbert_search(
                query, top_k=initial_k, threshold=similarity_threshold, **search_kwargs
            )
        elif search_method == "hybrid":
            initial_results = self.search_engine.hybrid_search(
                query, top_k=initial_k, threshold=similarity_threshold, **search_kwargs
            )
        else:
            raise ValueError(f"지원하지 않는 검색 방법: {search_method}")
        
        logger.info(f"1차 검색 완료: {len(initial_results)}개 결과")
        
        if not initial_results:
            logger.info("검색 결과가 없습니다.")
            return []
        
        # 2단계: 재순위화
        rerank_results = self.reranker.rerank(
            query=query,
            search_results=initial_results,
            top_k=final_k
        )
        
        logger.info(f"재순위화 완료: {len(rerank_results)}개 최종 결과")
        
        return rerank_results


def test_reranker():
    """Reranker 테스트 함수"""
    print("🧪 BGE Reranker 테스트")
    
    # 의존성 체크
    if not RERANKER_AVAILABLE:
        print("❌ FlagEmbedding이 설치되지 않아 테스트를 건너뜁니다.")
        return False
    
    try:
        # Reranker 초기화
        reranker = BGEReranker(device="cpu")  # 테스트용 CPU 사용
        
        if not reranker.is_available():
            print("❌ Reranker 초기화 실패")
            return False
        
        print("✅ Reranker 초기화 성공")
        print(f"   모델: {reranker.model_name}")
        print(f"   디바이스: {reranker.device}")
        
        return True
        
    except Exception as e:
        print(f"❌ 테스트 실패: {e}")
        return False


if __name__ == "__main__":
    test_reranker()