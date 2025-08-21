#!/usr/bin/env python3
"""
BGE-M3 기반 의미적 태깅 시스템

Obsidian vault의 모든 문서에 대해 BGE-M3 의미 분석을 통한 
일관성 있는 계층적 태그 시스템 구축
"""

import os
import re
import json
import logging
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
from dataclasses import dataclass, asdict
from datetime import datetime
import numpy as np
from collections import defaultdict, Counter

from ..core.sentence_transformer_engine import SentenceTransformerEngine
from ..core.vault_processor import VaultProcessor, Document
from .tag_rule_engine import TagRuleEngine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class TaggingResult:
    """태깅 결과"""
    file_path: str
    original_tags: List[str]
    generated_tags: List[str]
    confidence_scores: Dict[str, float]
    categorized_tags: Dict[str, List[str]]
    processing_time: float
    success: bool
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """딕셔너리로 변환"""
        return asdict(self)


@dataclass
class SemanticAnalysis:
    """문서 의미 분석 결과"""
    key_concepts: Dict[str, float]
    topic_distribution: Dict[str, float]
    semantic_embedding: np.ndarray
    similarity_to_existing: Dict[str, float]


class SemanticTagger:
    """BGE-M3 기반 의미적 태깅 시스템"""
    
    def __init__(self, vault_path: str, config: Dict):
        """
        Args:
            vault_path: Obsidian vault 경로
            config: 설정 딕셔너리
        """
        self.vault_path = Path(vault_path)
        self.config = config
        self.tagging_config = config.get('semantic_tagging', {})
        
        # 핵심 컴포넌트 초기화
        model_config = config.get('model', {})
        tagging_model_config = self.tagging_config
        
        self.embedding_engine = SentenceTransformerEngine(
            model_name=tagging_model_config.get('model_name', model_config.get('name', 'BAAI/bge-m3')),
            cache_dir=model_config.get('cache_folder', 'models/'),
            device=tagging_model_config.get('device', model_config.get('device', 'cpu')),
            use_fp16=tagging_model_config.get('use_fp16', model_config.get('use_fp16', False)),
            batch_size=tagging_model_config.get('batch_size', model_config.get('batch_size', 4)),
            max_length=tagging_model_config.get('max_length', model_config.get('max_length', 4096)),
            num_workers=model_config.get('num_workers', 6)
        )
        vault_config = config.get('vault', {})
        self.vault_processor = VaultProcessor(
            vault_path=vault_path,
            excluded_dirs=vault_config.get('excluded_dirs', None),
            excluded_files=vault_config.get('excluded_files', None), 
            file_extensions=vault_config.get('file_extensions', None)
        )
        self.tag_rule_engine = TagRuleEngine(self.tagging_config)
        
        # 기존 태그 패턴 학습
        self.existing_tags = {}
        self.tag_concepts = defaultdict(list)
        self.concept_tags = defaultdict(list)
        
        if self.tagging_config.get('learn_from_existing', True):
            self._learn_existing_tags()
        
        logger.info(f"의미적 태깅 시스템 초기화 완료: {vault_path}")
    
    def _learn_existing_tags(self) -> None:
        """vault 내 기존 태그 패턴 학습"""
        try:
            logger.info("기존 태그 패턴 학습 시작...")
            
            # 모든 마크다운 파일 찾기
            all_files = self.vault_processor.find_all_files()
            documents = []
            
            # 각 파일을 Document 객체로 변환
            for file_path in all_files:
                document = self.vault_processor.process_file(file_path)
                if document:
                    documents.append(document)
            tag_counter = Counter()
            tag_cooccurrence = defaultdict(Counter)
            
            for doc in documents:
                if not doc.tags:
                    continue
                
                # 정규화된 태그 수집
                normalized_tags = []
                for tag in doc.tags:
                    normalized_tag = self.tag_rule_engine.normalize_tag(tag)
                    if self.tag_rule_engine.validate_tag(normalized_tag):
                        normalized_tags.append(normalized_tag)
                        tag_counter[normalized_tag] += 1
                
                # 태그 공출현 패턴 학습
                for i, tag1 in enumerate(normalized_tags):
                    for tag2 in normalized_tags[i+1:]:
                        tag_cooccurrence[tag1][tag2] += 1
                        tag_cooccurrence[tag2][tag1] += 1
                
                # 문서 내용과 태그 연관성 학습
                if normalized_tags:
                    content_words = self._extract_key_words(doc.content)
                    for tag in normalized_tags:
                        self.tag_concepts[tag].extend(content_words)
                        for word in content_words:
                            self.concept_tags[word].append(tag)
            
            # 빈도 기반 태그 중요도 계산
            total_tags = sum(tag_counter.values())
            self.tag_frequencies = {
                tag: count / total_tags 
                for tag, count in tag_counter.items()
            }
            
            # 태그 공출현 정규화
            self.tag_cooccurrence = {}
            for tag1, related_tags in tag_cooccurrence.items():
                total_cooccur = sum(related_tags.values())
                if total_cooccur > 0:
                    self.tag_cooccurrence[tag1] = {
                        tag2: count / total_cooccur
                        for tag2, count in related_tags.items()
                    }
            
            logger.info(f"태그 학습 완료: {len(tag_counter)}개 태그, {len(tag_cooccurrence)}개 공출현 패턴")
            
        except Exception as e:
            logger.error(f"기존 태그 학습 실패: {e}")
            self.existing_tags = {}
    
    def _extract_key_words(self, content: str, max_words: int = 20) -> List[str]:
        """문서에서 핵심 단어 추출"""
        try:
            # 마크다운 제거 및 정제
            clean_content = re.sub(r'[#*`>\[\](){}]', ' ', content)
            clean_content = re.sub(r'\s+', ' ', clean_content).strip()
            
            # 단어 분리 및 필터링
            words = []
            for word in clean_content.split():
                word = word.lower().strip('.,!?;:"')
                if (len(word) >= 3 and 
                    not word.isdigit() and
                    word not in {'the', 'and', 'for', 'are', 'but', 'not', 
                                'you', 'all', 'can', 'had', 'her', 'was', 
                                'one', 'our', 'out', 'day', 'get', 'has',
                                'him', 'his', 'how', 'its', 'may', 'new',
                                'now', 'old', 'see', 'two', 'who', 'boy',
                                'did', 'she', 'use', 'way', 'what', 'why'}):
                    words.append(word)
            
            # 빈도 기반 상위 단어 반환
            word_counts = Counter(words)
            return [word for word, _ in word_counts.most_common(max_words)]
            
        except Exception as e:
            logger.error(f"핵심 단어 추출 실패: {e}")
            return []
    
    def analyze_document_semantics(self, document: Document) -> SemanticAnalysis:
        """문서 의미 분석 및 주제 추출"""
        try:
            # BGE-M3 임베딩 생성
            embedding = self.embedding_engine.encode_text(document.content)
            
            # 핵심 개념 추출
            key_words = self._extract_key_words(document.content, 30)
            key_concepts = {word: 1.0 for word in key_words[:10]}  # 상위 10개
            
            # 기존 태그와의 유사도 계산
            similarity_to_existing = {}
            if hasattr(self, 'tag_frequencies'):
                for tag in self.tag_frequencies.keys():
                    # 태그와 연관된 개념어들과의 매칭 점수
                    tag_concepts = self.tag_concepts.get(tag, [])
                    if tag_concepts:
                        common_concepts = set(key_words) & set(tag_concepts)
                        similarity = len(common_concepts) / len(set(tag_concepts))
                        if similarity > 0:
                            similarity_to_existing[tag] = similarity
            
            # 주제 분포 (간단한 키워드 기반)
            topic_distribution = {}
            topic_keywords = {
                'architecture': ['architecture', 'design', 'pattern', 'structure'],
                'development': ['development', 'coding', 'programming', 'implementation'],
                'testing': ['test', 'testing', 'tdd', 'unit', 'integration'],
                'framework': ['spring', 'react', 'vue', 'angular', 'framework'],
                'database': ['database', 'sql', 'query', 'data', 'storage']
            }
            
            content_lower = document.content.lower()
            for topic, keywords in topic_keywords.items():
                score = sum(1 for kw in keywords if kw in content_lower)
                if score > 0:
                    topic_distribution[topic] = score / len(keywords)
            
            return SemanticAnalysis(
                key_concepts=key_concepts,
                topic_distribution=topic_distribution,
                semantic_embedding=embedding,
                similarity_to_existing=similarity_to_existing
            )
            
        except Exception as e:
            logger.error(f"문서 의미 분석 실패: {e}")
            return SemanticAnalysis(
                key_concepts={},
                topic_distribution={},
                semantic_embedding=np.zeros(1024),
                similarity_to_existing={}
            )
    
    def generate_semantic_tags(self, document: Document, analysis: SemanticAnalysis) -> List[str]:
        """BGE-M3 분석을 바탕으로 의미적 태그 생성"""
        try:
            candidate_tags = []
            confidence_scores = {}
            
            # 1. 기존 태그와의 유사도 기반 태그 추천
            for tag, similarity in analysis.similarity_to_existing.items():
                if similarity >= self.tagging_config.get('min_semantic_similarity', 0.3):
                    candidate_tags.append(tag)
                    confidence_scores[tag] = similarity
            
            # 2. 주제 분포 기반 태그 생성
            for topic, score in analysis.topic_distribution.items():
                if score > 0.3:  # 임계값 이상의 주제만
                    base_tag = f"{topic}/general"
                    candidate_tags.append(base_tag)
                    confidence_scores[base_tag] = score
            
            # 3. 핵심 개념 기반 태그 생성
            for concept, weight in analysis.key_concepts.items():
                # 개념어가 알려진 태그와 연관되어 있다면
                related_tags = self.concept_tags.get(concept, [])
                for tag in related_tags[:2]:  # 상위 2개만
                    if tag not in candidate_tags:
                        candidate_tags.append(tag)
                        confidence_scores[tag] = weight * 0.8
            
            # 4. 패턴 기반 태그 생성 (파일명, 헤더 분석)
            pattern_tags = self._generate_pattern_tags(document)
            for tag in pattern_tags:
                if tag not in candidate_tags:
                    candidate_tags.append(tag)
                    confidence_scores[tag] = 0.7
            
            # 5. 태그 정규화 및 검증
            validated_tags = []
            for tag in candidate_tags:
                normalized_tag = self.tag_rule_engine.normalize_tag(tag)
                if (self.tag_rule_engine.validate_tag(normalized_tag) and
                    normalized_tag not in validated_tags):
                    validated_tags.append(normalized_tag)
            
            # 6. 카테고리별 제한 적용
            categorized_tags = self.tag_rule_engine.categorize_tags(validated_tags)
            final_tags = self.tag_rule_engine.limit_tag_count(
                validated_tags, 
                self.tagging_config.get('max_tags_per_document', 10)
            )
            
            return final_tags
            
        except Exception as e:
            logger.error(f"의미적 태그 생성 실패: {e}")
            return []
    
    def _generate_pattern_tags(self, document: Document) -> List[str]:
        """패턴 기반 태그 생성 (파일명, 헤더 등)"""
        pattern_tags = []
        
        try:
            # 파일명에서 태그 추출
            file_stem = Path(document.path).stem.lower()
            if 'spring' in file_stem:
                pattern_tags.append('frameworks/spring-boot')
            if 'tdd' in file_stem or 'test' in file_stem:
                pattern_tags.append('testing/tdd')
            if 'clean' in file_stem and 'code' in file_stem:
                pattern_tags.append('practices/clean-code')
            
            # 헤더에서 주요 개념 추출
            headers = re.findall(r'^#+\s+(.+)$', document.content, re.MULTILINE)
            header_text = ' '.join(headers).lower()
            
            if 'architecture' in header_text:
                pattern_tags.append('architecture/design')
            if 'refactor' in header_text:
                pattern_tags.append('practices/refactoring')
            if 'pattern' in header_text:
                pattern_tags.append('patterns/design-patterns')
            
        except Exception as e:
            logger.error(f"패턴 태그 생성 실패: {e}")
        
        return pattern_tags
    
    def tag_document(self, file_path: str, dry_run: bool = False) -> TaggingResult:
        """단일 문서 태깅"""
        start_time = datetime.now()
        
        try:
            # 문서 로드
            document = self.vault_processor.process_file(Path(file_path))
            if not document:
                return TaggingResult(
                    file_path=file_path,
                    original_tags=[],
                    generated_tags=[],
                    confidence_scores={},
                    categorized_tags={},
                    processing_time=0.0,
                    success=False,
                    error_message="문서 로드 실패"
                )
            
            # 기존 태그 보존 (무시하지 않는 경우)
            original_tags = document.tags.copy() if document.tags else []
            
            # 의미 분석
            analysis = self.analyze_document_semantics(document)
            
            # 태그 생성
            generated_tags = self.generate_semantic_tags(document, analysis)
            
            # 카테고리별 분류
            categorized_tags = self.tag_rule_engine.categorize_tags(generated_tags)
            
            # 신뢰도 점수 계산
            confidence_scores = {}
            for tag in generated_tags:
                # 기존 태그 유사도 + 개념 매칭 점수
                similarity_score = analysis.similarity_to_existing.get(tag, 0.0)
                concept_score = sum(
                    0.1 for concept in analysis.key_concepts.keys()
                    if concept in self.tag_concepts.get(tag, [])
                )
                confidence_scores[tag] = min(similarity_score + concept_score, 1.0)
            
            # 실제 태깅 적용 (dry_run이 아닌 경우)
            if not dry_run and self.tagging_config.get('ignore_existing_tags', True):
                self._apply_tags_to_file(file_path, generated_tags)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return TaggingResult(
                file_path=file_path,
                original_tags=original_tags,
                generated_tags=generated_tags,
                confidence_scores=confidence_scores,
                categorized_tags=categorized_tags,
                processing_time=processing_time,
                success=True
            )
            
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"문서 태깅 실패 {file_path}: {e}")
            
            return TaggingResult(
                file_path=file_path,
                original_tags=[],
                generated_tags=[],
                confidence_scores={},
                categorized_tags={},
                processing_time=processing_time,
                success=False,
                error_message=str(e)
            )
    
    def _apply_tags_to_file(self, file_path: str, tags: List[str]) -> bool:
        """파일에 태그 적용 (YAML frontmatter 업데이트)"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # YAML frontmatter 처리
            if content.startswith('---\n'):
                # 기존 frontmatter 찾기
                end_marker = content.find('\n---\n', 4)
                if end_marker != -1:
                    # 기존 frontmatter 업데이트
                    frontmatter = content[4:end_marker]
                    remaining_content = content[end_marker + 5:]
                else:
                    frontmatter = ""
                    remaining_content = content[4:]
            else:
                # 새 frontmatter 생성
                frontmatter = ""
                remaining_content = content
            
            # 태그 section 재작성
            frontmatter_lines = frontmatter.split('\n') if frontmatter else []
            new_frontmatter = []
            
            # 기존 태그 라인 제거
            in_tags_section = False
            for line in frontmatter_lines:
                if line.strip().startswith('tags:'):
                    in_tags_section = True
                    continue
                elif in_tags_section and line.startswith('  - '):
                    continue
                elif in_tags_section and not line.startswith(' '):
                    in_tags_section = False
                    new_frontmatter.append(line)
                else:
                    new_frontmatter.append(line)
            
            # 새 태그 추가
            new_frontmatter.append('tags:')
            for tag in tags:
                new_frontmatter.append(f'  - {tag}')
            
            # 최종 내용 구성
            new_content = '---\n' + '\n'.join(new_frontmatter) + '\n---\n' + remaining_content
            
            # 파일 저장
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            return True
            
        except Exception as e:
            logger.error(f"태그 적용 실패 {file_path}: {e}")
            return False
    
    def tag_folder(self, folder_path: str, recursive: bool = True, dry_run: bool = False) -> List[TaggingResult]:
        """폴더별 배치 태깅"""
        try:
            results = []
            folder_path = Path(folder_path)
            
            # 마크다운 파일 수집
            if recursive:
                md_files = list(folder_path.rglob('*.md'))
            else:
                md_files = list(folder_path.glob('*.md'))
            
            total_files = len(md_files)
            logger.info(f"폴더 태깅 시작: {total_files}개 파일")
            
            # 배치 처리
            batch_size = self.tagging_config.get('default_batch_size', 10)
            
            for i in range(0, total_files, batch_size):
                batch_files = md_files[i:i + batch_size]
                
                for j, file_path in enumerate(batch_files):
                    current_file = i + j + 1
                    
                    if self.tagging_config.get('show_progress', True):
                        print(f"진행: {current_file}/{total_files} - {file_path.name}")
                    
                    result = self.tag_document(str(file_path), dry_run=dry_run)
                    results.append(result)
            
            successful = sum(1 for r in results if r.success)
            logger.info(f"폴더 태깅 완료: {successful}/{total_files} 성공")
            
            return results
            
        except Exception as e:
            logger.error(f"폴더 태깅 실패: {e}")
            return []


def test_semantic_tagger():
    """의미적 태깅 시스템 테스트"""
    import tempfile
    import yaml
    
    try:
        # 테스트 설정
        config = {
            'semantic_tagging': {
                'model_name': 'BAAI/bge-m3',
                'device': 'mps',
                'batch_size': 2,
                'max_length': 1024,
                'max_tags_per_document': 5,
                'learn_from_existing': False,
                'ignore_existing_tags': True
            },
            'model': {
                'name': 'BAAI/bge-m3',
                'device': 'mps',
                'batch_size': 2,
                'cache_folder': 'models/',
                'use_fp16': False,
                'max_length': 1024,
                'num_workers': 2
            },
            'vault': {
                'excluded_dirs': ['.obsidian'],
                'file_extensions': ['.md']
            }
        }
        
        # 임시 vault 생성
        with tempfile.TemporaryDirectory() as temp_dir:
            # 테스트 문서 생성
            test_doc = """---
