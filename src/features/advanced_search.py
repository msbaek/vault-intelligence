#!/usr/bin/env python3
"""
Advanced Search Engine for Vault Intelligence System V2

Sentence Transformers 기반 의미적 검색 및 하이브리드 검색 엔진
"""

import os
import re
import logging
from typing import List, Dict, Optional, Tuple, Union
from pathlib import Path
from dataclasses import dataclass, asdict
from datetime import datetime
import numpy as np
from collections import defaultdict

try:
    from sklearn.metrics.pairwise import cosine_similarity
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

from ..core.sentence_transformer_engine import SentenceTransformerEngine
from ..core.embedding_cache import EmbeddingCache, CachedEmbedding
from ..core.vault_processor import VaultProcessor, Document

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """검색 결과"""
    document: Document
    similarity_score: float
    match_type: str  # "semantic", "keyword", "hybrid"
    matched_keywords: List[str] = None
    snippet: str = ""
    rank: int = 0


@dataclass 
class SearchQuery:
    """검색 쿼리"""
    text: str
    tags: List[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    min_word_count: Optional[int] = None
    max_word_count: Optional[int] = None
    exclude_paths: List[str] = None


class AdvancedSearchEngine:
    """고급 검색 엔진"""
    
    def __init__(
        self,
        vault_path: str,
        cache_dir: str,
        config: Dict = None
    ):
        """
        Args:
            vault_path: Vault 경로
            cache_dir: 캐시 디렉토리
            config: 검색 설정
        """
        self.vault_path = Path(vault_path)
        self.cache_dir = cache_dir
        self.config = config or {}
        
        # 핵심 컴포넌트 초기화 (성능 최적화 설정)
        self.engine = SentenceTransformerEngine(
            model_name=self.config.get('model', {}).get('name', 'BAAI/bge-m3'),
            cache_dir=self.config.get('model', {}).get('cache_folder', 'models'),
            device=self.config.get('model', {}).get('device'),
            use_fp16=self.config.get('model', {}).get('use_fp16', False),
            batch_size=self.config.get('model', {}).get('batch_size', 4),
            max_length=self.config.get('model', {}).get('max_length', 4096),
            num_workers=self.config.get('model', {}).get('num_workers', 6)
        )
        
        self.cache = EmbeddingCache(cache_dir)
        
        self.processor = VaultProcessor(
            str(vault_path),
            excluded_dirs=self.config.get('vault', {}).get('excluded_dirs'),
            excluded_files=self.config.get('vault', {}).get('excluded_files'),
            file_extensions=self.config.get('vault', {}).get('file_extensions'),
            include_folders=self.config.get('vault', {}).get('include_folders'),
            exclude_folders=self.config.get('vault', {}).get('exclude_folders'),
            min_word_count=self.config.get('vault', {}).get('min_word_count', 10)
        )
        
        # 문서 및 임베딩 캐시
        self.documents: List[Document] = []
        self.embeddings: Optional[np.ndarray] = None
        self.indexed = False
        self.is_sampled = False
        self.sample_size = None
        
        logger.info(f"고급 검색 엔진 초기화: {vault_path}")
        
        # 기존 인덱스 자동 로드 시도
        self.load_index()
    
    def build_index(self, force_rebuild: bool = False, progress_callback=None, sample_size: Optional[int] = None) -> bool:
        """검색 인덱스 구축
        
        Args:
            force_rebuild: 강제 재구축 여부
            progress_callback: 진행률 콜백
            sample_size: 샘플링할 문서 수 (None이면 전체 처리)
        """
        try:
            logger.info("검색 인덱스 구축 시작...")
            
            # 문서 처리
            self.documents = self.processor.process_all_files(progress_callback)
            logger.info(f"처리된 문서: {len(self.documents)}개")
            
            if not self.documents:
                logger.warning("처리할 문서가 없습니다.")
                return False
            
            # 대규모 vault에 대한 자동 샘플링 권장
            if sample_size is None and len(self.documents) > 1000:
                recommended_size = min(500, len(self.documents) // 2)
                logger.warning(f"⚠️  대규모 vault 감지 ({len(self.documents)}개 문서)")
                logger.warning(f"📊 성능 최적화를 위해 --sample-size {recommended_size} 옵션 사용을 권장합니다")
            
            # BGE-M3 임베딩 엔진 훈련 (샘플링 지원)
            all_contents = [doc.content for doc in self.documents]
            all_paths = [doc.path for doc in self.documents]
            self.engine.fit_documents(all_contents, all_paths, sample_size=sample_size)
            logger.info("BGE-M3 임베딩 엔진 훈련 완료")
            
            # 샘플링 모드일 때는 BGE-M3 엔진의 임베딩을 직접 사용
            if sample_size and sample_size < len(self.documents):
                logger.info("📊 샘플링 모드: BGE-M3 엔진의 임베딩을 직접 사용")
                embeddings_list = []
                
                # BGE-M3 엔진에서 샘플링된 인덱스 계산
                step = len(self.documents) // sample_size
                sample_indices = list(range(0, len(self.documents), step))[:sample_size]
                
                # 샘플링된 문서들만 선택
                sampled_documents = [self.documents[i] for i in sample_indices]
                
                # BGE-M3 엔진에서 생성된 임베딩 직접 사용
                if hasattr(self.engine, 'dense_embeddings') and self.engine.dense_embeddings is not None:
                    for i, doc in enumerate(sampled_documents):
                        if i < len(self.engine.dense_embeddings):
                            doc.embedding = self.engine.dense_embeddings[i]
                            embeddings_list.append(self.engine.dense_embeddings[i])
                        else:
                            # 폴백: 제로 벡터
                            doc.embedding = np.zeros(self.engine.embedding_dimension)
                            embeddings_list.append(doc.embedding)
                    
                    self.documents = sampled_documents
                    self.embeddings = np.array(embeddings_list)
                    self.indexed = True
                    self.is_sampled = True
                    self.sample_size = len(sampled_documents)
                    
                    logger.info(f"✅ 샘플링 인덱스 구축 완료: {len(sampled_documents)}개 문서")
                    
                    # 샘플링 인덱스 저장
                    self.save_index()
                    
                    return True
            
            # 전체 문서 처리 (기존 로직)
            embeddings_list = []
            cache_hits = 0
            new_embeddings = 0
            
            for i, doc in enumerate(self.documents):
                try:
                    # 캐시에서 임베딩 조회
                    cached = self.cache.get_embedding(
                        str(self.vault_path / doc.path), 
                        doc.file_hash
                    )
                    
                    if cached and not force_rebuild:
                        # 캐시된 임베딩 검증
                        if (isinstance(cached.embedding, np.ndarray) and 
                            cached.embedding.size > 0 and 
                            not np.allclose(cached.embedding, 0)):
                            embeddings_list.append(cached.embedding)
                            doc.embedding = cached.embedding
                            cache_hits += 1
                        else:
                            logger.warning(f"유효하지 않은 캐시 임베딩: {doc.path}")
                            # 새로 생성
                            embedding = self.engine.encode_text(doc.content)
                            embeddings_list.append(embedding)
                            doc.embedding = embedding
                            self.cache.store_embedding(
                                str(self.vault_path / doc.path),
                                embedding,
                                self.engine.model_name,
                                doc.word_count
                            )
                            new_embeddings += 1
                    else:
                        # 새 임베딩 생성
                        if doc.content and doc.content.strip():
                            embedding = self.engine.encode_text(doc.content)
                            if embedding is not None and not np.allclose(embedding, 0):
                                embeddings_list.append(embedding)
                                doc.embedding = embedding
                                
                                # 캐시에 저장
                                self.cache.store_embedding(
                                    str(self.vault_path / doc.path),
                                    embedding,
                                    self.engine.model_name,
                                    doc.word_count
                                )
                                new_embeddings += 1
                            else:
                                logger.warning(f"0인 임베딩 생성됨: {doc.path}")
                                empty_embedding = np.zeros(self.engine.embedding_dimension)
                                embeddings_list.append(empty_embedding)
                                doc.embedding = empty_embedding
                        else:
                            logger.warning(f"빈 내용 문서: {doc.path}")
                            empty_embedding = np.zeros(self.engine.embedding_dimension)
                            embeddings_list.append(empty_embedding)
                            doc.embedding = empty_embedding
                    
                    # 진행률 콜백
                    if progress_callback and (i + 1) % 50 == 0:
                        progress_callback(i + 1, len(self.documents))
                
                except Exception as e:
                    logger.error(f"임베딩 처리 실패: {doc.path}, {e}")
                    # 빈 임베딩으로 대체
                    empty_embedding = np.zeros(self.engine.embedding_dimension)
                    embeddings_list.append(empty_embedding)
                    doc.embedding = empty_embedding
            
            # 임베딩 배열 생성
            if embeddings_list:
                self.embeddings = np.array(embeddings_list)
                self.indexed = True
                
                logger.info(f"인덱스 구축 완료:")
                logger.info(f"- 문서: {len(self.documents)}개")
                logger.info(f"- 캐시 히트: {cache_hits}개")
                logger.info(f"- 신규 임베딩: {new_embeddings}개")
                logger.info(f"- 임베딩 형태: {self.embeddings.shape}")
                
                # 인덱스 저장
                self.save_index()
                
                return True
            
            return False
        
        except Exception as e:
            logger.error(f"인덱스 구축 실패: {e}")
            return False
    
    def load_index(self) -> bool:
        """저장된 인덱스 로드"""
        try:
            # 샘플링 메타데이터 확인
            metadata_path = os.path.join(self.cache.cache_dir, "index_metadata.json")
            if os.path.exists(metadata_path):
                import json
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    index_metadata = json.load(f)
                
                if index_metadata.get('is_sampled', False):
                    logger.info(f"📊 이전 샘플링 인덱스 발견: {index_metadata.get('sample_size', 'unknown')}개 문서")
                    logger.info("💡 샘플링 인덱스는 빠른 프로토타이핑용입니다.")
                    self.is_sampled = True
                    self.sample_size = index_metadata.get('sample_size')
                else:
                    self.is_sampled = False
                    self.sample_size = None
            
            # 캐시된 임베딩 활용하여 인덱스 복원
            logger.info("📂 캐시된 임베딩으로 인덱스 복원 시도...")
            
            # 문서 로드
            self.documents = self.processor.process_all_files()
            if not self.documents:
                logger.warning("문서를 찾을 수 없습니다.")
                return False
            
            # 캐시된 임베딩과 누락 문서 분리
            cached_embeddings = []
            missing_docs = []
            cached_docs = []
            
            for doc in self.documents:
                cached = self.cache.get_embedding(doc.path, doc.file_hash)
                if cached is None:
                    missing_docs.append(doc)
                else:
                    cached_docs.append(doc)
                    cached_embeddings.append(cached.embedding)
            
            logger.info(f"📊 캐시 상태: {len(cached_docs)}개 있음, {len(missing_docs)}개 누락")
            
            # 누락 문서가 너무 많으면 전체 재구축
            if len(missing_docs) > len(self.documents) * 0.1:  # 10% 이상 누락
                logger.warning(f"⚠️  누락 문서가 많아 전체 재구축 필요: {len(missing_docs)}개")
                return False
            
            # 누락 문서만 임베딩 생성
            if missing_docs:
                logger.info(f"🔄 누락된 {len(missing_docs)}개 문서만 임베딩 생성...")
                missing_texts = [doc.content for doc in missing_docs]
                missing_embeddings = self.engine.encode_texts(missing_texts)
                
                # 캐시에 저장
                for doc, embedding in zip(missing_docs, missing_embeddings):
                    # cache.store_embedding을 직접 호출
                    self.cache.store_embedding(
                        file_path=doc.path,
                        embedding=embedding,
                        model_name=self.engine.model_name,
                        word_count=doc.word_count
                    )
                
                # 모든 임베딩 통합
                all_embeddings = cached_embeddings + missing_embeddings.tolist()
                all_documents = cached_docs + missing_docs
            else:
                all_embeddings = cached_embeddings
                all_documents = cached_docs
            
            # 임베딩 배열 구성
            self.embeddings = np.array(all_embeddings)
            self.documents = all_documents

            # 개별 Document 객체에 임베딩 할당 (duplicate detector 등에서 사용)
            for i, doc in enumerate(self.documents):
                doc.embedding = self.embeddings[i]
            
            # BM25 인덱스 재구축 (빠름)
            from rank_bm25 import BM25Okapi
            tokenized_docs = [doc.content.split() for doc in self.documents]
            self.bm25 = BM25Okapi(tokenized_docs)
            
            self.indexed = True
            logger.info(f"✅ 점진적 인덱스 복원 완료: {len(self.documents)}개 문서 ({len(missing_docs)}개 새로 추가)")
            return True
        except Exception as e:
            logger.error(f"인덱스 로딩 실패: {e}")
            return False
    
    def save_index(self) -> bool:
        """인덱스 저장"""
        try:
            if not self.indexed:
                logger.warning("저장할 인덱스가 없습니다.")
                return False
            
            # BGE-M3 모델 저장 (BGE-M3는 자동으로 캐시됨)
            # 샘플링 메타데이터 저장
            index_metadata = {
                'is_sampled': getattr(self, 'is_sampled', False),
                'sample_size': getattr(self, 'sample_size', None),
                'total_documents': len(self.documents),
                'embedding_dimension': self.engine.embedding_dimension,
                'model_name': self.engine.model_name
            }
            
            metadata_path = os.path.join(self.cache.cache_dir, "index_metadata.json")
            import json
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(index_metadata, f, ensure_ascii=False, indent=2)
            
            logger.info(f"인덱스 저장 완료 - 샘플링: {index_metadata['is_sampled']}, 문서: {index_metadata['total_documents']}개")
            return True
        except Exception as e:
            logger.error(f"인덱스 저장 실패: {e}")
            return False
    
    def semantic_search(
        self,
        query: str,
        top_k: int = 10,
        threshold: float = 0.0
    ) -> List[SearchResult]:
        """의미적 검색"""
        if not self.indexed:
            # 인덱스 로드 시도
            if not self.load_index():
                logger.warning("인덱스가 구축되지 않았습니다.")
                return []
        
        try:
            # 쿼리 임베딩 생성
            query_embedding = self.engine.encode_text(query)
            
            # 유사도 계산
            similarities = self.engine.calculate_similarities(
                query_embedding, 
                self.embeddings
            )
            
            # 상위 결과 선택
            results = self.engine.find_most_similar(
                query_embedding,
                self.embeddings,
                top_k=min(top_k, len(self.documents))
            )
            
            # SearchResult 객체 생성
            search_results = []
            for rank, (idx, similarity) in enumerate(results):
                if similarity >= threshold:
                    snippet = self._generate_snippet(self.documents[idx], query)
                    
                    result = SearchResult(
                        document=self.documents[idx],
                        similarity_score=similarity,
                        match_type="semantic",
                        snippet=snippet,
                        rank=rank + 1
                    )
                    search_results.append(result)
            
            logger.info(f"의미적 검색 완료: {len(search_results)}개 결과")
            return search_results
        
        except Exception as e:
            logger.error(f"의미적 검색 실패: {e}")
            return []
    
    def keyword_search(
        self,
        query: str,
        top_k: int = 10,
        case_sensitive: bool = False
    ) -> List[SearchResult]:
        """키워드 검색"""
        if not self.documents:
            logger.warning("문서가 로드되지 않았습니다.")
            return []
        
        try:
            keywords = self._extract_keywords(query)
            results = []
            
            for doc in self.documents:
                match_score, matched_kw = self._calculate_keyword_match(
                    doc, keywords, case_sensitive
                )
                
                if match_score > 0:
                    snippet = self._generate_snippet(doc, query)
                    
                    result = SearchResult(
                        document=doc,
                        similarity_score=match_score,
                        match_type="keyword",
                        matched_keywords=matched_kw,
                        snippet=snippet
                    )
                    results.append(result)
            
            # 점수 순으로 정렬
            results.sort(key=lambda x: x.similarity_score, reverse=True)
            
            # 순위 할당 및 상위 k개 선택
            for rank, result in enumerate(results[:top_k]):
                result.rank = rank + 1
            
            logger.info(f"키워드 검색 완료: {len(results[:top_k])}개 결과")
            return results[:top_k]
        
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
    ) -> List[SearchResult]:
        """하이브리드 검색 (의미적 + 키워드)"""
        try:
            # 각각의 검색 수행
            semantic_results = self.semantic_search(query, top_k * 2, 0.0)
            keyword_results = self.keyword_search(query, top_k * 2)
            
            # 결과 통합
            combined_scores = defaultdict(float)
            all_results = {}
            
            # 의미적 검색 결과 처리
            for result in semantic_results:
                doc_path = result.document.path
                combined_scores[doc_path] += result.similarity_score * semantic_weight
                all_results[doc_path] = result
                all_results[doc_path].match_type = "hybrid"
            
            # 키워드 검색 결과 처리  
            for result in keyword_results:
                doc_path = result.document.path
                combined_scores[doc_path] += result.similarity_score * keyword_weight
                
                if doc_path in all_results:
                    # 키워드 정보 추가
                    all_results[doc_path].matched_keywords = result.matched_keywords
                else:
                    all_results[doc_path] = result
                    all_results[doc_path].match_type = "hybrid"
            
            # 통합 점수로 정렬
            final_results = []
            for doc_path, combined_score in combined_scores.items():
                if combined_score >= threshold:
                    result = all_results[doc_path]
                    result.similarity_score = combined_score
                    final_results.append(result)
            
            final_results.sort(key=lambda x: x.similarity_score, reverse=True)
            
            # 순위 할당
            for rank, result in enumerate(final_results[:top_k]):
                result.rank = rank + 1
            
            logger.info(f"하이브리드 검색 완료: {len(final_results[:top_k])}개 결과")
            return final_results[:top_k]
        
        except Exception as e:
            logger.error(f"하이브리드 검색 실패: {e}")
            return []
    
    def advanced_search(self, search_query: SearchQuery) -> List[SearchResult]:
        """고급 검색 (필터링 포함)"""
        try:
            # 기본 하이브리드 검색 수행
            results = self.hybrid_search(
                search_query.text,
                top_k=100,  # 넉넉하게 가져온 후 필터링
                threshold=self.config.get('search', {}).get('similarity_threshold', 0.0)
            )
            
            # 필터링 적용
            filtered_results = self._apply_filters(results, search_query)
            
            logger.info(f"고급 검색 완료: {len(filtered_results)}개 결과")
            return filtered_results
        
        except Exception as e:
            logger.error(f"고급 검색 실패: {e}")
            return []
    
    def _apply_filters(
        self, 
        results: List[SearchResult], 
        query: SearchQuery
    ) -> List[SearchResult]:
        """검색 결과에 필터 적용"""
        filtered = results
        
        # 태그 필터
        if query.tags:
            tag_set = set(tag.lower() for tag in query.tags)
            filtered = [
                r for r in filtered
                if any(tag.lower() in tag_set for tag in r.document.tags)
            ]
        
        # 날짜 필터
        if query.date_from:
            filtered = [
                r for r in filtered
                if r.document.modified_at >= query.date_from
            ]
        
        if query.date_to:
            filtered = [
                r for r in filtered  
                if r.document.modified_at <= query.date_to
            ]
        
        # 단어 수 필터
        if query.min_word_count:
            filtered = [
                r for r in filtered
                if r.document.word_count >= query.min_word_count
            ]
        
        if query.max_word_count:
            filtered = [
                r for r in filtered
                if r.document.word_count <= query.max_word_count
            ]
        
        # 경로 제외 필터
        if query.exclude_paths:
            exclude_set = set(query.exclude_paths)
            filtered = [
                r for r in filtered
                if r.document.path not in exclude_set
            ]
        
        return filtered
    
    def _extract_keywords(self, query: str) -> List[str]:
        """쿼리에서 키워드 추출"""
        # 기본적인 키워드 분리 (공백, 구두점 기준)
        keywords = re.findall(r'[a-zA-Z가-힣0-9]+', query)
        return [kw.lower() for kw in keywords if len(kw) >= 2]
    
    def _calculate_keyword_match(
        self,
        document: Document,
        keywords: List[str],
        case_sensitive: bool = False
    ) -> Tuple[float, List[str]]:
        """문서와 키워드 매칭 점수 계산"""
        if not keywords:
            return 0.0, []
        
        content = document.content if case_sensitive else document.content.lower()
        title = document.title if case_sensitive else document.title.lower()
        tags = document.tags if case_sensitive else [tag.lower() for tag in document.tags]
        
        matched_keywords = []
        total_score = 0.0
        
        for keyword in keywords:
            kw = keyword if case_sensitive else keyword.lower()
            
            # 제목 매칭 (가중치 3.0)
            if kw in title:
                total_score += 3.0
                matched_keywords.append(keyword)
            
            # 태그 매칭 (가중치 2.0)
            elif any(kw in tag for tag in tags):
                total_score += 2.0
                matched_keywords.append(keyword)
            
            # 본문 매칭 (가중치 1.0)
            elif kw in content:
                # 본문에서의 빈도수 고려
                frequency = content.count(kw)
                total_score += min(frequency * 1.0, 5.0)  # 최대 5점
                matched_keywords.append(keyword)
        
        # 정규화 (매칭된 키워드 비율)
        match_ratio = len(matched_keywords) / len(keywords)
        final_score = total_score * match_ratio
        
        return final_score, matched_keywords
    
    def _generate_snippet(self, document: Document, query: str, max_length: int = 150) -> str:
        """검색 결과 스니펫 생성"""
        try:
            keywords = self._extract_keywords(query)
            content = document.content
            
            if not keywords:
                return content[:max_length] + "..." if len(content) > max_length else content
            
            # 키워드가 포함된 문장 찾기
            sentences = re.split(r'[.!?]\s+', content)
            best_sentence = ""
            best_score = 0
            
            for sentence in sentences:
                score = sum(1 for kw in keywords if kw.lower() in sentence.lower())
                if score > best_score:
                    best_score = score
                    best_sentence = sentence
            
            if best_sentence:
                snippet = best_sentence.strip()
                if len(snippet) > max_length:
                    snippet = snippet[:max_length] + "..."
                return snippet
            
            # 기본 스니펫
            return content[:max_length] + "..." if len(content) > max_length else content
        
        except Exception as e:
            logger.error(f"스니펫 생성 실패: {e}")
            return document.content[:max_length] + "..."
    
    def get_search_statistics(self) -> Dict:
        """검색 엔진 통계"""
        try:
            cache_stats = self.cache.get_statistics()
            vault_stats = self.processor.get_vault_statistics()
            
            return {
                "indexed_documents": len(self.documents),
                "embedding_dimension": self.engine.embedding_dimension,
                "model_name": self.engine.model_name,
                "cache_statistics": cache_stats,
                "vault_statistics": vault_stats,
                "indexed": self.indexed
            }
        
        except Exception as e:
            logger.error(f"통계 생성 실패: {e}")
            return {}
    
    def search_with_reranking(
        self,
        query: str,
        search_method: str = "hybrid",
        initial_k: int = 100,
        final_k: int = 10,
        threshold: float = 0.0,
        use_reranker: bool = True,
        **search_kwargs
    ) -> List[SearchResult]:
        """
        재순위화를 포함한 고급 검색
        
        Args:
            query: 검색 쿼리
            search_method: 검색 방법 ("semantic", "keyword", "hybrid")
            initial_k: 1차 검색에서 가져올 후보 수
            final_k: 최종 반환할 결과 수
            threshold: 유사도 임계값
            use_reranker: 재순위화 사용 여부
            **search_kwargs: 추가 검색 매개변수
            
        Returns:
            재순위화된 검색 결과 (SearchResult 형태로 변환)
        """
        # Reranker가 요청되었지만 사용 불가능한 경우
        if use_reranker:
            try:
                from .reranker import BGEReranker, RerankerPipeline
                
                # 설정에서 reranker 정보 가져오기
                reranker_config = self.config.get('reranker', {})
                
                # Reranker 초기화
                reranker = BGEReranker(
                    model_name=reranker_config.get('model_name', 'BAAI/bge-reranker-v2-m3'),
                    use_fp16=reranker_config.get('use_fp16', True),
                    cache_folder=reranker_config.get('cache_folder', self.config.get('model', {}).get('cache_folder')),
                    device=reranker_config.get('device', self.config.get('model', {}).get('device'))
                )
                
                if reranker.is_available():
                    # 파이프라인 생성 및 실행
                    pipeline = RerankerPipeline(self, reranker, self.config)
                    rerank_results = pipeline.search_and_rerank(
                        query=query,
                        search_method=search_method,
                        initial_k=initial_k,
                        final_k=final_k,
                        similarity_threshold=threshold,
                        **search_kwargs
                    )
                    
                    # RerankResult를 SearchResult로 변환
                    search_results = []
                    for rerank_result in rerank_results:
                        # 원본 SearchResult를 복사하고 점수 업데이트
                        search_result = rerank_result.search_result
                        search_result.similarity_score = rerank_result.rerank_score
                        search_result.rank = rerank_result.new_rank + 1
                        search_result.match_type = f"{search_result.match_type}_reranked"
                        search_results.append(search_result)
                    
                    logger.info(f"재순위화 검색 완료: {len(search_results)}개 결과")
                    return search_results
                else:
                    logger.warning("Reranker를 사용할 수 없습니다. 일반 검색으로 진행합니다.")
                    use_reranker = False
                    
            except ImportError:
                logger.warning("Reranker 모듈을 가져올 수 없습니다. 일반 검색으로 진행합니다.")
                use_reranker = False
            except Exception as e:
                logger.warning(f"Reranker 초기화 실패: {e}. 일반 검색으로 진행합니다.")
                use_reranker = False
        
        # 일반 검색 수행 (reranker 없이)
        if search_method == "semantic":
            return self.semantic_search(query, top_k=final_k, threshold=threshold, **search_kwargs)
        elif search_method == "keyword":
            return self.keyword_search(query, top_k=final_k, **search_kwargs)
        elif search_method == "colbert":
            return self.colbert_search(query, top_k=final_k, threshold=threshold, **search_kwargs)
        elif search_method == "hybrid":
            return self.hybrid_search(query, top_k=final_k, threshold=threshold, **search_kwargs)
        else:
            raise ValueError(f"지원하지 않는 검색 방법: {search_method}")
    
    def colbert_search(
        self,
        query: str,
        top_k: int = 10,
        threshold: float = 0.0
    ) -> List[SearchResult]:
        """
        ColBERT 기반 토큰 수준 late interaction 검색
        
        Args:
            query: 검색 쿼리
            top_k: 반환할 상위 결과 수
            threshold: 유사도 임계값
            
        Returns:
            ColBERT 검색 결과
        """
        try:
            from .colbert_search import ColBERTSearchEngine
            
            # ColBERT 엔진 설정
            colbert_config = self.config.get('colbert', {})
            
            # ColBERT 엔진 초기화 (캐시 포함)
            colbert_engine = ColBERTSearchEngine(
                model_name=colbert_config.get('model_name', 'BAAI/bge-m3'),
                device=colbert_config.get('device', self.config.get('model', {}).get('device')),
                use_fp16=colbert_config.get('use_fp16', True),
                cache_folder=colbert_config.get('cache_folder', self.config.get('model', {}).get('cache_folder')),
                max_length=colbert_config.get('max_length', self.config.get('model', {}).get('max_length', 4096)),
                cache_dir=self.cache_dir,
                enable_cache=colbert_config.get('enable_cache', True)
            )
            
            if not colbert_engine.is_available():
                logger.warning("ColBERT 엔진을 사용할 수 없습니다. 의미적 검색으로 대체합니다.")
                return self.semantic_search(query, top_k, threshold)
            
            # 인덱스가 없으면 구축 (캐시를 활용하여 전체 문서 처리 가능)
            if not colbert_engine.is_indexed:
                logger.info("ColBERT 인덱스 구축 중...")
                max_docs = colbert_config.get('max_documents', None)  # None이면 전체 문서
                force_rebuild = False  # 기본적으로 캐시 활용
                
                if not colbert_engine.build_index(
                    self.documents, 
                    max_documents=max_docs,
                    force_rebuild=force_rebuild
                ):
                    logger.error("ColBERT 인덱스 구축 실패")
                    return self.semantic_search(query, top_k, threshold)
            
            # ColBERT 검색 수행
            colbert_results = colbert_engine.search(query, top_k, threshold)
            
            # SearchResult 형태로 변환
            search_results = colbert_engine.convert_to_search_results(colbert_results)
            
            logger.info(f"ColBERT 검색 완료: {len(search_results)}개 결과")
            return search_results
            
        except ImportError:
            logger.warning("ColBERT 모듈을 가져올 수 없습니다. 의미적 검색으로 대체합니다.")
            return self.semantic_search(query, top_k, threshold)
        except Exception as e:
            logger.error(f"ColBERT 검색 실패: {e}. 의미적 검색으로 대체합니다.")
            return self.semantic_search(query, top_k, threshold)
    
    def expanded_search(
        self,
        query: str,
        search_method: str = "hybrid",
        top_k: int = 10,
        threshold: float = 0.0,
        include_synonyms: bool = True,
        include_hyde: bool = True,
        **search_kwargs
    ) -> List[SearchResult]:
        """
        쿼리 확장을 포함한 고급 검색
        
        Args:
            query: 검색 쿼리
            search_method: 검색 방법 ("semantic", "keyword", "hybrid", "colbert")
            top_k: 반환할 상위 결과 수
            threshold: 유사도 임계값
            include_synonyms: 동의어 포함 여부
            include_hyde: HyDE 포함 여부
            **search_kwargs: 추가 검색 매개변수
            
        Returns:
            확장된 쿼리로 검색한 결과
        """
        try:
            from .query_expansion import QueryExpansionEngine
            
            # 쿼리 확장 설정
            expansion_config = self.config.get('query_expansion', {})
            
            # 쿼리 확장 엔진 초기화
            expansion_engine = QueryExpansionEngine(
                model_name=expansion_config.get('model_name', 'BAAI/bge-m3'),
                device=expansion_config.get('device', self.config.get('model', {}).get('device')),
                use_fp16=expansion_config.get('use_fp16', True),
                enable_hyde=expansion_config.get('enable_hyde', True)
            )
            
            # 쿼리 확장 실행
            expanded_query = expansion_engine.expand_query(
                query=query,
                include_synonyms=include_synonyms,
                include_hyde=include_hyde,
                max_synonyms=expansion_config.get('max_synonyms', 3)
            )
            
            logger.info(f"쿼리 확장 완료: {expanded_query.expansion_method}")
            
            # 여러 검색 쿼리 생성
            search_queries = expansion_engine.create_expanded_search_queries(expanded_query)
            
            # 각 쿼리로 검색 수행 및 결과 통합
            all_results = []
            seen_docs = set()  # 중복 문서 제거용
            
            for i, search_query in enumerate(search_queries):
                try:
                    # 각 쿼리별 가중치 (원본 쿼리가 가장 높음)
                    weight = 1.0 - (i * 0.1)  # 0.9, 0.8, 0.7, ...
                    weight = max(weight, 0.3)  # 최소 0.3
                    
                    # 검색 실행
                    if search_method == "semantic":
                        results = self.semantic_search(search_query, top_k * 2, threshold, **search_kwargs)
                    elif search_method == "keyword":
                        results = self.keyword_search(search_query, top_k * 2, **search_kwargs)
                    elif search_method == "hybrid":
                        results = self.hybrid_search(search_query, top_k * 2, threshold, **search_kwargs)
                    elif search_method == "colbert":
                        results = self.colbert_search(search_query, top_k * 2, threshold, **search_kwargs)
                    else:
                        continue
                    
                    # 결과 가중치 적용 및 중복 제거
                    for result in results:
                        doc_id = result.document.path
                        if doc_id not in seen_docs:
                            # 점수에 가중치 적용
                            result.similarity_score *= weight
                            result.match_type = f"{result.match_type}_expanded"
                            
                            # 확장 정보 추가
                            if i == 0:
                                result.match_type += "_original"
                            elif search_query in expanded_query.synonyms:
                                result.match_type += "_synonym"
                            elif search_query == expanded_query.hypothetical_doc:
                                result.match_type += "_hyde"
                            else:
                                result.match_type += "_related"
                            
                            all_results.append(result)
                            seen_docs.add(doc_id)
                
                except Exception as e:
                    logger.warning(f"확장 쿼리 '{search_query[:50]}...' 검색 실패: {e}")
                    continue
            
            # 통합 결과 정렬 및 상위 K개 선택
            all_results.sort(key=lambda x: x.similarity_score, reverse=True)
            final_results = all_results[:top_k]
            
            # 순위 재할당
            for rank, result in enumerate(final_results):
                result.rank = rank + 1
            
            logger.info(f"확장 검색 완료: {len(search_queries)}개 쿼리로 {len(final_results)}개 결과")
            
            return final_results
            
        except ImportError:
            logger.warning("쿼리 확장 모듈을 가져올 수 없습니다. 일반 검색으로 진행합니다.")
            # 폴백: 일반 검색
            if search_method == "semantic":
                return self.semantic_search(query, top_k, threshold, **search_kwargs)
            elif search_method == "keyword":
                return self.keyword_search(query, top_k, **search_kwargs)
            elif search_method == "hybrid":
                return self.hybrid_search(query, top_k, threshold, **search_kwargs)
            elif search_method == "colbert":
                return self.colbert_search(query, top_k, threshold, **search_kwargs)
            else:
                raise ValueError(f"지원하지 않는 검색 방법: {search_method}")
        except Exception as e:
            logger.error(f"확장 검색 실패: {e}. 일반 검색으로 대체합니다.")
            # 폴백: 일반 검색
            if search_method == "semantic":
                return self.semantic_search(query, top_k, threshold, **search_kwargs)
            elif search_method == "keyword":
                return self.keyword_search(query, top_k, **search_kwargs)
            elif search_method == "hybrid":
                return self.hybrid_search(query, top_k, threshold, **search_kwargs)
            elif search_method == "colbert":
                return self.colbert_search(query, top_k, threshold, **search_kwargs)
            else:
                raise ValueError(f"지원하지 않는 검색 방법: {search_method}")
    
    def get_related_documents(
        self,
        document_path: str,
        top_k: int = 5,
        include_centrality_boost: bool = True,
        similarity_threshold: float = 0.3
    ) -> List[SearchResult]:
        """
        특정 문서와 관련된 문서들을 추천합니다.
        
        Args:
            document_path: 기준이 되는 문서 경로
            top_k: 반환할 관련 문서 수
            include_centrality_boost: 중심성 점수를 반영할지 여부
            similarity_threshold: 유사도 임계값
            
        Returns:
            관련 문서 목록 (SearchResult)
        """
        try:
            if not self.indexed:
                logger.warning("인덱스가 구축되지 않았습니다.")
                return []
            
            # 기준 문서 찾기
            base_document = None
            for doc in self.documents:
                if doc.path == document_path or doc.title == document_path:
                    base_document = doc
                    break
            
            if base_document is None:
                logger.warning(f"문서를 찾을 수 없습니다: {document_path}")
                return []
            
            # 기준 문서의 임베딩 가져오기
            base_cached = self.cache.get_embedding(base_document.path)
            if base_cached is None:
                logger.warning(f"문서에 임베딩이 없습니다: {document_path}")
                return []
            base_embedding = base_cached.embedding
            
            # 지식 그래프 기반 관련성 점수 계산 (옵션)
            centrality_scores = {}
            if include_centrality_boost:
                centrality_scores = self._get_centrality_scores()
            
            # 유사도 기반 관련 문서 찾기
            related_results = []
            base_embedding = base_embedding.reshape(1, -1)
            
            for doc in self.documents:
                # 자기 자신 제외
                if doc.path == base_document.path:
                    continue
                    
                # 문서의 임베딩 가져오기
                doc_cached = self.cache.get_embedding(doc.path)
                if doc_cached is None:
                    continue
                doc_embedding = doc_cached.embedding
                
                # 의미적 유사도 계산
                doc_embedding = doc_embedding.reshape(1, -1)
                if SKLEARN_AVAILABLE:
                    similarity = cosine_similarity(base_embedding, doc_embedding)[0][0]
                else:
                    # NumPy로 코사인 유사도 계산
                    similarity = np.dot(base_embedding[0], doc_embedding[0]) / (
                        np.linalg.norm(base_embedding[0]) * np.linalg.norm(doc_embedding[0])
                    )
                
                if similarity < similarity_threshold:
                    continue
                
                # 태그 기반 가중치 추가
                tag_boost = self._calculate_tag_similarity(base_document, doc)
                
                # 중심성 점수 가중치 (옵션)
                centrality_boost = 0.0
                if include_centrality_boost and doc.path in centrality_scores:
                    centrality_boost = centrality_scores[doc.path] * 0.2  # 20% 가중치
                
                # 최종 점수 계산
                final_score = similarity + tag_boost + centrality_boost
                
                # SearchResult 생성
                result = SearchResult(
                    document=doc,
                    similarity_score=final_score,
                    match_type="related_semantic",
                    matched_keywords=[],
                    snippet=doc.content[:150] + "..." if len(doc.content) > 150 else doc.content
                )
                
                related_results.append(result)
            
            # 점수별 정렬 및 상위 K개 선택
            related_results.sort(key=lambda x: x.similarity_score, reverse=True)
            final_results = related_results[:top_k]
            
            # 순위 할당
            for rank, result in enumerate(final_results):
                result.rank = rank + 1
            
            logger.info(f"관련 문서 추천 완료: {base_document.title}에 대한 {len(final_results)}개 문서")
            return final_results
            
        except Exception as e:
            logger.error(f"관련 문서 추천 실패: {e}")
            return []
    
    def search_with_related(
        self,
        query: str,
        search_method: str = "hybrid", 
        top_k: int = 10,
        include_related: int = 3,
        **search_kwargs
    ) -> Tuple[List[SearchResult], List[SearchResult]]:
        """
        검색 결과와 함께 관련 문서들을 추천합니다.
        
        Args:
            query: 검색 쿼리
            search_method: 검색 방법
            top_k: 주요 검색 결과 수
            include_related: 각 결과별 관련 문서 수
            **search_kwargs: 추가 검색 매개변수
            
        Returns:
            (주요 검색 결과, 관련 문서 목록) 튜플
        """
        try:
            # 기본 검색 수행
            if search_method == "semantic":
                main_results = self.semantic_search(query, top_k, **search_kwargs)
            elif search_method == "keyword":
                main_results = self.keyword_search(query, top_k, **search_kwargs)
            elif search_method == "hybrid":
                main_results = self.hybrid_search(query, top_k, **search_kwargs)
            elif search_method == "colbert":
                main_results = self.colbert_search(query, top_k, **search_kwargs)
            else:
                raise ValueError(f"지원하지 않는 검색 방법: {search_method}")
            
            if not main_results:
                return [], []
            
            # 상위 결과들에 대한 관련 문서 수집
            all_related = []
            seen_docs = {result.document.path for result in main_results}  # 중복 방지
            
            for main_result in main_results[:3]:  # 상위 3개 결과만 사용
                related_docs = self.get_related_documents(
                    main_result.document.path, 
                    top_k=include_related + 2,  # 여유분 추가
                    similarity_threshold=0.2  # 낮은 임계값으로 더 많은 문서 포함
                )
                
                # 중복 제거하며 추가
                for related in related_docs:
                    if related.document.path not in seen_docs:
                        # 관련 문서임을 표시
                        related.match_type = f"related_to_{main_result.document.title[:20]}"
                        all_related.append(related)
                        seen_docs.add(related.document.path)
                        
                        if len(all_related) >= include_related * 3:  # 적절한 수준에서 중단
                            break
                
                if len(all_related) >= include_related * 3:
                    break
            
            # 관련 문서들을 점수별로 재정렬
            all_related.sort(key=lambda x: x.similarity_score, reverse=True)
            final_related = all_related[:include_related * 2]  # 최종 관련 문서 수
            
            # 순위 재할당
            for rank, result in enumerate(final_related):
                result.rank = rank + 1
            
            logger.info(f"검색+관련문서 완료: 주요 {len(main_results)}개, 관련 {len(final_related)}개")
            return main_results, final_related
            
        except Exception as e:
            logger.error(f"검색+관련문서 실패: {e}")
            return [], []
    
    def _get_centrality_scores(self) -> Dict[str, float]:
        """지식 그래프에서 중심성 점수를 가져옵니다."""
        try:
            from .knowledge_graph import KnowledgeGraphBuilder
            
            # 지식 그래프 구축 (낮은 임계값 사용)
            graph_config = self.config.get('graph', {})
            if 'min_word_count' not in graph_config:
                graph_config['min_word_count'] = 5  # 낮은 임계값 설정
            graph_builder = KnowledgeGraphBuilder(self, graph_config)
            knowledge_graph = graph_builder.build_graph()
            
            if knowledge_graph.centrality_scores:
                # 노드 ID를 문서 경로로 매핑
                path_scores = {}
                for node in knowledge_graph.nodes:
                    if node.node_type == "document":
                        node_id = node.id
                        centrality = knowledge_graph.centrality_scores.get(node_id, 0.0)
                        path_scores[node.path] = centrality
                
                return path_scores
            
            return {}
            
        except Exception as e:
            logger.debug(f"중심성 점수 계산 실패: {e}")
            return {}
    
    def _calculate_tag_similarity(self, doc1: Document, doc2: Document) -> float:
        """두 문서 간의 태그 유사도를 계산합니다."""
        if not doc1.tags or not doc2.tags:
            return 0.0
        
        tags1 = set(doc1.tags)
        tags2 = set(doc2.tags)
        
        # Jaccard 유사도
        intersection = len(tags1 & tags2)
        union = len(tags1 | tags2)
        
        if union == 0:
            return 0.0
        
        # 태그 유사도에 가중치 적용 (최대 0.2)
        tag_similarity = (intersection / union) * 0.2
        
        return tag_similarity
    
    def search_with_centrality_boost(
        self,
        query: str,
        search_method: str = "hybrid",
        top_k: int = 10,
        centrality_weight: float = 0.2,
        **search_kwargs
    ) -> List[SearchResult]:
        """
        중심성 점수를 반영한 검색
        
        Args:
            query: 검색 쿼리
            search_method: 검색 방법 ("semantic", "keyword", "hybrid", "colbert")
            top_k: 반환할 상위 결과 수
            centrality_weight: 중심성 점수 가중치 (0.0 - 1.0)
            **search_kwargs: 추가 검색 매개변수
            
        Returns:
            중심성 점수가 반영된 검색 결과
        """
        # threshold는 semantic/colbert만 지원
        threshold = search_kwargs.pop('threshold', 0.0)

        try:
            # 기본 검색 수행
            if search_method == "semantic":
                results = self.semantic_search(query, top_k * 2, threshold=threshold, **search_kwargs)
            elif search_method == "keyword":
                results = self.keyword_search(query, top_k * 2, **search_kwargs)
            elif search_method == "hybrid":
                results = self.hybrid_search(query, top_k * 2, **search_kwargs)
            elif search_method == "colbert":
                results = self.colbert_search(query, top_k * 2, threshold=threshold, **search_kwargs)
            else:
                raise ValueError(f"지원하지 않는 검색 방법: {search_method}")
            
            if not results:
                return []
            
            # 중심성 점수 가져오기
            centrality_scores = self._get_centrality_scores()
            
            if not centrality_scores:
                logger.info("중심성 점수가 없어 일반 검색 결과를 반환합니다.")
                return results[:top_k]
            
            # 결과에 중심성 점수 적용
            boosted_results = []
            for result in results:
                doc_path = result.document.path
                centrality_boost = centrality_scores.get(doc_path, 0.0) * centrality_weight
                
                # 새로운 점수 = 원래 점수 + 중심성 부스트
                new_score = result.similarity_score + centrality_boost
                
                # 새로운 SearchResult 생성
                boosted_result = SearchResult(
                    document=result.document,
                    similarity_score=new_score,
                    match_type=f"{result.match_type}_centrality_boosted",
                    matched_keywords=result.matched_keywords,
                    snippet=result.snippet,
                    rank=0  # 재정렬 후 할당
                )
                
                boosted_results.append(boosted_result)
            
            # 새로운 점수로 재정렬
            boosted_results.sort(key=lambda x: x.similarity_score, reverse=True)
            final_results = boosted_results[:top_k]
            
            # 순위 재할당
            for rank, result in enumerate(final_results):
                result.rank = rank + 1
            
            # 순위 변화 로깅
            original_order = [r.document.title for r in results[:top_k]]
            new_order = [r.document.title for r in final_results]
            
            if original_order != new_order:
                logger.info(f"중심성 부스팅으로 순위 변경됨:")
                for i, (orig, new) in enumerate(zip(original_order, new_order)):
                    if orig != new:
                        logger.info(f"  순위 {i+1}: {orig} → {new}")
            
            logger.info(f"중심성 부스팅 검색 완료: {len(final_results)}개 결과")
            return final_results
            
        except Exception as e:
            logger.error(f"중심성 부스팅 검색 실패: {e}")
            # 폴백: 일반 검색 결과 반환
            if search_method == "semantic":
                return self.semantic_search(query, top_k, threshold=threshold, **search_kwargs)
            elif search_method == "keyword":
                return self.keyword_search(query, top_k, **search_kwargs)
            elif search_method == "hybrid":
                return self.hybrid_search(query, top_k, **search_kwargs)
            elif search_method == "colbert":
                return self.colbert_search(query, top_k, threshold=threshold, **search_kwargs)
            else:
                return []
    
    def analyze_knowledge_gaps(
        self,
        similarity_threshold: float = 0.3,
        min_connections: int = 2
    ) -> Dict[str, any]:
        """
        지식 공백을 분석합니다.
        
        Args:
            similarity_threshold: 연결 판정 유사도 임계값
            min_connections: 최소 연결 수 (이보다 적으면 고립으로 판정)
            
        Returns:
            지식 공백 분석 결과
        """
        try:
            if not self.indexed:
                logger.warning("인덱스가 구축되지 않았습니다.")
                return {}
            
            # 지식 그래프 구축
            centrality_scores = self._get_centrality_scores()
            
            # 문서 간 유사도 매트릭스 계산
            doc_similarities = {}
            isolated_docs = []
            weakly_connected_docs = []
            
            for i, doc1 in enumerate(self.documents):
                if doc1.embedding is None:
                    continue
                
                connections = 0
                related_docs = []
                
                for j, doc2 in enumerate(self.documents):
                    if i == j or doc2.embedding is None:
                        continue
                    
                    # 유사도 계산
                    if SKLEARN_AVAILABLE:
                        similarity = cosine_similarity(
                            doc1.embedding.reshape(1, -1),
                            doc2.embedding.reshape(1, -1)
                        )[0][0]
                    else:
                        similarity = np.dot(doc1.embedding, doc2.embedding) / (
                            np.linalg.norm(doc1.embedding) * np.linalg.norm(doc2.embedding)
                        )
                    
                    if similarity >= similarity_threshold:
                        connections += 1
                        related_docs.append({
                            'title': doc2.title,
                            'similarity': float(similarity)
                        })
                
                doc_similarities[doc1.title] = {
                    'connections': connections,
                    'related_docs': related_docs,
                    'centrality': centrality_scores.get(doc1.path, 0.0)
                }
                
                # 고립/약한 연결 문서 분류
                if connections == 0:
                    isolated_docs.append({
                        'title': doc1.title,
                        'path': doc1.path,
                        'word_count': doc1.word_count,
                        'tags': doc1.tags or []
                    })
                elif connections < min_connections:
                    weakly_connected_docs.append({
                        'title': doc1.title,
                        'path': doc1.path,
                        'connections': connections,
                        'word_count': doc1.word_count,
                        'tags': doc1.tags or []
                    })
            
            # 태그별 문서 분포 분석
            tag_distribution = {}
            for doc in self.documents:
                if doc.tags:
                    for tag in doc.tags:
                        if tag not in tag_distribution:
                            tag_distribution[tag] = []
                        tag_distribution[tag].append(doc.title)
            
            # 고립된 태그 찾기
            isolated_tags = {
                tag: docs for tag, docs in tag_distribution.items()
                if len(docs) == 1
            }
            
            # 분석 결과 구성
            analysis_result = {
                'total_documents': len(self.documents),
                'isolated_documents': isolated_docs,
                'weakly_connected_documents': weakly_connected_docs,
                'isolated_tags': isolated_tags,
                'tag_distribution': tag_distribution,
                'document_similarities': doc_similarities,
                'summary': {
                    'isolated_count': len(isolated_docs),
                    'weakly_connected_count': len(weakly_connected_docs),
                    'isolated_tag_count': len(isolated_tags),
                    'total_tags': len(tag_distribution),
                    'isolation_rate': len(isolated_docs) / len(self.documents) if self.documents else 0
                }
            }
            
            logger.info(f"지식 공백 분석 완료:")
            logger.info(f"  - 고립 문서: {len(isolated_docs)}개")
            logger.info(f"  - 약한 연결 문서: {len(weakly_connected_docs)}개")
            logger.info(f"  - 고립 태그: {len(isolated_tags)}개")
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"지식 공백 분석 실패: {e}")
            return {}

    def clean_isolated_tags(self, dry_run: bool = True, top_k: int = 50) -> Dict[str, any]:
        """
        고립 태그(1개 문서에만 존재하는 태그)를 정리합니다.

        Args:
            dry_run: True이면 미리보기만, False이면 실제 제거
            top_k: 표시할 최대 결과 수

        Returns:
            정리 결과 통계
        """
        try:
            if not self.indexed:
                logger.warning("인덱스가 구축되지 않았습니다.")
                return {}

            # 태그별 문서 분포 분석
            tag_distribution = {}
            for doc in self.documents:
                if doc.tags:
                    for tag in doc.tags:
                        if tag not in tag_distribution:
                            tag_distribution[tag] = []
                        tag_distribution[tag].append(doc)

            # 고립 태그: 1개 문서에만 존재하는 태그
            isolated_tags = {
                tag: docs for tag, docs in tag_distribution.items()
                if len(docs) == 1
            }

            if not isolated_tags:
                return {'total_isolated': 0, 'files_affected': 0, 'tags_removed': 0}

            # 파일별로 제거할 태그 그룹핑
            file_tags_map = {}  # {file_path: [tag1, tag2, ...]}
            for tag, docs in isolated_tags.items():
                doc = docs[0]
                abs_path = str(self.vault_path / doc.path)
                if abs_path not in file_tags_map:
                    file_tags_map[abs_path] = []
                file_tags_map[abs_path].append(tag)

            total_tags = len(isolated_tags)
            files_affected = len(file_tags_map)
            tags_removed = 0

            if dry_run:
                # 미리보기: 파일별 제거 대상 태그 출력
                shown = 0
                for file_path, tags in sorted(file_tags_map.items()):
                    if shown >= top_k:
                        break
                    rel_path = str(Path(file_path).relative_to(self.vault_path))
                    print(f"  {rel_path}")
                    for tag in sorted(tags):
                        print(f"    - {tag}")
                    shown += 1

                if files_affected > top_k:
                    print(f"\n  ... 외 {files_affected - top_k}개 파일")
            else:
                # 실제 태그 제거
                for file_path, tags in file_tags_map.items():
                    if self.processor.remove_tags_from_file(file_path, tags):
                        tags_removed += len(tags)

            return {
                'total_isolated': total_tags,
                'files_affected': files_affected,
                'tags_removed': tags_removed,
                'dry_run': dry_run
            }

        except Exception as e:
            logger.error(f"고립 태그 정리 실패: {e}")
            return {}


