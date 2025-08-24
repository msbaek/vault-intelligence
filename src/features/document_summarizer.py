#!/usr/bin/env python3
"""
Document Summarizer for Vault Intelligence System V2 - Phase 9

Claude Code LLM을 활용한 문서 그룹 요약 시스템
"""

import os
import logging
from typing import List, Dict, Optional, Tuple, Union
from pathlib import Path
from dataclasses import dataclass, asdict
from datetime import datetime

from .content_clusterer import DocumentCluster, ClusteringResult
from ..core.vault_processor import Document
from ..utils.claude_code_integration import ClaudeCodeIntegration

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class SummaryRequest:
    """요약 요청"""
    cluster: DocumentCluster
    style: str = "detailed"  # brief, detailed, technical, conceptual
    max_length: int = 4000
    focus_areas: List[str] = None
    include_keywords: bool = True
    include_representative_doc: bool = True


@dataclass
class ClusterSummary:
    """클러스터 요약 결과"""
    cluster_id: str
    cluster_label: str
    summary_text: str
    key_insights: List[str]
    main_concepts: List[str]
    practical_tips: List[str]
    related_documents: List[str]
    keywords: List[str]
    representative_doc_title: str
    confidence_score: float
    summary_style: str
    generated_at: datetime


@dataclass
class GroupSummaryResult:
    """전체 그룹 요약 결과"""
    topic: Optional[str]
    cluster_summaries: List[ClusterSummary]
    overall_insights: List[str]
    common_themes: List[str]
    knowledge_gaps: List[str]
    recommended_actions: List[str]
    total_documents: int
    summary_quality_score: float
    generated_at: datetime


