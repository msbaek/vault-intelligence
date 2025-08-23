#!/usr/bin/env python3
"""
MOC(Map of Content) Generator for Vault Intelligence System V2

주제별 자동 목차 문서 생성 시스템
"""

import os
import re
import logging
from typing import List, Dict, Optional, Tuple, Set
from pathlib import Path
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import numpy as np

from ..core.vault_processor import Document
from ..features.advanced_search import SearchResult
from .topic_collector import TopicCollector, DocumentCollection

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class DocumentCategory:
    """문서 카테고리"""
    name: str
    description: str
    keywords: List[str]
    documents: List[Document]
    priority: int = 0


@dataclass
class LearningPathStep:
    """학습 경로 단계"""
    step: int
    title: str
    documents: List[Document]
    description: str
    difficulty_level: str  # "입문", "기초", "중급", "고급"


@dataclass
class DocumentRelationship:
    """문서 간 관계"""
    source_doc: Document
    target_doc: Document
    relationship_type: str  # "references", "similar", "prerequisite"
    strength: float  # 관계 강도 (0-1)


@dataclass
class MOCData:
    """MOC 데이터 구조"""
    topic: str
    overview: str
    total_documents: int
    core_documents: List[Document]
    categories: List[DocumentCategory]
    learning_path: List[LearningPathStep]
    related_topics: List[Tuple[str, int]]
    recent_updates: List[Document]
    relationships: List[DocumentRelationship]
    generation_date: datetime
    statistics: Dict