tags:
  - old-tag
---

# Spring Boot with TDD

This document explains how to implement Test-Driven Development in Spring Boot applications.

## Key Concepts

- Unit Testing
- Integration Testing
- Mocking
- Clean Code

## Implementation

Spring Boot provides excellent support for testing with annotations like @Test and @MockBean.
"""
            
            test_file = Path(temp_dir) / "spring-tdd.md"
            test_file.write_text(test_doc, encoding='utf-8')
            
            # 태깅 시스템 테스트
            tagger = SemanticTagger(temp_dir, config)
            
            # 단일 파일 태깅 테스트
            result = tagger.tag_document(str(test_file), dry_run=True)
            
            print(f"태깅 테스트 결과:")
            print(f"  파일: {result.file_path}")
            print(f"  성공: {result.success}")
            print(f"  기존 태그: {result.original_tags}")
            print(f"  생성 태그: {result.generated_tags}")
            print(f"  카테고리별: {result.categorized_tags}")
            print(f"  처리 시간: {result.processing_time:.2f}초")
            
            if result.error_message:
                print(f"  오류: {result.error_message}")
        
        print("✅ 의미적 태깅 시스템 테스트 완료!")
        return True
        
    except Exception as e:
        print(f"❌ 의미적 태깅 시스템 테스트 실패: {e}")
        return False


if __name__ == "__main__":
    test_semantic_tagger()