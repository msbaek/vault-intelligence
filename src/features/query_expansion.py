#!/usr/bin/env python3
"""
Query Expansion Engine for Vault Intelligence System V2

쿼리 확장 기능:
- 동의어 확장 (Synonym Expansion)
- HyDE (Hypothetical Document Embeddings)
- 관련어 추천 (Related Terms)
"""

import os
import logging
from typing import List, Dict, Optional, Tuple, Union, Set
from dataclasses import dataclass
import json
import re

# BGE-M3 모델
try:
    from FlagEmbedding import BGEM3FlagModel
    BGE_AVAILABLE = True
except ImportError:
    BGE_AVAILABLE = False
    logging.warning("FlagEmbedding not available. Query expansion will be limited.")

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ExpandedQuery:
    """확장된 쿼리"""
    original_query: str
    expanded_terms: List[str]
    synonyms: List[str]
    related_terms: List[str]
    hypothetical_doc: Optional[str] = None
    expansion_method: str = "basic"


class KoreanSynonymExpander:
    """한국어 동의어 확장기"""
    
    def __init__(self):
        """한국어 동의어 사전 초기화"""
        self.synonym_dict = {
            # 소프트웨어 개발 관련
            "TDD": ["테스트 주도 개발", "테스트 드리븐 개발", "Test Driven Development", "test driven development"],
            "테스트 주도 개발": ["TDD", "테스트 드리븐 개발", "Test Driven Development"],
            "테스트 드리븐 개발": ["TDD", "테스트 주도 개발", "Test Driven Development"],
            
            "리팩토링": ["refactoring", "코드 개선", "구조 개선", "코드 정리"],
            "refactoring": ["리팩토링", "코드 개선", "구조 개선"],
            
            "클린코드": ["clean code", "깨끗한 코드", "좋은 코드", "가독성"],
            "clean code": ["클린코드", "깨끗한 코드", "좋은 코드"],
            
            "디자인패턴": ["design pattern", "설계 패턴", "패턴"],
            "design pattern": ["디자인패턴", "설계 패턴", "패턴"],
            
            "아키텍처": ["architecture", "구조", "설계", "아키텍쳐"],
            "architecture": ["아키텍처", "구조", "설계"],
            
            "마이크로서비스": ["microservice", "MSA", "마이크로 서비스"],
            "microservice": ["마이크로서비스", "MSA", "마이크로 서비스"],
            
            # 프로그래밍 언어
            "자바": ["java", "Java"],
            "java": ["자바", "Java"],
            "파이썬": ["python", "Python"],
            "python": ["파이썬", "Python"],
            "자바스크립트": ["javascript", "JS", "js"],
            "javascript": ["자바스크립트", "JS", "js"],
            
            # 프레임워크
            "스프링": ["spring", "Spring", "스프링부트", "spring boot"],
            "spring": ["스프링", "Spring", "스프링부트"],
            "리액트": ["react", "React"],
            "react": ["리액트", "React"],
            
            # 개발 방법론
            "애자일": ["agile", "Agile", "스크럼", "scrum"],
            "agile": ["애자일", "Agile", "스크럼"],
            "스크럼": ["scrum", "Scrum", "애자일"],
            "scrum": ["스크럼", "Scrum", "애자일"],
            
            # 일반적인 용어
            "구현": ["implementation", "개발", "코딩", "작성"],
            "implementation": ["구현", "개발", "코딩"],
            "개발": ["development", "구현", "제작"],
            "development": ["개발", "구현", "제작"],
            
            "학습": ["learning", "공부", "스터디", "연구"],
            "learning": ["학습", "공부", "스터디"],
            "공부": ["study", "학습", "연구"],
            "study": ["공부", "학습", "연구"],
        }
        
        logger.info(f"한국어 동의어 사전 로딩 완료: {len(self.synonym_dict)}개 엔트리")
    
    def expand_synonyms(self, query: str) -> List[str]:
        """동의어 확장"""
        synonyms = set()
        
        # 쿼리를 단어로 분할
        words = self._tokenize_query(query)
        
        for word in words:
            # 대소문자 구분 없이 검색
            word_lower = word.lower()
            word_original = word
            
            # 직접 매칭
            if word_lower in self.synonym_dict:
                synonyms.update(self.synonym_dict[word_lower])
            elif word_original in self.synonym_dict:
                synonyms.update(self.synonym_dict[word_original])
            
            # 부분 매칭 (포함 관계)
            for key, values in self.synonym_dict.items():
                if word_lower in key.lower() or key.lower() in word_lower:
                    synonyms.update(values)
        
        # 원본 쿼리의 단어들 제외
        synonyms.discard(query)
        synonyms.discard(query.lower())
        for word in words:
            synonyms.discard(word)
            synonyms.discard(word.lower())
        
        return list(synonyms)
    
    def _tokenize_query(self, query: str) -> List[str]:
        """쿼리를 토큰으로 분할"""
        # 한글, 영문, 숫자를 포함한 단어 추출
        tokens = re.findall(r'[가-힣a-zA-Z0-9]+', query)
        return tokens