class MOCGenerator:
    """MOC(Map of Content) 생성기"""
    
    # 카테고리별 키워드 정의
    CATEGORY_KEYWORDS = {
        "입문/기초": {
            "keywords": ["입문", "시작", "기초", "기본", "소개", "개요", "introduction", "basic", "fundamental", "getting started", "overview", "primer"],
            "description": "주제에 대한 첫 걸음과 기본 개념",
            "priority": 1
        },
        "개념/이론": {
            "keywords": ["개념", "이론", "원리", "정의", "concept", "theory", "principle", "definition", "model", "framework"],
            "description": "핵심 개념과 이론적 배경",
            "priority": 2
        },
        "실습/예제": {
            "keywords": ["실습", "예제", "연습", "실전", "구현", "practice", "example", "exercise", "implementation", "hands-on", "tutorial", "workshop"],
            "description": "실제 적용 사례와 연습 문제",
            "priority": 3
        },
        "심화/고급": {
            "keywords": ["심화", "고급", "전문", "상세", "advanced", "deep", "expert", "in-depth", "professional", "detailed"],
            "description": "전문적이고 깊이 있는 내용",
            "priority": 4
        },
        "도구/기술": {
            "keywords": ["도구", "툴", "기술", "방법", "tool", "technique", "method", "approach", "framework", "library"],
            "description": "관련 도구와 기술 스택",
            "priority": 3
        },
        "참고자료": {
            "keywords": ["참고", "자료", "리소스", "문서", "reference", "resource", "documentation", "guide", "manual", "cheat sheet"],
            "description": "추가 학습을 위한 참고 자료",
            "priority": 5
        }
    }
    
    def __init__(
        self,
        search_engine,
        config: Dict = None
    ):
        """
        Args:
            search_engine: AdvancedSearchEngine 인스턴스
            config: MOC 생성 설정
        """
        self.search_engine = search_engine
        self.config = config or {}
        
        # TopicCollector 인스턴스 생성
        self.topic_collector = TopicCollector(search_engine, config)
        
        # MOC 생성 설정
        self.max_core_documents = self.config.get('moc', {}).get('max_core_documents', 5)
        self.max_category_documents = self.config.get('moc', {}).get('max_category_documents', 10)
        self.recent_days = self.config.get('moc', {}).get('recent_days', 30)
        self.min_similarity_threshold = self.config.get('moc', {}).get('min_similarity_threshold', 0.3)
        self.relationship_threshold = self.config.get('moc', {}).get('relationship_threshold', 0.6)
        
        logger.info("MOC 생성기 초기화 완료")
    
    def generate_moc(
        self,
        topic: str,
        top_k: int = 100,
        threshold: float = 0.3,
        include_orphans: bool = False,
        use_expansion: bool = True,
        output_file: Optional[str] = None
    ) -> MOCData:
        """주제별 MOC 생성"""
        try:
            logger.info(f"MOC 생성 시작: '{topic}'")
            
            # 1. 관련 문서 수집
            logger.info("1️⃣ 관련 문서 수집 중...")
            collection = self.topic_collector.collect_topic(
                topic=topic,
                top_k=top_k,
                threshold=threshold,
                use_expansion=use_expansion,
                include_synonyms=True,
                include_hyde=True
            )
            
            if not collection.documents:
                logger.warning(f"주제 '{topic}'에 대한 문서를 찾을 수 없습니다.")
                return self._create_empty_moc(topic)
            
            logger.info(f"수집된 문서: {len(collection.documents)}개")
            
            # 2. 개요 생성
            logger.info("2️⃣ 주제 개요 생성 중...")
            overview = self._create_overview(topic, collection)
            
            # 3. 핵심 문서 선정
            logger.info("3️⃣ 핵심 문서 선정 중...")
            core_documents = self._select_core_documents(collection.documents)
            
            # 4. 문서 카테고리별 분류
            logger.info("4️⃣ 문서 카테고리별 분류 중...")
            categories = self._classify_documents(collection.documents)
            
            # 5. 학습 경로 생성
            logger.info("5️⃣ 학습 경로 생성 중...")
            learning_path = self._create_learning_path(collection.documents, categories)
            
            # 6. 관련 주제 추출
            logger.info("6️⃣ 관련 주제 추출 중...")
            related_topics = self._extract_related_topics(collection)
            
            # 7. 최근 업데이트 문서
            logger.info("7️⃣ 최근 업데이트 문서 분석 중...")
            recent_updates = self._get_recent_updates(collection.documents)
            
            # 8. 문서 간 관계 분석
            logger.info("8️⃣ 문서 간 관계 분석 중...")
            relationships = self._analyze_document_relationships(collection.documents)
            
            # 9. 통계 정보 생성
            statistics = self._generate_moc_statistics(collection.documents, categories, relationships)
            
            # MOC 데이터 생성
            moc_data = MOCData(
                topic=topic,
                overview=overview,
                total_documents=len(collection.documents),
                core_documents=core_documents,
                categories=categories,
                learning_path=learning_path,
                related_topics=related_topics,
                recent_updates=recent_updates,
                relationships=relationships,
                generation_date=datetime.now(),
                statistics=statistics
            )
            
            # 출력 파일 생성
            if output_file:
                self._export_moc(moc_data, output_file)
                logger.info(f"MOC 파일 저장: {output_file}")
            
            logger.info(f"MOC 생성 완료: {len(collection.documents)}개 문서, {len(categories)}개 카테고리")
            return moc_data
            
        except Exception as e:
            logger.error(f"MOC 생성 실패: {e}")
            return self._create_empty_moc(topic)
    
    def _create_overview(self, topic: str, collection: DocumentCollection) -> str:
        """주제 개요 생성"""
        try:
            # 기본 통계
            total_docs = len(collection.documents)
            total_words = sum(doc.word_count for doc in collection.documents)
            avg_words = total_words // total_docs if total_docs > 0 else 0
            
            # 주요 태그 추출
            top_tags = list(collection.metadata.tag_distribution.items())[:5]
            tags_str = ", ".join([f"#{tag}" for tag, _ in top_tags])
            
            # 기간 분석
            if collection.documents:
                dates = [doc.modified_at for doc in collection.documents]
                oldest = min(dates)
                newest = max(dates)
                span_days = (newest - oldest).days
            else:
                span_days = 0
            
            overview = f"""이 Map of Content는 '{topic}' 주제에 대한 종합적인 탐색 가이드입니다.

**📊 컬렉션 통계:**
- 총 문서 수: {total_docs}개
- 총 단어 수: {total_words:,}개
- 평균 문서 길이: {avg_words:,}개 단어
- 업데이트 기간: {span_days}일간"""

            if tags_str:
                overview += f"\n- 주요 태그: {tags_str}"
            
            overview += f"""

이 MOC를 통해 {topic} 관련 지식을 체계적으로 탐색하고 학습할 수 있습니다."""
            
            return overview
            
        except Exception as e:
            logger.error(f"개요 생성 실패: {e}")
            return f"'{topic}' 주제에 대한 종합적인 지식 모음입니다."
    
    def _select_core_documents(self, documents: List[Document]) -> List[Document]:
        """핵심 문서 선정"""
        try:
            # 점수 기반 핵심 문서 선정
            scored_docs = []
            
            for doc in documents:
                score = 0.0
                
                # 단어 수 점수 (적당한 길이 선호)
                word_score = min(doc.word_count / 1000, 1.0) if doc.word_count else 0
                score += word_score * 0.3
                
                # 태그 수 점수 (태그가 많을수록 체계적)
                tag_score = min(len(doc.tags) / 5, 1.0) if doc.tags else 0
                score += tag_score * 0.2
                
                # 최근성 점수 (최근 수정된 문서 선호)
                if doc.modified_at:
                    days_ago = (datetime.now() - doc.modified_at).days
                    recency_score = max(0, 1 - days_ago / 365)  # 1년 기준
                    score += recency_score * 0.2
                
                # 제목 품질 점수 (구체적이고 명확한 제목)
                title_score = min(len(doc.title.split()) / 10, 1.0)
                score += title_score * 0.3
                
                scored_docs.append((doc, score))
            
            # 점수 순으로 정렬하여 상위 문서 선택
            scored_docs.sort(key=lambda x: x[1], reverse=True)
            core_docs = [doc for doc, score in scored_docs[:self.max_core_documents]]
            
            logger.info(f"핵심 문서 {len(core_docs)}개 선정")
            return core_docs
            
        except Exception as e:
            logger.error(f"핵심 문서 선정 실패: {e}")
            return documents[:self.max_core_documents]
    
    def _classify_documents(self, documents: List[Document]) -> List[DocumentCategory]:
        """문서를 카테고리별로 분류"""
        try:
            categories = []
            
            for category_name, config in self.CATEGORY_KEYWORDS.items():
                category_docs = []
                keywords = config["keywords"]
                
                for doc in documents:
                    # 제목과 내용에서 키워드 매칭
                    text_to_check = f"{doc.title} {doc.content[:500]}".lower()
                    
                    # 키워드 매칭 점수 계산
                    matches = sum(1 for keyword in keywords if keyword.lower() in text_to_check)
                    
                    # 매칭 점수가 있으면 해당 카테고리에 추가
                    if matches > 0:
                        category_docs.append((doc, matches))
                
                # 매칭 점수 순으로 정렬하고 상위 문서들 선택
                category_docs.sort(key=lambda x: x[1], reverse=True)
                selected_docs = [doc for doc, _ in category_docs[:self.max_category_documents]]
                
                if selected_docs:
                    category = DocumentCategory(
                        name=category_name,
                        description=config["description"],
                        keywords=keywords,
                        documents=selected_docs,
                        priority=config["priority"]
                    )
                    categories.append(category)
            
            # 분류되지 않은 문서들을 "기타" 카테고리로 처리
            all_categorized = set()
            for category in categories:
                all_categorized.update(doc.path for doc in category.documents)
            
            uncategorized = [doc for doc in documents if doc.path not in all_categorized]
            if uncategorized:
                other_category = DocumentCategory(
                    name="기타",
                    description="기타 관련 문서들",
                    keywords=[],
                    documents=uncategorized[:self.max_category_documents],
                    priority=6
                )
                categories.append(other_category)
            
            # 우선순위와 문서 수로 정렬
            categories.sort(key=lambda c: (c.priority, -len(c.documents)))
            
            logger.info(f"문서 분류 완료: {len(categories)}개 카테고리")
            return categories
            
        except Exception as e:
            logger.error(f"문서 분류 실패: {e}")
            return []
    
    def _create_learning_path(self, documents: List[Document], categories: List[DocumentCategory]) -> List[LearningPathStep]:
        """학습 경로 생성"""
        try:
            learning_path = []
            step_counter = 1
            
            # 카테고리 우선순위 순으로 학습 단계 생성
            for category in categories:
                if not category.documents:
                    continue
                
                # 난이도 레벨 매핑
                difficulty_map = {
                    "입문/기초": "입문",
                    "개념/이론": "기초",
                    "실습/예제": "중급",
                    "도구/기술": "중급",
                    "심화/고급": "고급",
                    "참고자료": "참고"
                }
                
                difficulty = difficulty_map.get(category.name, "중급")
                
                # 학습 단계 설명 생성
                if category.name == "입문/기초":
                    description = "주제에 대한 기본적인 이해와 개념 학습"
                elif category.name == "개념/이론":
                    description = "핵심 개념과 이론적 배경 이해"
                elif category.name == "실습/예제":
                    description = "실제 사례를 통한 실습과 연습"
                elif category.name == "도구/기술":
                    description = "관련 도구와 기술 스택 학습"
                elif category.name == "심화/고급":
                    description = "전문적이고 깊이 있는 지식 습득"
                else:
                    description = "추가 학습과 참고를 위한 자료"
                
                # 카테고리 내에서 문서를 단어 수 기준으로 정렬 (쉬운 것부터)
                sorted_docs = sorted(category.documents, key=lambda d: d.word_count)
                
                step = LearningPathStep(
                    step=step_counter,
                    title=f"{step_counter}단계: {category.name}",
                    documents=sorted_docs[:5],  # 최대 5개 문서
                    description=description,
                    difficulty_level=difficulty
                )
                
                learning_path.append(step)
                step_counter += 1
            
            logger.info(f"학습 경로 생성: {len(learning_path)}단계")
            return learning_path
            
        except Exception as e:
            logger.error(f"학습 경로 생성 실패: {e}")
            return []
    
    def _extract_related_topics(self, collection: DocumentCollection) -> List[Tuple[str, int]]:
        """관련 주제 추출"""
        try:
            # TopicCollector의 기능 활용
            related_topics = self.topic_collector.suggest_related_topics(
                collection.metadata.topic, 
                top_k=10
            )
            
            logger.info(f"관련 주제 {len(related_topics)}개 추출")
            return related_topics
            
        except Exception as e:
            logger.error(f"관련 주제 추출 실패: {e}")
            return []
    
    def _get_recent_updates(self, documents: List[Document]) -> List[Document]:
        """최근 업데이트된 문서 목록"""
        try:
            # 최근 N일 이내 수정된 문서들
            cutoff_date = datetime.now() - timedelta(days=self.recent_days)
            recent_docs = [
                doc for doc in documents 
                if doc.modified_at and doc.modified_at > cutoff_date
            ]
            
            # 수정일 순으로 정렬 (최신 순)
            recent_docs.sort(key=lambda d: d.modified_at, reverse=True)
            
            logger.info(f"최근 {self.recent_days}일 이내 업데이트: {len(recent_docs)}개")
            return recent_docs[:10]  # 최대 10개
            
        except Exception as e:
            logger.error(f"최근 업데이트 분석 실패: {e}")
            return []
    
    def _analyze_document_relationships(self, documents: List[Document]) -> List[DocumentRelationship]:
        """문서 간 관계 분석"""
        try:
            relationships = []
            
            # 문서 간 유사도 기반 관계 분석
            for i, doc1 in enumerate(documents):
                for doc2 in documents[i+1:]:
                    # 간단한 유사도 계산 (제목과 태그 기반)
                    similarity = self._calculate_document_similarity(doc1, doc2)
                    
                    if similarity > self.relationship_threshold:
                        relationship = DocumentRelationship(
                            source_doc=doc1,
                            target_doc=doc2,
                            relationship_type="similar",
                            strength=similarity
                        )
                        relationships.append(relationship)
            
            # 강한 관계 순으로 정렬
            relationships.sort(key=lambda r: r.strength, reverse=True)
            
            logger.info(f"문서 관계 {len(relationships)}개 발견")
            return relationships[:20]  # 최대 20개 관계
            
        except Exception as e:
            logger.error(f"문서 관계 분석 실패: {e}")
            return []
    
    def _calculate_document_similarity(self, doc1: Document, doc2: Document) -> float:
        """두 문서 간 유사도 계산"""
        try:
            similarity = 0.0
            
            # 태그 유사도
            if doc1.tags and doc2.tags:
                tags1 = set(tag.lower() for tag in doc1.tags)
                tags2 = set(tag.lower() for tag in doc2.tags)
                
                if tags1 and tags2:
                    tag_similarity = len(tags1.intersection(tags2)) / len(tags1.union(tags2))
                    similarity += tag_similarity * 0.7
            
            # 제목 유사도 (간단한 단어 겹침 기반)
            title1_words = set(doc1.title.lower().split())
            title2_words = set(doc2.title.lower().split())
            
            if title1_words and title2_words:
                title_similarity = len(title1_words.intersection(title2_words)) / len(title1_words.union(title2_words))
                similarity += title_similarity * 0.3
            
            return similarity
            
        except Exception as e:
            logger.error(f"문서 유사도 계산 실패: {e}")
            return 0.0
    
    def _generate_moc_statistics(self, documents: List[Document], categories: List[DocumentCategory], relationships: List[DocumentRelationship]) -> Dict:
        """MOC 통계 정보 생성"""
        try:
            statistics = {
                "total_documents": len(documents),
                "total_categories": len(categories),
                "total_relationships": len(relationships),
                "category_distribution": {
                    cat.name: len(cat.documents) for cat in categories
                },
                "word_count_distribution": {
                    "total": sum(doc.word_count for doc in documents),
                    "average": sum(doc.word_count for doc in documents) // len(documents) if documents else 0,
                    "min": min(doc.word_count for doc in documents) if documents else 0,
                    "max": max(doc.word_count for doc in documents) if documents else 0
                },
                "tag_coverage": len(set(tag for doc in documents for tag in doc.tags)) if documents else 0
            }
            
            return statistics
            
        except Exception as e:
            logger.error(f"통계 생성 실패: {e}")
            return {}
    
    def _create_empty_moc(self, topic: str) -> MOCData:
        """빈 MOC 데이터 생성"""
        return MOCData(
            topic=topic,
            overview=f"'{topic}' 주제에 대한 문서를 찾을 수 없습니다.",
            total_documents=0,
            core_documents=[],
            categories=[],
            learning_path=[],
            related_topics=[],
            recent_updates=[],
            relationships=[],
            generation_date=datetime.now(),
            statistics={}
        )
    
    def _export_moc(self, moc_data: MOCData, output_file: str) -> bool:
        """MOC를 마크다운 파일로 내보내기"""
        try:
            content = self._format_as_markdown(moc_data)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info(f"MOC 파일 저장 완료: {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"MOC 파일 저장 실패: {e}")
            return False
    
    def _format_as_markdown(self, moc_data: MOCData) -> str:
        """MOC 데이터를 마크다운 형식으로 변환"""
        try:
            lines = []
            
            # 헤더와 메타데이터
            lines.append("---")
            lines.append("tags:")
            lines.append("  - vault-intelligence/moc")
            lines.append(f"  - topic/{moc_data.topic.lower().replace(' ', '-')}")
            lines.append(f"generated: {moc_data.generation_date.isoformat()}")
            lines.append(f"topic: {moc_data.topic}")
            lines.append(f"total_documents: {moc_data.total_documents}")
            lines.append("---")
            lines.append("")
            
            # 제목
            lines.append(f"# 📚 {moc_data.topic} Map of Content")
            lines.append("")
            
            # 생성 정보
            lines.append(f"*생성일: {moc_data.generation_date.strftime('%Y-%m-%d %H:%M:%S')}*")
            lines.append("")
            
            # 개요
            lines.append("## 🎯 개요")
            lines.append("")
            lines.append(moc_data.overview)
            lines.append("")
            
            # 핵심 문서
            if moc_data.core_documents:
                lines.append("## 🌟 핵심 문서")
                lines.append("")
                lines.append("이 주제에서 가장 중요하고 핵심적인 문서들입니다:")
                lines.append("")
                for i, doc in enumerate(moc_data.core_documents, 1):
                    lines.append(f"{i}. **[[{doc.path}]]**")
                    if doc.word_count:
                        lines.append(f"   - {doc.word_count:,} 단어")
                    if doc.tags:
                        tags_str = ", ".join(f"#{tag}" for tag in doc.tags[:3])
                        lines.append(f"   - {tags_str}")
                    lines.append("")
            
            # 카테고리별 분류
            if moc_data.categories:
                lines.append("## 📖 카테고리별 분류")
                lines.append("")
                
                for category in moc_data.categories:
                    lines.append(f"### {category.name}")
                    lines.append("")
                    lines.append(f"*{category.description}*")
                    lines.append("")
                    
                    for doc in category.documents:
                        lines.append(f"- **[[{doc.path}]]**")
                        info_parts = []
                        if doc.word_count:
                            info_parts.append(f"{doc.word_count:,} 단어")
                        if doc.tags:
                            tags_str = ", ".join(f"#{tag}" for tag in doc.tags[:2])
                            info_parts.append(tags_str)
                        
                        if info_parts:
                            lines.append(f"  - {' | '.join(info_parts)}")
                    
                    lines.append("")
            
            # 학습 경로
            if moc_data.learning_path:
                lines.append("## 🛤️ 추천 학습 경로")
                lines.append("")
                lines.append("체계적인 학습을 위한 단계별 가이드입니다:")
                lines.append("")
                
                for step in moc_data.learning_path:
                    lines.append(f"### {step.title}")
                    lines.append("")
                    lines.append(f"**난이도**: {step.difficulty_level}  ")
                    lines.append(f"**설명**: {step.description}")
                    lines.append("")
                    lines.append("**추천 문서:**")
                    
                    for doc in step.documents:
                        lines.append(f"- [[{doc.path}]]")
                    
                    lines.append("")
            
            # 관련 주제
            if moc_data.related_topics:
                lines.append("## 🔗 관련 주제")
                lines.append("")
                lines.append("이 주제와 연관된 다른 주제들:")
                lines.append("")
                
                for topic, count in moc_data.related_topics:
                    lines.append(f"- **{topic}** ({count}개 문서)")
                
                lines.append("")
            
            # 최근 업데이트
            if moc_data.recent_updates:
                lines.append("## 📅 최근 업데이트")
                lines.append("")
                lines.append(f"최근 {self.recent_days}일 이내에 업데이트된 문서들:")
                lines.append("")
                
                for doc in moc_data.recent_updates:
                    update_date = doc.modified_at.strftime('%Y-%m-%d')
                    lines.append(f"- **[[{doc.path}]]** ({update_date})")
                
                lines.append("")
            
            # 문서 관계도
            if moc_data.relationships:
                lines.append("## 📊 문서 관계도")
                lines.append("")
                lines.append("주요 문서들 간의 관련성:")
                lines.append("")
                
                for rel in moc_data.relationships[:10]:  # 상위 10개만
                    strength_emoji = "🔗" if rel.strength > 0.8 else "↔️"
                    lines.append(f"- {strength_emoji} [[{rel.source_doc.path}]] ↔ [[{rel.target_doc.path}]] ({rel.strength:.2f})")
                
                lines.append("")
            
            # 통계 정보
            if moc_data.statistics:
                stats = moc_data.statistics
                lines.append("## 📈 통계")
                lines.append("")
                lines.append(f"- **총 문서**: {stats.get('total_documents', 0)}개")
                lines.append(f"- **총 카테고리**: {stats.get('total_categories', 0)}개")
                lines.append(f"- **문서 관계**: {stats.get('total_relationships', 0)}개")
                
                word_stats = stats.get('word_count_distribution', {})
                if word_stats:
                    lines.append(f"- **총 단어 수**: {word_stats.get('total', 0):,}개")
                    lines.append(f"- **평균 단어 수**: {word_stats.get('average', 0):,}개")
                
                lines.append("")
            
            # 푸터
            lines.append("---")
            lines.append("")
            lines.append("*이 MOC는 Vault Intelligence System V2에 의해 자동 생성되었습니다.*  ")
            lines.append(f"*생성 시간: {moc_data.generation_date.strftime('%Y-%m-%d %H:%M:%S')}*")
            
            return "\n".join(lines)
            
        except Exception as e:
            logger.error(f"마크다운 형식 변환 실패: {e}")
            return f"# {moc_data.topic} MOC\n\nMOC 생성 중 오류가 발생했습니다."


def test_moc_generator():
    """MOC 생성기 테스트"""
    import tempfile
    import shutil
    from ..features.advanced_search import AdvancedSearchEngine
    
    try:
        print("🧪 MOC 생성기 테스트 시작...")
        
        # 임시 vault 및 캐시 생성
        temp_vault = tempfile.mkdtemp()
        temp_cache = tempfile.mkdtemp()
        
        # 다양한 카테고리의 테스트 문서들 생성
        test_docs = [
            ("tdd-introduction.md", """---
tags:
  - development/tdd
  - learning/basic
---

# TDD 입문 가이드

TDD(Test-Driven Development)는 테스트를 먼저 작성하고 구현하는 개발 방법론입니다.
초보자를 위한 기본적인 개념과 시작 방법을 설명합니다.
"""),
            
            ("tdd-concepts.md", """---
tags:
  - development/tdd
  - theory/concept
---

# TDD 핵심 개념

Red-Green-Refactor 사이클의 이론적 배경과 
TDD의 핵심 원리들을 상세히 설명합니다.
"""),
            
            ("tdd-practice.md", """---
tags:
  - development/tdd
  - practice/example
---

# TDD 실습 예제

실제 코드를 통한 TDD 실습 가이드입니다.
단계별 예제와 연습 문제가 포함되어 있습니다.
"""),
            
            ("tdd-advanced.md", """---
tags:
  - development/tdd
  - advanced/expert
---

# 고급 TDD 기법

복잡한 상황에서의 TDD 적용 방법과
전문적인 테스팅 패턴들을 다룹니다.
"""),
            
            ("junit-guide.md", """---
tags:
  - tools/junit
  - testing/framework
---

# JUnit 사용 가이드

Java TDD를 위한 JUnit 프레임워크 사용법과
다양한 테스트 도구들을 소개합니다.
"""),
            
            ("testing-resources.md", """---
tags:
  - reference/testing
  - resources/documentation
---

# 테스팅 참고 자료

TDD와 테스팅에 관한 추가 학습 자료와
유용한 참고 문서들의 모음입니다.
""")
        ]
        
        for filename, content in test_docs:
            with open(Path(temp_vault) / filename, 'w', encoding='utf-8') as f:
                f.write(content)
        
        # 검색 엔진 초기화 및 인덱싱
        config = {
            "model": {"name": "BAAI/bge-m3"},
            "vault": {"excluded_dirs": [], "file_extensions": [".md"]},
            "moc": {
                "max_core_documents": 3,
                "max_category_documents": 5,
                "recent_days": 30,
                "min_similarity_threshold": 0.3,
                "relationship_threshold": 0.5
            }
        }
        
        search_engine = AdvancedSearchEngine(temp_vault, temp_cache, config)
        print("🔍 검색 엔진 인덱싱 중...")
        if not search_engine.build_index():
            print("❌ 인덱싱 실패")
            return False
        
        # MOC 생성기 초기화
        moc_generator = MOCGenerator(search_engine, config)
        
        # TDD MOC 생성 테스트
        print("\n📚 'TDD' MOC 생성 중...")
        moc_data = moc_generator.generate_moc(
            topic="TDD",
            top_k=20,
            threshold=0.2,
            use_expansion=True
        )
        
        print(f"\n📊 MOC 생성 결과:")
        print(f"- 주제: {moc_data.topic}")
        print(f"- 총 문서: {moc_data.total_documents}개")
        print(f"- 핵심 문서: {len(moc_data.core_documents)}개")
        print(f"- 카테고리: {len(moc_data.categories)}개")
        print(f"- 학습 단계: {len(moc_data.learning_path)}개")
        print(f"- 문서 관계: {len(moc_data.relationships)}개")
        
        if moc_data.categories:
            print(f"\n📋 카테고리별 문서:")
            for category in moc_data.categories:
                print(f"  {category.name}: {len(category.documents)}개 문서")
        
        if moc_data.learning_path:
            print(f"\n🛤️ 학습 경로:")
            for step in moc_data.learning_path:
                print(f"  {step.step}. {step.title} ({step.difficulty_level})")
        
        # 마크다운 내보내기 테스트
        output_file = Path(temp_cache) / "TDD-MOC.md"
        if moc_generator._export_moc(moc_data, str(output_file)):
            print(f"\n💾 MOC 파일 저장: {output_file}")
            
            # 생성된 파일 일부 확인
            with open(output_file, 'r', encoding='utf-8') as f:
                content = f.read()
                print(f"\n📝 생성된 MOC 파일 일부:")
                print(content[:800] + "..." if len(content) > 800 else content)
        
        # 정리
        shutil.rmtree(temp_vault)
        shutil.rmtree(temp_cache)
        
        print("✅ MOC 생성기 테스트 완료!")
        return True
        
    except Exception as e:
        print(f"❌ MOC 생성기 테스트 실패: {e}")
        return False


if __name__ == "__main__":
    test_moc_generator()