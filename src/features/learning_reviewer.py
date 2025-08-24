#!/usr/bin/env python3
"""
Learning Reviewer for Vault Intelligence System V2 - Phase 9

시간 기반 학습 활동 분석 및 리뷰 생성 시스템
"""

import os
import logging
from typing import List, Dict, Optional, Tuple, Union
from pathlib import Path
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from collections import defaultdict, Counter

from ..core.vault_processor import Document, VaultProcessor
from .advanced_search import AdvancedSearchEngine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class LearningActivity:
    """학습 활동 정보"""
    date: datetime
    action: str  # created, modified
    document: Document
    activity_score: float = 1.0


@dataclass
class TopicProgress:
    """주제별 학습 진전도"""
    topic: str
    documents_count: int
    activity_count: int
    creation_count: int
    modification_count: int
    average_word_count: float
    first_activity: datetime
    last_activity: datetime
    progress_score: float
    growth_rate: float


@dataclass
class LearningInsight:
    """학습 인사이트"""
    insight_type: str  # strength, weakness, trend, recommendation
    title: str
    description: str
    evidence: List[str]
    confidence_score: float


@dataclass
class LearningReview:
    """학습 리뷰 결과"""
    period: str
    start_date: datetime
    end_date: datetime
    total_activities: int
    documents_created: int
    documents_modified: int
    active_days: int
    topic_progress: List[TopicProgress]
    learning_insights: List[LearningInsight]
    recommendations: List[str]
    strengths: List[str]
    weaknesses: List[str]
    trending_topics: List[str]
    quality_score: float
    generated_at: datetime


