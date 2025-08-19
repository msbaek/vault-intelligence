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
        self.config = config or {}
        
        # 핵심 컴포넌트 초기화
        self.engine = SentenceTransformerEngine(
            model_name=self.config.get('model', {}).get('name', 'paraphrase-multilingual-mpnet-base-v2'),
            cache_dir=self.config.get('model', {}).get('cache_folder', 'models'),
            device=self.config.get('model', {}).get('device')
        )
        
        self.cache = EmbeddingCache(cache_dir)
        
        self.processor = VaultProcessor(
            str(vault_path),
            excluded_dirs=self.config.get('vault', {}).get('excluded_dirs'),
            file_extensions=self.config.get('vault', {}).get('file_extensions')
        )
        
        # 문서 및 임베딩 캐시
        self.documents: List[Document] = []
        self.embeddings: Optional[np.ndarray] = None
        self.indexed = False
        
        logger.info(f"고급 검색 엔진 초기화: {vault_path}")
        
        # 기존 인덱스 자동 로드 시도
        self.load_index()
    
    def build_index(self, force_rebuild: bool = False, progress_callback=None) -> bool:
        """검색 인덱스 구축"""
        try:
            logger.info("검색 인덱스 구축 시작...")
            
            # 문서 처리
            self.documents = self.processor.process_all_files(progress_callback)
            logger.info(f"처리된 문서: {len(self.documents)}개")
            
            if not self.documents:
                logger.warning("처리할 문서가 없습니다.")
                return False
            
            # TF-IDF vectorizer 훈련 (모든 문서 내용)
            all_contents = [doc.content for doc in self.documents]
            all_paths = [doc.path for doc in self.documents]
            self.engine.fit_documents(all_contents, all_paths)
            logger.info("TF-IDF vectorizer 훈련 완료")
            
            # 임베딩 생성/로딩
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
            # TF-IDF 모델 로드
            model_path = os.path.join(self.cache.cache_dir, "tfidf_model.pkl")
            if os.path.exists(model_path):
                self.engine.load_model(model_path)
                logger.info("TF-IDF 모델 로딩 완료")
                
                # 문서 데이터 다시 로드
                logger.info("문서 데이터 로딩 중...")
                self.documents = self.processor.process_all_files()
                logger.info(f"문서 로딩 완료: {len(self.documents)}개")
                
                # TF-IDF 모델이 로드되었지만 새 문서들에 대해 다시 훈련 필요
                # (캐시된 임베딩이 현재 TF-IDF 모델과 호환되지 않을 수 있음)
                logger.info("TF-IDF 모델을 현재 문서들로 재훈련 중...")
                all_contents = [doc.content for doc in self.documents]
                all_paths = [doc.path for doc in self.documents]
                self.engine.fit_documents(all_contents, all_paths)
                logger.info("TF-IDF 재훈련 완료")
                
                # 임베딩 배열 재생성 (TF-IDF 재훈련 후 모든 임베딩 새로 생성)
                embeddings_list = []
                logger.info("모든 임베딩을 새로 생성 중...")
                for i, doc in enumerate(self.documents):
                    # 캐시 무시하고 모든 임베딩 새로 생성 
                    # (TF-IDF 재훈련으로 인해 기존 캐시가 무효화됨)
                    embedding = self.engine.encode_text(doc.content)
                    embeddings_list.append(embedding)
                    doc.embedding = embedding
                    
                    # 새 임베딩을 캐시에 저장
                    self.cache.store_embedding(
                        str(self.vault_path / doc.path),
                        embedding,
                        self.engine.model_name,
                        doc.word_count
                    )
                    
                    # 진행률 표시
                    if (i + 1) % 100 == 0:
                        logger.info(f"임베딩 생성 진행률: {i + 1}/{len(self.documents)}")
                
                logger.info("모든 임베딩 생성 완료")
                
                if embeddings_list:
                    self.embeddings = np.array(embeddings_list)
                    self.indexed = True
                    logger.info(f"인덱스 로딩 완료: {len(self.documents)}개 문서, {self.embeddings.shape}")
                    return True
                else:
                    logger.warning("임베딩 데이터를 로드할 수 없습니다.")
                    return False
            else:
                logger.warning("저장된 모델을 찾을 수 없습니다.")
                return False
        except Exception as e:
            logger.error(f"인덱스 로딩 실패: {e}")
            return False
    
    def save_index(self) -> bool:
        """인덱스 저장"""
        try:
            if not self.indexed:
                logger.warning("저장할 인덱스가 없습니다.")
                return False
            
            # TF-IDF 모델 저장
            model_path = os.path.join(self.cache.cache_dir, "tfidf_model.pkl")
            self.engine.save_model(model_path)
            logger.info("인덱스 저장 완료")
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