class HyDEGenerator:
    """Hypothetical Document Embeddings (HyDE) 생성기"""
    
    def __init__(
        self,
        model_name: str = "BAAI/bge-m3",
        device: Optional[str] = None,
        use_fp16: bool = True
    ):
        """
        Args:
            model_name: BGE 모델명
            device: 사용할 디바이스
            use_fp16: FP16 사용 여부
        """
        self.model_name = model_name
        self.device = device
        self.use_fp16 = use_fp16
        self.model = None
        self.is_initialized = False
        
        if BGE_AVAILABLE:
            self._initialize_model()
    
    def _initialize_model(self):
        """BGE-M3 모델 초기화"""
        try:
            # 디바이스 자동 감지
            if self.device is None:
                import torch
                if torch.cuda.is_available():
                    self.device = "cuda"
                elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                    self.device = "mps"
                else:
                    self.device = "cpu"
            
            self.model = BGEM3FlagModel(
                self.model_name,
                use_fp16=self.use_fp16,
                device=self.device
            )
            
            self.is_initialized = True
            logger.info(f"HyDE 생성기 초기화 완료: {self.model_name}")
            
        except Exception as e:
            logger.error(f"HyDE 생성기 초기화 실패: {e}")
            self.is_initialized = False
    
    def generate_hypothetical_document(self, query: str) -> str:
        """
        쿼리를 기반으로 가상의 문서 생성
        (실제로는 쿼리를 확장하여 더 자세한 문서 형태로 변환)
        """
        if not self.is_initialized:
            # 폴백: 규칙 기반 확장
            return self._rule_based_expansion(query)
        
        # 현재는 규칙 기반 구현 (향후 LLM 통합 가능)
        return self._rule_based_expansion(query)
    
    def _rule_based_expansion(self, query: str) -> str:
        """규칙 기반 문서 확장"""
        # 쿼리 분석
        words = re.findall(r'[가-힣a-zA-Z0-9]+', query.lower())
        
        # 도메인별 확장 템플릿
        templates = {
            # 소프트웨어 개발
            "tdd": "테스트 주도 개발(TDD)은 소프트웨어 개발 방법론 중 하나입니다. Red-Green-Refactor 사이클을 통해 먼저 실패하는 테스트를 작성하고, 테스트를 통과하는 최소한의 코드를 구현한 후, 코드를 개선하는 과정을 반복합니다. 이를 통해 코드 품질을 높이고 버그를 줄일 수 있습니다.",
            
            "리팩토링": "리팩토링은 기능은 변경하지 않으면서 코드의 구조와 가독성을 개선하는 과정입니다. 코드 스멜을 제거하고, 중복을 줄이며, 더 나은 설계 패턴을 적용하여 유지보수성을 향상시킵니다. 안전한 리팩토링을 위해서는 충분한 테스트 코드가 필요합니다.",
            
            "클린코드": "클린 코드는 읽기 쉽고, 이해하기 쉬우며, 변경하기 쉬운 코드를 의미합니다. 의미 있는 변수명, 작고 집중된 함수, 명확한 주석, 일관된 코딩 스타일을 통해 달성할 수 있습니다. 좋은 코드는 다른 개발자가 쉽게 이해하고 유지보수할 수 있습니다.",
            
            "아키텍처": "소프트웨어 아키텍처는 시스템의 구조와 설계를 다룹니다. 컴포넌트 간의 관계, 데이터 흐름, 인터페이스 설계 등을 포함하며, 확장성, 유지보수성, 성능을 고려하여 설계됩니다. 좋은 아키텍처는 비즈니스 요구사항을 효과적으로 지원합니다.",
            
            "마이크로서비스": "마이크로서비스 아키텍처는 애플리케이션을 작고 독립적인 서비스들로 분해하는 설계 방식입니다. 각 서비스는 특정 비즈니스 기능을 담당하며, 독립적으로 배포하고 확장할 수 있습니다. API를 통해 통신하며, 장애 격리와 기술 다양성을 제공합니다.",
            
            # 학습 관련
            "학습": "효과적인 학습을 위해서는 체계적인 접근이 필요합니다. 이론과 실습을 병행하고, 정기적인 복습과 실전 프로젝트를 통해 지식을 내재화해야 합니다. 동료들과의 토론과 지식 공유도 학습 효과를 높이는 중요한 방법입니다.",
            
            "연구": "기술 연구는 문제 정의, 현황 분석, 해결 방안 모색, 실험 및 검증의 단계를 거칩니다. 최신 기술 동향을 파악하고, 기존 솔루션의 한계를 분석하여 개선된 접근 방법을 찾는 것이 핵심입니다.",
        }
        
        # 쿼리에 맞는 템플릿 찾기
        for keyword, template in templates.items():
            if any(keyword in word for word in words) or keyword in query.lower():
                return template
        
        # 기본 확장
        expanded = f"'{query}'에 대한 상세한 내용입니다. "
        
        # 개발 관련 키워드가 있으면 개발 컨텍스트 추가
        dev_keywords = ["코드", "개발", "프로그래밍", "소프트웨어", "시스템", "기술"]
        if any(keyword in query for keyword in dev_keywords):
            expanded += "소프트웨어 개발에서 중요한 개념으로, 코드 품질과 개발 효율성에 영향을 미칩니다. "
        
        # 학습 관련 키워드가 있으면 학습 컨텍스트 추가
        learning_keywords = ["배우", "학습", "공부", "익히", "연습"]
        if any(keyword in query for keyword in learning_keywords):
            expanded += "지속적인 학습과 실습을 통해 숙련도를 향상시킬 수 있습니다. "
        
        expanded += f"관련 자료와 예제, 실습 내용을 포함하여 {query}에 대해 자세히 설명합니다."
        
        return expanded