class LearningReviewer:
    """시간 기반 학습 활동 분석 및 리뷰 생성"""
    
    def __init__(self, 
                 search_engine: AdvancedSearchEngine,
                 config: dict):
        """
        LearningReviewer 초기화
        
        Args:
            search_engine: 검색 엔진
            config: 설정 정보
        """
        self.search_engine = search_engine
        self.processor = search_engine.processor
        self.config = config
        
        # 학습 리뷰 설정
        learning_config = config.get('learning_review', {})
        self.default_period = learning_config.get('default_period', 'weekly')
        self.include_activity_stats = learning_config.get('include_activity_stats', True)
        self.include_topic_analysis = learning_config.get('include_topic_analysis', True)
        self.include_progress_tracking = learning_config.get('include_progress_tracking', True)
        self.include_recommendations = learning_config.get('include_recommendations', True)
        
        # 기간별 설정
        self.period_configs = learning_config.get('periods', {})
        
        # 진전도 측정 설정
        progress_config = learning_config.get('progress_tracking', {})
        self.min_topic_documents = progress_config.get('min_topic_documents', 5)
        self.growth_calculation_method = progress_config.get('growth_calculation_method', 'exponential')
        self.benchmark_period_days = progress_config.get('benchmark_period_days', 30)
        self.significance_threshold = progress_config.get('significance_threshold', 0.1)
        
        logger.info(f"LearningReviewer 초기화 완료 - 기본 기간: {self.default_period}")
    
    def generate_learning_review(self,
                               period: str = None,
                               start_date: datetime = None,
                               end_date: datetime = None,
                               topic_filter: str = None) -> LearningReview:
        """
        학습 리뷰 생성
        
        Args:
            period: 리뷰 기간 ('weekly', 'monthly', 'quarterly')
            start_date: 시작 날짜 (지정하지 않으면 period에 따라 자동 계산)
            end_date: 종료 날짜 (지정하지 않으면 현재)
            topic_filter: 특정 주제 필터
            
        Returns:
            LearningReview: 학습 리뷰 결과
        """
        period = period or self.default_period
        
        # 날짜 범위 설정
        if not end_date:
            end_date = datetime.now()
        
        if not start_date:
            start_date = self._calculate_start_date(end_date, period)
        
        logger.info(f"{period} 학습 리뷰 생성: {start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}")
        
        # 학습 활동 수집
        activities = self._collect_learning_activities(start_date, end_date, topic_filter)
        
        # 주제별 진전도 분석
        topic_progress = self._analyze_topic_progress(activities, start_date, end_date)
        
        # 학습 인사이트 생성
        insights = self._generate_learning_insights(activities, topic_progress, period)
        
        # 권장사항 생성
        recommendations = self._generate_recommendations(activities, topic_progress, insights)
        
        # 강점/약점 분석
        strengths, weaknesses = self._analyze_strengths_weaknesses(topic_progress, insights)
        
        # 트렌딩 주제 식별
        trending_topics = self._identify_trending_topics(activities, topic_progress)
        
        # 품질 점수 계산
        quality_score = self._calculate_review_quality(activities, topic_progress, insights)
        
        # 학습 활동 통계
        total_activities = len(activities)
        documents_created = sum(1 for act in activities if act.action == 'created')
        documents_modified = sum(1 for act in activities if act.action == 'modified')
        active_days = len(set(act.date.date() for act in activities))
        
        review = LearningReview(
            period=period,
            start_date=start_date,
            end_date=end_date,
            total_activities=total_activities,
            documents_created=documents_created,
            documents_modified=documents_modified,
            active_days=active_days,
            topic_progress=topic_progress,
            learning_insights=insights,
            recommendations=recommendations,
            strengths=strengths,
            weaknesses=weaknesses,
            trending_topics=trending_topics,
            quality_score=quality_score,
            generated_at=datetime.now()
        )
        
        logger.info(f"학습 리뷰 생성 완료 - 활동: {total_activities}개, 주제: {len(topic_progress)}개, 품질: {quality_score:.3f}")
        return review
    
    def _calculate_start_date(self, end_date: datetime, period: str) -> datetime:
        """기간에 따른 시작 날짜 계산"""
        if period == 'weekly':
            return end_date - timedelta(days=7)
        elif period == 'monthly':
            return end_date - timedelta(days=30)
        elif period == 'quarterly':
            return end_date - timedelta(days=90)
        else:
            return end_date - timedelta(days=7)  # 기본값
    
    def _collect_learning_activities(self,
                                   start_date: datetime,
                                   end_date: datetime,
                                   topic_filter: str = None) -> List[LearningActivity]:
        """학습 활동 수집"""
        logger.info("학습 활동 수집 중...")
        
        # 모든 문서 가져오기
        documents = self.processor.get_all_documents()
        activities = []
        
        for doc in documents:
            # 주제 필터 적용
            if topic_filter:
                if not self._document_matches_topic(doc, topic_filter):
                    continue
            
            # 문서 생성 활동
            if start_date <= doc.modified_at <= end_date:
                activity = LearningActivity(
                    date=doc.modified_at,
                    action='modified',  # modified_at을 기준으로 함
                    document=doc,
                    activity_score=self._calculate_activity_score(doc, 'modified')
                )
                activities.append(activity)
        
        # 날짜순 정렬
        activities.sort(key=lambda x: x.date)
        
        logger.info(f"학습 활동 수집 완료: {len(activities)}개 활동")
        return activities
    
    def _document_matches_topic(self, doc: Document, topic: str) -> bool:
        """문서가 특정 주제와 일치하는지 확인"""
        topic_lower = topic.lower()
        
        # 제목에서 검색
        if topic_lower in doc.title.lower():
            return True
        
        # 태그에서 검색
        for tag in doc.tags:
            if topic_lower in tag.lower():
                return True
        
        # 내용에서 검색 (간단한 키워드 매칭)
        if topic_lower in doc.content.lower():
            return True
        
        return False
    
    def _calculate_activity_score(self, doc: Document, action: str) -> float:
        """활동 점수 계산"""
        base_score = 1.0
        
        # 문서 길이에 따른 가중치
        if doc.word_count > 1000:
            base_score += 0.5
        elif doc.word_count > 500:
            base_score += 0.2
        
        # 태그 수에 따른 가중치
        if len(doc.tags) > 5:
            base_score += 0.3
        elif len(doc.tags) > 2:
            base_score += 0.1
        
        return base_score
    
    def _analyze_topic_progress(self,
                              activities: List[LearningActivity],
                              start_date: datetime,
                              end_date: datetime) -> List[TopicProgress]:
        """주제별 진전도 분석"""
        logger.info("주제별 진전도 분석 중...")
        
        # 태그 기반 주제 그룹화
        topic_activities = defaultdict(list)
        
        for activity in activities:
            doc = activity.document
            # 문서의 모든 태그를 주제로 취급
            for tag in doc.tags:
                if tag:  # 빈 태그 제외
                    topic_activities[tag].append(activity)
        
        topic_progress_list = []
        
        for topic, topic_acts in topic_activities.items():
            if len(topic_acts) < 1:  # 최소 1개 활동 필요 (테스트용)
                continue
            
            # 기본 통계
            documents = [act.document for act in topic_acts]
            unique_docs = {doc.path: doc for doc in documents}
            
            creation_count = sum(1 for act in topic_acts if act.action == 'created')
            modification_count = sum(1 for act in topic_acts if act.action == 'modified')
            
            word_counts = [doc.word_count for doc in unique_docs.values()]
            avg_word_count = sum(word_counts) / len(word_counts) if word_counts else 0
            
            first_activity = min(act.date for act in topic_acts)
            last_activity = max(act.date for act in topic_acts)
            
            # 진전도 점수 계산
            progress_score = self._calculate_progress_score(topic_acts, unique_docs.values())
            
            # 성장률 계산
            growth_rate = self._calculate_growth_rate(topic_acts, start_date, end_date)
            
            topic_progress = TopicProgress(
                topic=topic,
                documents_count=len(unique_docs),
                activity_count=len(topic_acts),
                creation_count=creation_count,
                modification_count=modification_count,
                average_word_count=avg_word_count,
                first_activity=first_activity,
                last_activity=last_activity,
                progress_score=progress_score,
                growth_rate=growth_rate
            )
            
            topic_progress_list.append(topic_progress)
        
        # 진전도 점수순 정렬
        topic_progress_list.sort(key=lambda x: x.progress_score, reverse=True)
        
        logger.info(f"주제별 진전도 분석 완료: {len(topic_progress_list)}개 주제")
        return topic_progress_list
    
    def _calculate_progress_score(self, activities: List[LearningActivity], documents) -> float:
        """진전도 점수 계산"""
        if not activities:
            return 0.0
        
        base_score = 0.5
        
        # 활동량 점수 (정규화)
        activity_score = min(len(activities) / 10.0, 0.3)  # 최대 0.3점
        
        # 문서 품질 점수 (단어 수 기준)
        avg_words = sum(doc.word_count for doc in documents) / len(documents)
        quality_score = min(avg_words / 1000.0, 0.2)  # 최대 0.2점
        
        return base_score + activity_score + quality_score
    
    def _calculate_growth_rate(self, activities: List[LearningActivity], start_date: datetime, end_date: datetime) -> float:
        """성장률 계산"""
        if len(activities) < 2:
            return 0.0
        
        # 시간을 두 구간으로 나누어 비교
        mid_date = start_date + (end_date - start_date) / 2
        
        early_activities = [act for act in activities if act.date <= mid_date]
        late_activities = [act for act in activities if act.date > mid_date]
        
        if not early_activities:
            return 1.0  # 최근에만 활동이 있으면 높은 성장률
        
        early_score = sum(act.activity_score for act in early_activities)
        late_score = sum(act.activity_score for act in late_activities)
        
        if early_score == 0:
            return 1.0
        
        growth_rate = (late_score - early_score) / early_score
        return max(-1.0, min(1.0, growth_rate))  # -100% ~ +100%로 제한
    
    def _generate_learning_insights(self,
                                  activities: List[LearningActivity],
                                  topic_progress: List[TopicProgress],
                                  period: str) -> List[LearningInsight]:
        """학습 인사이트 생성"""
        logger.info("학습 인사이트 생성 중...")
        
        insights = []
        
        # 가장 활발한 주제
        if topic_progress:
            most_active = topic_progress[0]
            insights.append(LearningInsight(
                insight_type="strength",
                title=f"가장 활발한 학습 주제",
                description=f"'{most_active.topic}' 주제에서 {most_active.activity_count}개 활동 기록",
                evidence=[f"진전도 점수: {most_active.progress_score:.3f}"],
                confidence_score=0.9
            ))
        
        # 성장률이 높은 주제
        growing_topics = [tp for tp in topic_progress if tp.growth_rate > 0.3]
        if growing_topics:
            best_growth = max(growing_topics, key=lambda x: x.growth_rate)
            insights.append(LearningInsight(
                insight_type="trend",
                title="급성장 주제",
                description=f"'{best_growth.topic}' 주제가 {best_growth.growth_rate:.1%} 성장",
                evidence=[f"활동 증가율: {best_growth.growth_rate:.1%}"],
                confidence_score=0.8
            ))
        
        # 활동량 분석
        if len(activities) > 0:
            active_days_ratio = len(set(act.date.date() for act in activities)) / 7.0  # 주간 기준
            if active_days_ratio > 0.5:
                insights.append(LearningInsight(
                    insight_type="strength",
                    title="꾸준한 학습 습관",
                    description=f"{period} 기간 중 {active_days_ratio:.1%}의 날에 학습 활동",
                    evidence=[f"총 {len(activities)}개 활동"],
                    confidence_score=0.7
                ))
        
        # 저조한 주제 식별
        weak_topics = [tp for tp in topic_progress if tp.progress_score < 0.3]
        if weak_topics and len(topic_progress) > 1:
            insights.append(LearningInsight(
                insight_type="weakness",
                title="관심 부족 주제",
                description=f"{len(weak_topics)}개 주제에서 활동 저조",
                evidence=[f"최저 진전도: {min(tp.progress_score for tp in weak_topics):.3f}"],
                confidence_score=0.6
            ))
        
        logger.info(f"학습 인사이트 생성 완료: {len(insights)}개")
        return insights
    
    def _generate_recommendations(self,
                                activities: List[LearningActivity],
                                topic_progress: List[TopicProgress],
                                insights: List[LearningInsight]) -> List[str]:
        """권장사항 생성"""
        recommendations = []
        
        # 가장 활발한 주제를 더 깊이 학습
        if topic_progress:
            top_topic = topic_progress[0]
            recommendations.append(f"'{top_topic.topic}' 주제의 심화 학습 자료 추가 수집 권장")
        
        # 저조한 주제 개선
        weak_topics = [tp for tp in topic_progress if tp.progress_score < 0.4]
        if weak_topics:
            recommendations.append(f"활동이 저조한 {len(weak_topics)}개 주제에 더 집중")
        
        # 성장률이 높은 주제 계속 투자
        growing_topics = [tp for tp in topic_progress if tp.growth_rate > 0.2]
        if growing_topics:
            best_growth = max(growing_topics, key=lambda x: x.growth_rate)
            recommendations.append(f"성장세가 좋은 '{best_growth.topic}' 주제 지속 투자")
        
        # 전반적인 활동량에 따른 권장
        if len(activities) < 5:
            recommendations.append("학습 활동량을 늘려 더 많은 지식 축적 권장")
        elif len(activities) > 20:
            recommendations.append("높은 학습 활동량 유지, 품질과 깊이에 더 집중")
        
        return recommendations
    
    def _analyze_strengths_weaknesses(self,
                                    topic_progress: List[TopicProgress],
                                    insights: List[LearningInsight]) -> Tuple[List[str], List[str]]:
        """강점/약점 분석"""
        strengths = []
        weaknesses = []
        
        # 인사이트에서 강점/약점 추출
        for insight in insights:
            if insight.insight_type == "strength":
                strengths.append(insight.title)
            elif insight.insight_type == "weakness":
                weaknesses.append(insight.title)
        
        # 추가 강점/약점 분석
        if len(topic_progress) > 5:
            strengths.append(f"다양한 주제 ({len(topic_progress)}개) 학습")
        
        high_quality_topics = [tp for tp in topic_progress if tp.average_word_count > 800]
        if high_quality_topics:
            strengths.append(f"상세한 내용 작성 ({len(high_quality_topics)}개 주제)")
        
        shallow_topics = [tp for tp in topic_progress if tp.average_word_count < 200]
        if shallow_topics and len(topic_progress) > 1:
            weaknesses.append(f"내용이 부족한 주제 ({len(shallow_topics)}개)")
        
        return strengths, weaknesses
    
    def _identify_trending_topics(self,
                                activities: List[LearningActivity],
                                topic_progress: List[TopicProgress]) -> List[str]:
        """트렌딩 주제 식별"""
        # 성장률이 높은 상위 3개 주제
        sorted_by_growth = sorted(topic_progress, key=lambda x: x.growth_rate, reverse=True)
        trending = [tp.topic for tp in sorted_by_growth[:3] if tp.growth_rate > 0.1]
        
        return trending
    
    def _calculate_review_quality(self,
                                activities: List[LearningActivity],
                                topic_progress: List[TopicProgress],
                                insights: List[LearningInsight]) -> float:
        """리뷰 품질 점수 계산"""
        base_score = 0.5
        
        # 활동량 점수
        if len(activities) > 10:
            base_score += 0.2
        elif len(activities) > 5:
            base_score += 0.1
        
        # 주제 다양성 점수
        if len(topic_progress) > 5:
            base_score += 0.2
        elif len(topic_progress) > 2:
            base_score += 0.1
        
        # 인사이트 품질 점수
        high_confidence_insights = [i for i in insights if i.confidence_score > 0.7]
        if len(high_confidence_insights) > 2:
            base_score += 0.1
        
        return min(1.0, base_score)