def test_search_engine():
    """검색 엔진 테스트"""
    import tempfile
    import shutil
    
    try:
        # 임시 vault 생성
        temp_vault = tempfile.mkdtemp()
        temp_cache = tempfile.mkdtemp()
        
        # 테스트 문서들 생성
        test_docs = [
            ("tdd.md", "# TDD 기본 개념\n\nTDD는 테스트 주도 개발 방법론입니다.\n## Red-Green-Refactor\n테스트를 먼저 작성하고 구현합니다."),
            ("refactoring.md", "# 리팩토링\n\n리팩토링은 코드의 구조를 개선하는 과정입니다.\n테스트가 있어야 안전하게 리팩토링할 수 있습니다."),
            ("clean_code.md", "# Clean Code\n\n깨끗한 코드 작성법을 다룹니다.\n좋은 테스트는 깨끗한 코드의 기반입니다.")
        ]
        
        for filename, content in test_docs:
            with open(Path(temp_vault) / filename, 'w', encoding='utf-8') as f:
                f.write(content)
        
        # 검색 엔진 초기화
        config = {
            "model": {"name": "paraphrase-multilingual-mpnet-base-v2"},
            "vault": {"excluded_dirs": [], "file_extensions": [".md"]}
        }
        
        engine = AdvancedSearchEngine(temp_vault, temp_cache, config)
        
        print("인덱스 구축 중...")
        if not engine.build_index():
            print("❌ 인덱스 구축 실패")
            return False
        
        # 의미적 검색 테스트
        print("\n🔍 의미적 검색 테스트: '테스트 방법론'")
        results = engine.semantic_search("테스트 방법론", top_k=3)
        for result in results:
            print(f"  {result.rank}. {result.document.title} (유사도: {result.similarity_score:.4f})")
        
        # 키워드 검색 테스트  
        print("\n🔍 키워드 검색 테스트: 'TDD 리팩토링'")
        results = engine.keyword_search("TDD 리팩토링", top_k=3)
        for result in results:
            print(f"  {result.rank}. {result.document.title} (점수: {result.similarity_score:.2f}) - {result.matched_keywords}")
        
        # 하이브리드 검색 테스트
        print("\n🔍 하이브리드 검색 테스트: '테스트 코드 작성'")
        results = engine.hybrid_search("테스트 코드 작성", top_k=3)
        for result in results:
            print(f"  {result.rank}. {result.document.title} (점수: {result.similarity_score:.4f})")
        
        # 통계 확인
        stats = engine.get_search_statistics()
        print(f"\n📊 통계: {stats['indexed_documents']}개 문서, {stats['embedding_dimension']}차원")
        
        # 정리
        shutil.rmtree(temp_vault)
        shutil.rmtree(temp_cache)
        
        print("✅ 검색 엔진 테스트 완료!")
        return True
        
    except Exception as e:
        print(f"❌ 검색 엔진 테스트 실패: {e}")
        return False


if __name__ == "__main__":
    test_search_engine()