class DocumentSummarizer:
    """Claude Code LLM 기반 문서 요약 시스템"""
    
    def __init__(self, config: dict):
        """
        DocumentSummarizer 초기화
        
        Args:
            config: 설정 정보
        """
        self.config = config
        self.summarization_config = config.get('document_summarization', {})
        self.claude_code_config = self.summarization_config.get('claude_code_integration', {})
        
        # 요약 설정
        self.default_style = self.summarization_config.get('default_style', 'detailed')
        self.max_documents_per_cluster = self.summarization_config.get('max_documents_per_cluster', 50)
        self.max_content_length = self.summarization_config.get('max_content_length', 8000)
        self.hierarchical_summary = self.summarization_config.get('hierarchical_summary', True)
        
        # Claude Code LLM 연동 설정
        self.subagent_type = self.claude_code_config.get('subagent_type', 'general-purpose')
        self.max_retries = self.claude_code_config.get('max_retries', 3)
        self.timeout = self.claude_code_config.get('timeout', 300)
        self.chunk_size = self.claude_code_config.get('chunk_size', 4000)
        self.overlap_size = self.claude_code_config.get('overlap_size', 200)
        
        # 스타일별 설정
        self.style_configs = self.summarization_config.get('styles', {})
        
        # Claude Code 통합 모듈 초기화
        self.claude_code = ClaudeCodeIntegration(config)
        
        logger.info(f"DocumentSummarizer 초기화 완료 - 기본 스타일: {self.default_style}")
    
    def summarize_clustering_result(self, 
                                  clustering_result: ClusteringResult,
                                  style: str = None,
                                  topic: str = None) -> GroupSummaryResult:
        """
        클러스터링 결과 전체를 요약
        
        Args:
            clustering_result: 클러스터링 결과
            style: 요약 스타일
            topic: 주제 (선택사항)
            
        Returns:
            GroupSummaryResult: 전체 그룹 요약 결과
        """
        style = style or self.default_style
        logger.info(f"전체 그룹 요약 시작: {len(clustering_result.clusters)}개 클러스터, {style} 스타일")
        
        # 각 클러스터별 요약 생성
        cluster_summaries = []
        total_confidence = 0.0
        
        for cluster in clustering_result.clusters:
            try:
                summary = self.summarize_cluster(cluster, style)
                cluster_summaries.append(summary)
                total_confidence += summary.confidence_score
                
                logger.info(f"클러스터 '{cluster.label}' 요약 완료 (신뢰도: {summary.confidence_score:.3f})")
                
            except Exception as e:
                logger.error(f"클러스터 '{cluster.label}' 요약 실패: {e}")
                # 기본 요약 생성
                fallback_summary = self._create_fallback_summary(cluster, style)
                cluster_summaries.append(fallback_summary)
        
        # 전체 분석 및 통합
        overall_insights = self._generate_overall_insights(cluster_summaries, topic)
        common_themes = self._extract_common_themes(cluster_summaries)
        knowledge_gaps = self._identify_knowledge_gaps(cluster_summaries)
        recommended_actions = self._generate_recommendations(cluster_summaries, topic)
        
        # 품질 점수 계산
        quality_score = total_confidence / len(cluster_summaries) if cluster_summaries else 0.0
        
        result = GroupSummaryResult(
            topic=topic,
            cluster_summaries=cluster_summaries,
            overall_insights=overall_insights,
            common_themes=common_themes,
            knowledge_gaps=knowledge_gaps,
            recommended_actions=recommended_actions,
            total_documents=clustering_result.total_documents,
            summary_quality_score=quality_score,
            generated_at=datetime.now()
        )
        
        logger.info(f"전체 그룹 요약 완료 - 품질 점수: {quality_score:.3f}")
        return result
    
    def summarize_cluster(self, cluster: DocumentCluster, style: str = None) -> ClusterSummary:
        """
        단일 클러스터 요약
        
        Args:
            cluster: 요약할 클러스터
            style: 요약 스타일
            
        Returns:
            ClusterSummary: 클러스터 요약 결과
        """
        style = style or self.default_style
        logger.info(f"클러스터 '{cluster.label}' 요약 시작: {cluster.size}개 문서, {style} 스타일")
        
        # 문서 수 제한
        documents = cluster.documents[:self.max_documents_per_cluster]
        if len(documents) < cluster.size:
            logger.info(f"문서 수 제한: {cluster.size}개 → {len(documents)}개")
        
        # 문서 콘텐츠 준비
        content_chunks = self._prepare_content_for_summarization(documents)
        
        # Claude Code LLM으로 요약 생성
        try:
            # 콘텐츠 준비
            full_content = "\n\n".join(content_chunks)
            cluster_info = {
                'label': cluster.label,
                'keywords': cluster.keywords or [],
                'size': cluster.size
            }
            
            # Claude Code 통합 모듈로 요약 생성
            summary_result = self.claude_code.summarize_documents(
                content=full_content,
                cluster_info=cluster_info,
                style=style
            )
            
            confidence_score = self._calculate_confidence_score(summary_result, cluster)
            
        except Exception as e:
            logger.error(f"LLM 호출 실패: {e}")
            # 폴백 요약 생성
            return self._create_fallback_summary(cluster, style)
        
        # 결과 구성
        cluster_summary = ClusterSummary(
            cluster_id=cluster.id,
            cluster_label=cluster.label,
            summary_text=summary_result.get('summary', ''),
            key_insights=summary_result.get('insights', []),
            main_concepts=summary_result.get('concepts', []),
            practical_tips=summary_result.get('tips', []),
            related_documents=[doc.title for doc in documents],
            keywords=cluster.keywords or [],
            representative_doc_title=cluster.representative_doc.title if cluster.representative_doc else '',
            confidence_score=confidence_score,
            summary_style=style,
            generated_at=datetime.now()
        )
        
        logger.info(f"클러스터 요약 완료: {len(cluster_summary.summary_text)}자")
        return cluster_summary
    
    def _prepare_content_for_summarization(self, documents: List[Document]) -> List[str]:
        """요약을 위한 콘텐츠 준비"""
        content_chunks = []
        current_chunk = ""
        current_length = 0
        
        for doc in documents:
            # 문서 제목과 주요 내용 포함
            doc_content = f"## {doc.title}\n{doc.content[:1000]}..."  # 최대 1000자
            
            if current_length + len(doc_content) > self.chunk_size:
                if current_chunk:
                    content_chunks.append(current_chunk)
                current_chunk = doc_content
                current_length = len(doc_content)
            else:
                current_chunk += f"\n\n{doc_content}"
                current_length += len(doc_content)
        
        if current_chunk:
            content_chunks.append(current_chunk)
        
        logger.info(f"콘텐츠 준비 완료: {len(content_chunks)}개 청크, 총 {current_length}자")
        return content_chunks
    
    
    def _calculate_confidence_score(self, summary_result: Dict, cluster: DocumentCluster) -> float:
        """요약 신뢰도 점수 계산"""
        score = 0.7  # 기본 점수
        
        # 요약 길이 점수
        summary_length = len(summary_result.get('summary', ''))
        if summary_length > 100:
            score += 0.1
        
        # 인사이트 수 점수
        insights_count = len(summary_result.get('insights', []))
        if insights_count >= 3:
            score += 0.1
        
        # 클러스터 크기 점수
        if cluster.size >= 5:
            score += 0.05
        
        # 클러스터 유사도 점수
        if cluster.similarity_score > 0.5:
            score += 0.05
        
        return min(1.0, score)  # 최대 1.0으로 제한
    
    def _create_fallback_summary(self, cluster: DocumentCluster, style: str) -> ClusterSummary:
        """폴백 요약 생성 (LLM 호출 실패시)"""
        logger.warning(f"폴백 요약 생성: {cluster.label}")
        
        return ClusterSummary(
            cluster_id=cluster.id,
            cluster_label=cluster.label,
            summary_text=f"{cluster.label}에 관한 {cluster.size}개 문서의 컬렉션입니다.",
            key_insights=[f"{cluster.label}의 기본 내용"],
            main_concepts=cluster.keywords[:3] if cluster.keywords else [],
            practical_tips=[],
            related_documents=[doc.title for doc in cluster.documents[:5]],
            keywords=cluster.keywords or [],
            representative_doc_title=cluster.representative_doc.title if cluster.representative_doc else '',
            confidence_score=0.3,  # 낮은 신뢰도
            summary_style=style,
            generated_at=datetime.now()
        )
    
    def _generate_overall_insights(self, cluster_summaries: List[ClusterSummary], topic: str = None) -> List[str]:
        """전체 인사이트 생성"""
        insights = []
        
        if topic:
            insights.append(f"{topic} 관련 {len(cluster_summaries)}개 주제군 분석 완료")
        
        # 고신뢰도 요약들에서 인사이트 추출
        high_confidence_summaries = [s for s in cluster_summaries if s.confidence_score > 0.7]
        if high_confidence_summaries:
            insights.append(f"고품질 요약 {len(high_confidence_summaries)}개 생성")
        
        # 문서 수가 많은 클러스터 식별
        large_clusters = [s for s in cluster_summaries if len(s.related_documents) > 10]
        if large_clusters:
            largest_cluster = max(large_clusters, key=lambda s: len(s.related_documents))
            insights.append(f"가장 큰 주제군: {largest_cluster.cluster_label} ({len(largest_cluster.related_documents)}개 문서)")
        
        return insights
    
    def _extract_common_themes(self, cluster_summaries: List[ClusterSummary]) -> List[str]:
        """공통 주제 추출"""
        all_keywords = []
        for summary in cluster_summaries:
            all_keywords.extend(summary.keywords)
        
        # 키워드 빈도 계산
        from collections import Counter
        keyword_freq = Counter(all_keywords)
        
        # 빈도가 높은 키워드들을 공통 주제로 반환
        common_themes = [keyword for keyword, freq in keyword_freq.most_common(5) if freq > 1]
        return common_themes
    
    def _identify_knowledge_gaps(self, cluster_summaries: List[ClusterSummary]) -> List[str]:
        """지식 공백 식별"""
        gaps = []
        
        # 낮은 신뢰도 요약들
        low_confidence_summaries = [s for s in cluster_summaries if s.confidence_score < 0.5]
        if low_confidence_summaries:
            gaps.append(f"품질 개선 필요: {len(low_confidence_summaries)}개 주제군")
        
        # 소규모 클러스터들 (문서가 적은)
        small_clusters = [s for s in cluster_summaries if len(s.related_documents) < 3]
        if small_clusters:
            gaps.append(f"내용 확장 필요: {len(small_clusters)}개 소규모 주제군")
        
        return gaps
    
    def _generate_recommendations(self, cluster_summaries: List[ClusterSummary], topic: str = None) -> List[str]:
        """권장사항 생성"""
        recommendations = []
        
        if topic:
            recommendations.append(f"{topic} 관련 추가 학습 자료 수집 고려")
        
        # 고품질 클러스터 활용 권장
        high_quality_clusters = [s for s in cluster_summaries if s.confidence_score > 0.8]
        if high_quality_clusters:
            best_cluster = max(high_quality_clusters, key=lambda s: s.confidence_score)
            recommendations.append(f"우선 학습 권장: {best_cluster.cluster_label}")
        
        # 소규모 클러스터 보완
        small_clusters = [s for s in cluster_summaries if len(s.related_documents) < 5]
        if len(small_clusters) > len(cluster_summaries) // 2:
            recommendations.append("관련 문서 추가 수집을 통한 주제군 확장 권장")
        
        return recommendations