def test_learning_reviewer():
    """LearningReviewer 테스트"""
    print("🧪 LearningReviewer 테스트 시작...")
    
    try:
        # Mock 설정
        config = {
            'learning_review': {
                'default_period': 'weekly',
                'periods': {
                    'weekly': {'min_documents': 2}
                }
            }
        }
        
        # Mock SearchEngine과 Processor 생성
        class MockProcessor:
            def get_all_documents(self):
                from datetime import datetime
                from ..core.vault_processor import Document
                
                return [
                    Document(
                        path="test1.md", title="TDD 기초", content="테스트 주도 개발",
                        tags=["tdd", "testing"], frontmatter={}, word_count=500, char_count=2000,
                        file_size=100, modified_at=datetime.now() - timedelta(days=1), file_hash="hash1"
                    ),
                    Document(
                        path="test2.md", title="리팩토링", content="코드 개선", 
                        tags=["refactoring", "clean-code"], frontmatter={}, word_count=300, char_count=1200,
                        file_size=80, modified_at=datetime.now() - timedelta(days=2), file_hash="hash2"
                    )
                ]
        
        class MockSearchEngine:
            def __init__(self):
                self.processor = MockProcessor()
        
        search_engine = MockSearchEngine()
        
        # LearningReviewer 생성
        reviewer = LearningReviewer(search_engine, config)
        
        # 학습 리뷰 생성 테스트
        review = reviewer.generate_learning_review(period="weekly")
        
        # 결과 검증
        assert review is not None, "리뷰가 생성되지 않음"
        assert review.period == "weekly", "기간 설정 오류"
        assert review.total_activities >= 0, "활동 수집 실패"
        assert review.quality_score >= 0, "품질 점수 계산 실패"
        
        print(f"✅ 학습 리뷰 생성 성공")
        print(f"   기간: {review.period}")
        print(f"   총 활동: {review.total_activities}개")
        print(f"   주제 수: {len(review.topic_progress)}개")
        print(f"   인사이트: {len(review.learning_insights)}개")
        print(f"   품질 점수: {review.quality_score:.3f}")
        
        return True
        
    except Exception as e:
        print(f"❌ LearningReviewer 테스트 실패: {e}")
        return False


if __name__ == "__main__":
    test_learning_reviewer()