class QueryExpansionEngine:
    """통합 쿼리 확장 엔진"""
    
    def __init__(
        self,
        model_name: str = "BAAI/bge-m3",
        device: Optional[str] = None,
        use_fp16: bool = True,
        enable_hyde: bool = True
    ):
        """
        Args:
            model_name: BGE 모델명
            device: 사용할 디바이스
            use_fp16: FP16 사용 여부
            enable_hyde: HyDE 기능 활성화 여부
        """
        self.model_name = model_name
        self.device = device
        self.use_fp16 = use_fp16
        self.enable_hyde = enable_hyde
        
        # 서브 컴포넌트 초기화
        self.synonym_expander = KoreanSynonymExpander()
        
        if self.enable_hyde and BGE_AVAILABLE:
            self.hyde_generator = HyDEGenerator(model_name, device, use_fp16)
        else:
            self.hyde_generator = None
            if self.enable_hyde:
                logger.warning("HyDE 기능이 요청되었지만 BGE가 사용 불가능합니다.")
        
        logger.info("쿼리 확장 엔진 초기화 완료")
    
    def expand_query(
        self,
        query: str,
        include_synonyms: bool = True,
        include_hyde: bool = True,
        max_synonyms: int = 5
    ) -> ExpandedQuery:
        """
        쿼리 확장 실행
        
        Args:
            query: 원본 쿼리
            include_synonyms: 동의어 포함 여부
            include_hyde: HyDE 포함 여부
            max_synonyms: 최대 동의어 수
            
        Returns:
            확장된 쿼리 정보
        """
        logger.info(f"쿼리 확장 시작: '{query}'")
        
        # 동의어 확장
        synonyms = []
        if include_synonyms:
            synonyms = self.synonym_expander.expand_synonyms(query)
            synonyms = synonyms[:max_synonyms]  # 최대 수 제한
            logger.info(f"동의어 발견: {len(synonyms)}개")
        
        # 관련어 (현재는 동의어와 동일, 향후 의미적 유사어로 확장 가능)
        related_terms = synonyms.copy()
        
        # 확장된 용어 목록
        expanded_terms = [query] + synonyms + related_terms
        expanded_terms = list(dict.fromkeys(expanded_terms))  # 중복 제거
        
        # HyDE 생성
        hypothetical_doc = None
        if include_hyde and self.hyde_generator:
            hypothetical_doc = self.hyde_generator.generate_hypothetical_document(query)
            logger.info(f"HyDE 문서 생성 완료: {len(hypothetical_doc)}자")
        
        # 확장 방법 결정
        expansion_method = []
        if synonyms:
            expansion_method.append("synonyms")
        if hypothetical_doc:
            expansion_method.append("hyde")
        
        expanded_query = ExpandedQuery(
            original_query=query,
            expanded_terms=expanded_terms,
            synonyms=synonyms,
            related_terms=related_terms,
            hypothetical_doc=hypothetical_doc,
            expansion_method="+".join(expansion_method) if expansion_method else "none"
        )
        
        logger.info(f"쿼리 확장 완료: {len(expanded_terms)}개 용어, 방법: {expanded_query.expansion_method}")
        
        return expanded_query
    
    def create_expanded_search_queries(self, expanded_query: ExpandedQuery) -> List[str]:
        """확장된 쿼리로부터 여러 검색 쿼리 생성"""
        search_queries = []
        
        # 1. 원본 쿼리
        search_queries.append(expanded_query.original_query)
        
        # 2. 동의어가 포함된 쿼리들
        for synonym in expanded_query.synonyms[:3]:  # 상위 3개만
            search_queries.append(f"{expanded_query.original_query} {synonym}")
        
        # 3. HyDE 문서 (있는 경우)
        if expanded_query.hypothetical_doc:
            search_queries.append(expanded_query.hypothetical_doc)
        
        # 4. 확장된 용어들의 조합
        if len(expanded_query.expanded_terms) > 1:
            # 상위 용어들의 조합
            top_terms = expanded_query.expanded_terms[:4]
            combined_query = " ".join(top_terms)
            search_queries.append(combined_query)
        
        # 중복 제거
        search_queries = list(dict.fromkeys(search_queries))
        
        return search_queries