def test_document_summarizer():
    """DocumentSummarizer 테스트"""
    print("🧪 DocumentSummarizer 테스트 시작...")
    
    try:
        # Mock 설정
        config = {
            'document_summarization': {
                'default_style': 'detailed',
                'max_documents_per_cluster': 10,
                'claude_code_integration': {
                    'subagent_type': 'general-purpose'
                },
                'styles': {
                    'detailed': {
                        'max_sentences': 5,
                        'focus': 'comprehensive'
                    }
                }
            }
        }
        
        # DocumentSummarizer 생성
        summarizer = DocumentSummarizer(config)
        
        # Mock 클러스터 생성 (테스트용)
        from datetime import datetime
        from ..core.vault_processor import Document
        
        test_docs = [
            Document(
                path="test1.md", title="TDD 기초", content="테스트 주도 개발",
                tags=["tdd"], frontmatter={}, word_count=10, char_count=50,
                file_size=100, modified_at=datetime.now(), file_hash="hash1"
            )
        ]
        
        from .content_clusterer import DocumentCluster
        test_cluster = DocumentCluster(
            id="test_cluster",
            label="TDD 기본 개념",
            documents=test_docs,
            keywords=["tdd", "testing"],
            similarity_score=0.8
        )
        
        # 클러스터 요약 테스트
        summary = summarizer.summarize_cluster(test_cluster, "detailed")
        
        # 결과 검증
        assert summary is not None, "요약이 생성되지 않음"
        assert summary.cluster_id == "test_cluster", "클러스터 ID 불일치"
        assert len(summary.summary_text) > 0, "요약 텍스트가 비어있음"
        assert summary.confidence_score > 0, "신뢰도 점수 오류"
        
        print(f"✅ 요약 생성 성공")
        print(f"   클러스터: {summary.cluster_label}")
        print(f"   요약 길이: {len(summary.summary_text)}자")
        print(f"   신뢰도: {summary.confidence_score:.3f}")
        
        return True
        
    except Exception as e:
        print(f"❌ DocumentSummarizer 테스트 실패: {e}")
        return False


if __name__ == "__main__":
    test_document_summarizer()