#!/usr/bin/env python3
"""
Duplicate Document Detector for Vault Intelligence System V2

Sentence Transformers 임베딩을 활용한 중복 문서 감지 및 분석
"""

import logging
from typing import List, Dict, Optional, Tuple, Set
from pathlib import Path
from dataclasses import dataclass, asdict
from datetime import datetime
import numpy as np
from collections import defaultdict
import json

try:
    from sklearn.cluster import DBSCAN
    from sklearn.metrics.pairwise import cosine_similarity
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

from ..core.sentence_transformer_engine import SentenceTransformerEngine
from ..core.vault_processor import Document

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class DuplicateGroup:
    """중복 문서 그룹"""
    id: str
    documents: List[Document]
    similarity_scores: List[List[float]]  # 그룹 내 문서 간 유사도 매트릭스
    master_document: Optional[Document] = None
    average_similarity: float = 0.0
    created_at: Optional[datetime] = None
    
    def get_document_count(self) -> int:
        return len(self.documents)
    
    def get_total_word_count(self) -> int:
        return sum(doc.word_count for doc in self.documents)
    
    def get_paths(self) -> List[str]:
        return [doc.path for doc in self.documents]


@dataclass
class DuplicateAnalysis:
    """중복 분석 결과"""
    total_documents: int
    duplicate_groups: List[DuplicateGroup]
    duplicate_count: int
    unique_count: int
    similarity_threshold: float
    analysis_date: datetime
    potential_savings_mb: float = 0.0
    
    def get_group_count(self) -> int:
        return len(self.duplicate_groups)
    
    def get_duplicate_ratio(self) -> float:
        if self.total_documents == 0:
            return 0.0
        return self.duplicate_count / self.total_documents