def test_query_expansion():
    """쿼리 확장 엔진 테스트"""
    print("🧪 쿼리 확장 엔진 테스트")
    
    try:
        # 쿼리 확장 엔진 초기화
        expansion_engine = QueryExpansionEngine(enable_hyde=True)
        
        # 테스트 쿼리들
        test_queries = [
            "TDD",
            "리팩토링 방법",
            "클린코드 작성법",
            "스프링 부트 학습",
            "자바 개발"
        ]
        
        for query in test_queries:
            print(f"\n🔍 테스트 쿼리: '{query}'")
            
            # 쿼리 확장
            expanded = expansion_engine.expand_query(query)
            
            print(f"   동의어: {expanded.synonyms}")
            print(f"   확장 용어: {expanded.expanded_terms}")
            print(f"   확장 방법: {expanded.expansion_method}")
            
            if expanded.hypothetical_doc:
                print(f"   HyDE 문서: {expanded.hypothetical_doc[:100]}...")
            
            # 검색 쿼리 생성
            search_queries = expansion_engine.create_expanded_search_queries(expanded)
            print(f"   검색 쿼리 수: {len(search_queries)}")
        
        print("\n✅ 쿼리 확장 엔진 테스트 완료!")
        return True
        
    except Exception as e:
        print(f"❌ 테스트 실패: {e}")
        return False


if __name__ == "__main__":
    test_query_expansion()