class DuplicateDetector:
    """중복 문서 감지기"""
    
    def __init__(
        self,
        search_engine,
        config: Dict = None
    ):
        """
        Args:
            search_engine: AdvancedSearchEngine 인스턴스
            config: 중복 감지 설정
        """
        self.search_engine = search_engine
        self.config = config or {}
        
        # 기본 설정
        self.similarity_threshold = self.config.get('duplicates', {}).get(
            'similarity_threshold', 0.85
        )
        self.min_word_count = self.config.get('duplicates', {}).get(
            'min_word_count', 50
        )
        self.group_threshold = self.config.get('duplicates', {}).get(
            'group_threshold', 0.9
        )
        
        logger.info(f"중복 감지기 초기화 - 임계값: {self.similarity_threshold}")
    
    def find_duplicates(
        self,
        threshold: Optional[float] = None,
        min_word_count: Optional[int] = None
    ) -> DuplicateAnalysis:
        """중복 문서 감지"""
        try:
            # 설정값 사용
            threshold = threshold or self.similarity_threshold
            min_word_count = min_word_count or self.min_word_count
            
            if not self.search_engine.indexed:
                logger.warning("검색 엔진이 인덱싱되지 않았습니다.")
                return self._create_empty_analysis(threshold)
            
            logger.info(f"중복 감지 시작 - 임계값: {threshold}")
            
            # 필터링된 문서 가져오기
            documents = self._filter_documents(min_word_count)
            logger.info(f"분석 대상 문서: {len(documents)}개")
            
            if len(documents) < 2:
                logger.info("분석할 문서가 충분하지 않습니다.")
                return self._create_empty_analysis(threshold)
            
            # 유사도 매트릭스 계산
            similarity_matrix = self._calculate_similarity_matrix(documents)
            
            # 중복 그룹 찾기
            duplicate_groups = self._find_duplicate_groups(
                documents, similarity_matrix, threshold
            )
            
            logger.info(f"발견된 중복 그룹: {len(duplicate_groups)}개")
            
            # 분석 결과 생성
            analysis = self._create_analysis(
                documents, duplicate_groups, threshold
            )
            
            logger.info(f"중복 분석 완료 - 중복률: {analysis.get_duplicate_ratio():.1%}")
            return analysis
            
        except Exception as e:
            logger.error(f"중복 감지 실패: {e}")
            return self._create_empty_analysis(threshold or self.similarity_threshold)
    
    def _filter_documents(self, min_word_count: int) -> List[Document]:
        """문서 필터링"""
        filtered = []
        
        for doc in self.search_engine.documents:
            # 최소 단어 수 확인
            if doc.word_count < min_word_count:
                continue
            
            # 임베딩 존재 확인
            if doc.embedding is None or np.allclose(doc.embedding, 0):
                continue
            
            filtered.append(doc)
        
        return filtered
    
    def _calculate_similarity_matrix(self, documents: List[Document]) -> np.ndarray:
        """유사도 매트릭스 계산"""
        try:
            embeddings = np.array([doc.embedding for doc in documents])
            
            if SKLEARN_AVAILABLE:
                # sklearn 사용
                similarity_matrix = cosine_similarity(embeddings)
            else:
                # 수동 계산
                n = len(embeddings)
                similarity_matrix = np.zeros((n, n))
                
                for i in range(n):
                    for j in range(i, n):
                        if i == j:
                            similarity_matrix[i, j] = 1.0
                        else:
                            sim = self.search_engine.engine.calculate_similarity(
                                embeddings[i], embeddings[j]
                            )
                            similarity_matrix[i, j] = sim
                            similarity_matrix[j, i] = sim
            
            return similarity_matrix
            
        except Exception as e:
            logger.error(f"유사도 매트릭스 계산 실패: {e}")
            return np.zeros((len(documents), len(documents)))
    
    def _find_duplicate_groups(
        self,
        documents: List[Document],
        similarity_matrix: np.ndarray,
        threshold: float
    ) -> List[DuplicateGroup]:
        """중복 그룹 찾기"""
        try:
            n = len(documents)
            visited = set()
            groups = []
            
            for i in range(n):
                if i in visited:
                    continue
                
                # 현재 문서와 유사한 문서들 찾기
                similar_indices = []
                for j in range(n):
                    if i != j and similarity_matrix[i, j] >= threshold:
                        similar_indices.append(j)
                
                if similar_indices:
                    # 그룹 생성
                    group_indices = [i] + similar_indices
                    group_docs = [documents[idx] for idx in group_indices]
                    
                    # 그룹 내 유사도 매트릭스 추출
                    group_similarity = similarity_matrix[np.ix_(group_indices, group_indices)]
                    
                    # 마스터 문서 선정
                    master_doc = self._select_master_document(group_docs)
                    
                    # 평균 유사도 계산
                    avg_sim = self._calculate_average_similarity(group_similarity)
                    
                    group = DuplicateGroup(
                        id=f"group_{len(groups) + 1}",
                        documents=group_docs,
                        similarity_scores=group_similarity.tolist(),
                        master_document=master_doc,
                        average_similarity=avg_sim,
                        created_at=datetime.now()
                    )
                    
                    groups.append(group)
                    
                    # 방문 표시
                    for idx in group_indices:
                        visited.add(idx)
            
            return groups
            
        except Exception as e:
            logger.error(f"중복 그룹 찾기 실패: {e}")
            return []
    
    def _select_master_document(self, documents: List[Document]) -> Document:
        """마스터 문서 선정 (가장 최신이면서 내용이 많은 문서)"""
        try:
            # 우선순위: 1) 단어 수, 2) 수정 날짜
            return max(documents, key=lambda doc: (doc.word_count, doc.modified_at))
        except Exception as e:
            logger.error(f"마스터 문서 선정 실패: {e}")
            return documents[0] if documents else None
    
    def _calculate_average_similarity(self, similarity_matrix: np.ndarray) -> float:
        """그룹 내 평균 유사도 계산"""
        try:
            # 대각선 제외 (자기 자신과의 유사도 1.0 제외)
            n = similarity_matrix.shape[0]
            if n <= 1:
                return 1.0
            
            total_sum = 0.0
            count = 0
            
            for i in range(n):
                for j in range(i + 1, n):
                    total_sum += similarity_matrix[i, j]
                    count += 1
            
            return total_sum / count if count > 0 else 0.0
            
        except Exception as e:
            logger.error(f"평균 유사도 계산 실패: {e}")
            return 0.0
    
    def _create_analysis(
        self,
        documents: List[Document],
        duplicate_groups: List[DuplicateGroup],
        threshold: float
    ) -> DuplicateAnalysis:
        """분석 결과 생성"""
        try:
            # 중복 문서 수 계산
            duplicate_docs = set()
            for group in duplicate_groups:
                for doc in group.documents:
                    duplicate_docs.add(doc.path)
            
            duplicate_count = len(duplicate_docs)
            unique_count = len(documents) - duplicate_count
            
            # 잠재적 절약 공간 계산 (중복 문서들의 파일 크기 합)
            potential_savings = 0
            for group in duplicate_groups:
                # 마스터 문서 제외하고 나머지 문서들의 크기 합
                if group.master_document:
                    for doc in group.documents:
                        if doc.path != group.master_document.path:
                            potential_savings += doc.file_size
            
            potential_savings_mb = potential_savings / (1024 * 1024)
            
            return DuplicateAnalysis(
                total_documents=len(documents),
                duplicate_groups=duplicate_groups,
                duplicate_count=duplicate_count,
                unique_count=unique_count,
                similarity_threshold=threshold,
                analysis_date=datetime.now(),
                potential_savings_mb=potential_savings_mb
            )
            
        except Exception as e:
            logger.error(f"분석 결과 생성 실패: {e}")
            return self._create_empty_analysis(threshold)
    
    def _create_empty_analysis(self, threshold: float) -> DuplicateAnalysis:
        """빈 분석 결과 생성"""
        return DuplicateAnalysis(
            total_documents=0,
            duplicate_groups=[],
            duplicate_count=0,
            unique_count=0,
            similarity_threshold=threshold,
            analysis_date=datetime.now()
        )
    
    def find_near_duplicates(
        self,
        document_path: str,
        threshold: float = 0.8,
        top_k: int = 5
    ) -> List[Tuple[Document, float]]:
        """특정 문서의 유사 문서 찾기"""
        try:
            if not self.search_engine.indexed:
                logger.warning("검색 엔진이 인덱싱되지 않았습니다.")
                return []
            
            # 대상 문서 찾기
            target_doc = None
            target_idx = None
            
            for i, doc in enumerate(self.search_engine.documents):
                if doc.path == document_path:
                    target_doc = doc
                    target_idx = i
                    break
            
            if target_doc is None:
                logger.warning(f"문서를 찾을 수 없습니다: {document_path}")
                return []
            
            # 유사 문서 검색
            query_embedding = target_doc.embedding
            if query_embedding is None:
                logger.warning(f"임베딩이 없습니다: {document_path}")
                return []
            
            results = self.search_engine.engine.find_most_similar(
                query_embedding,
                self.search_engine.embeddings,
                top_k=top_k + 1  # 자기 자신 제외
            )
            
            # 자기 자신 제외하고 임계값 이상만 반환
            similar_docs = []
            for idx, similarity in results:
                if idx != target_idx and similarity >= threshold:
                    similar_docs.append((self.search_engine.documents[idx], similarity))
            
            return similar_docs[:top_k]
            
        except Exception as e:
            logger.error(f"유사 문서 찾기 실패: {e}")
            return []
    
    def generate_merge_suggestions(
        self, 
        duplicate_group: DuplicateGroup
    ) -> Dict:
        """중복 그룹에 대한 병합 제안"""
        try:
            if not duplicate_group.master_document:
                return {"error": "마스터 문서가 없습니다"}
            
            master = duplicate_group.master_document
            duplicates = [doc for doc in duplicate_group.documents if doc.path != master.path]
            
            suggestions = {
                "master_document": {
                    "path": master.path,
                    "title": master.title,
                    "word_count": master.word_count,
                    "modified_at": master.modified_at.isoformat(),
                    "reason": "가장 많은 내용과 최신 수정 날짜"
                },
                "duplicates": [],
                "merge_strategy": "content_comparison",
                "potential_savings_mb": 0.0
            }
            
            total_size = 0
            for doc in duplicates:
                suggestions["duplicates"].append({
                    "path": doc.path,
                    "title": doc.title,
                    "word_count": doc.word_count,
                    "file_size_mb": doc.file_size / (1024 * 1024),
                    "similarity_to_master": self._get_similarity_to_master(
                        duplicate_group, doc, master
                    )
                })
                total_size += doc.file_size
            
            suggestions["potential_savings_mb"] = total_size / (1024 * 1024)
            
            # 병합 전략 제안
            if len(duplicates) == 1:
                suggestions["merge_strategy"] = "simple_replacement"
            else:
                suggestions["merge_strategy"] = "content_consolidation"
            
            return suggestions
            
        except Exception as e:
            logger.error(f"병합 제안 생성 실패: {e}")
            return {"error": str(e)}
    
    def _get_similarity_to_master(
        self,
        group: DuplicateGroup,
        doc: Document,
        master: Document
    ) -> float:
        """마스터 문서와의 유사도 조회"""
        try:
            doc_idx = group.documents.index(doc)
            master_idx = group.documents.index(master)
            return group.similarity_scores[doc_idx][master_idx]
        except (ValueError, IndexError):
            return 0.0
    
    def export_analysis(self, analysis: DuplicateAnalysis, output_file: str) -> bool:
        """분석 결과를 파일로 내보내기"""
        try:
            export_data = {
                "analysis_info": {
                    "total_documents": analysis.total_documents,
                    "duplicate_count": analysis.duplicate_count,
                    "unique_count": analysis.unique_count,
                    "duplicate_ratio": analysis.get_duplicate_ratio(),
                    "similarity_threshold": analysis.similarity_threshold,
                    "analysis_date": analysis.analysis_date.isoformat(),
                    "potential_savings_mb": analysis.potential_savings_mb
                },
                "duplicate_groups": []
            }
            
            for group in analysis.duplicate_groups:
                group_data = {
                    "id": group.id,
                    "document_count": group.get_document_count(),
                    "average_similarity": group.average_similarity,
                    "total_word_count": group.get_total_word_count(),
                    "master_document": group.master_document.path if group.master_document else None,
                    "documents": [
                        {
                            "path": doc.path,
                            "title": doc.title,
                            "word_count": doc.word_count,
                            "file_size_bytes": doc.file_size,
                            "modified_at": doc.modified_at.isoformat()
                        }
                        for doc in group.documents
                    ],
                    "merge_suggestions": self.generate_merge_suggestions(group)
                }
                export_data["duplicate_groups"].append(group_data)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"분석 결과 내보내기 완료: {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"분석 결과 내보내기 실패: {e}")
            return False


def test_duplicate_detector():
    """중복 감지기 테스트"""
    import tempfile
    import shutil
    from ..features.advanced_search import AdvancedSearchEngine
    
    try:
        # 임시 vault 및 캐시 생성
        temp_vault = tempfile.mkdtemp()
        temp_cache = tempfile.mkdtemp()
        
        # 유사한 테스트 문서들 생성
        test_docs = [
            ("tdd1.md", "# TDD 기본 개념\n\nTDD는 테스트 주도 개발 방법론입니다.\nRed-Green-Refactor 사이클을 따릅니다."),
            ("tdd2.md", "# TDD 개념\n\nTDD는 테스트 주도 개발입니다.\nRed-Green-Refactor 과정을 반복합니다."),  # 유사
            ("refactoring.md", "# 리팩토링\n\n코드의 구조를 개선하는 과정입니다.\n테스트가 있어야 안전합니다."),
            ("clean_code.md", "# Clean Code\n\n깨끗한 코드 작성 방법론입니다.\n읽기 쉬운 코드를 만드는 것이 목표입니다."),
            ("duplicate_clean.md", "# 깨끗한 코드\n\nClean Code는 읽기 쉬운 코드를 작성하는 방법입니다.\n이해하기 쉬운 코드가 목표입니다.")  # 유사
        ]
        
        for filename, content in test_docs:
            with open(Path(temp_vault) / filename, 'w', encoding='utf-8') as f:
                f.write(content)
        
        # 검색 엔진 초기화 및 인덱싱
        config = {
            "model": {"name": "paraphrase-multilingual-mpnet-base-v2"},
            "vault": {"excluded_dirs": [], "file_extensions": [".md"]},
            "duplicates": {"similarity_threshold": 0.7, "min_word_count": 10}
        }
        
        search_engine = AdvancedSearchEngine(temp_vault, temp_cache, config)
        print("검색 엔진 인덱싱 중...")
        if not search_engine.build_index():
            print("❌ 인덱싱 실패")
            return False
        
        # 중복 감지기 초기화
        detector = DuplicateDetector(search_engine, config)
        
        # 중복 감지 실행
        print("\n🔍 중복 문서 감지 중...")
        analysis = detector.find_duplicates(threshold=0.7)
        
        print(f"\n📊 중복 분석 결과:")
        print(f"- 총 문서: {analysis.total_documents}개")
        print(f"- 중복 그룹: {analysis.get_group_count()}개")
        print(f"- 중복 문서: {analysis.duplicate_count}개")
        print(f"- 중복률: {analysis.get_duplicate_ratio():.1%}")
        print(f"- 잠재적 절약: {analysis.potential_savings_mb:.2f}MB")
        
        # 중복 그룹 세부 정보
        for i, group in enumerate(analysis.duplicate_groups):
            print(f"\n🔗 중복 그룹 {i+1} (평균 유사도: {group.average_similarity:.3f}):")
            print(f"  마스터: {group.master_document.path if group.master_document else 'None'}")
            for doc in group.documents:
                print(f"  - {doc.path} ({doc.word_count} 단어)")
        
        # 특정 문서의 유사 문서 찾기 테스트
        print(f"\n🔍 'tdd1.md'와 유사한 문서:")
        similar_docs = detector.find_near_duplicates("tdd1.md", threshold=0.5, top_k=3)
        for doc, similarity in similar_docs:
            print(f"  - {doc.path} (유사도: {similarity:.3f})")
        
        # 결과 내보내기 테스트
        output_file = Path(temp_cache) / "duplicate_analysis.json"
        if detector.export_analysis(analysis, str(output_file)):
            print(f"\n💾 분석 결과 저장: {output_file}")
        
        # 정리
        shutil.rmtree(temp_vault)
        shutil.rmtree(temp_cache)
        
        print("✅ 중복 감지기 테스트 완료!")
        return True
        
    except Exception as e:
        print(f"❌ 중복 감지기 테스트 실패: {e}")
        return False


if __name__ == "__main__":
    test_duplicate_detector()