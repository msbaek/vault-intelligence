#!/usr/bin/env python3
"""
태그 규칙 엔진

~/dotfiles/.claude/commands/obsidian/add-tag.md의 태깅 규칙을 
파싱하고 적용하는 엔진
"""

import os
import re
import logging
from typing import Dict, List, Set, Optional, Tuple
from pathlib import Path
from collections import defaultdict, Counter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TagRuleEngine:
    """add-tag.md 규칙 엔진"""
    
    def __init__(self, config: Dict, rules_path: Optional[str] = None):
        """
        Args:
            config: 태깅 설정 딕셔너리
            rules_path: 규칙 파일 경로 (기본값: ~/dotfiles/.claude/commands/obsidian/add-tag.md)
        """
        self.config = config
        self.rules_path = rules_path or config.get('rules_file', 
            "~/dotfiles/.claude/commands/obsidian/add-tag.md")
        
        # 규칙 로딩
        self.rules = self._load_tagging_rules()
        self.category_mapping = self._load_category_mapping()
        self.validation_rules = self._load_validation_rules()
        
        logger.info(f"태그 규칙 엔진 초기화 완료: {self.rules_path}")
    
    def _load_tagging_rules(self) -> Dict:
        """add-tag.md 파일에서 태깅 규칙 로딩"""
        try:
            rules_path = Path(self.rules_path).expanduser()
            
            if not rules_path.exists():
                logger.warning(f"규칙 파일을 찾을 수 없음: {rules_path}")
                return self._get_default_rules()
            
            with open(rules_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            rules = {}
            
            # 계층 구분자 추출
            if "계층 구분은 '/' 사용" in content:
                rules['hierarchical_separator'] = '/'
            
            # 태그명 규칙
            if "tag 명은 소문자 사용" in content:
                rules['force_lowercase'] = True
            
            # 공백 처리
            if "공백은 허용되지 않음 (대신 '-' 사용)" in content:
                rules['replace_spaces_with_hyphens'] = True
            
            # 태그 개수 제한
            max_tags_match = re.search(r'태그의 갯수는 최대 (\d+)개로 제한', content)
            if max_tags_match:
                rules['max_tags'] = int(max_tags_match.group(1))
            
            # 확장된 개수 (8-12개)
            if "8-12개로 확장" in content:
                rules['max_tags'] = 12
            
            # 금지 패턴
            if "디렉토리 기반 태그(resources/, slipbox/) 사용 금지" in content:
                rules['exclude_directory_tags'] = True
                rules['forbidden_prefixes'] = ['resources/', 'slipbox/']
            
            # development/ prefix 제거
            if "development/ prefix 제거" in content:
                rules['remove_development_prefix'] = True
            
            # 카테고리 추출
            categories = self._extract_categories_from_content(content)
            if categories:
                rules['categories'] = categories
            
            logger.info(f"규칙 로딩 완료: {len(rules)}개 규칙")
            return rules
            
        except Exception as e:
            logger.error(f"규칙 파일 로딩 실패: {e}")
            return self._get_default_rules()
    
    def _extract_categories_from_content(self, content: str) -> Dict[str, List[str]]:
        """규칙 파일에서 카테고리 정보 추출"""
        categories = {
            'Topic': [],
            'Document Type': [],
            'Source': [],
            'Patterns': [],
            'Frameworks': []
        }
        
        # 예시 태그에서 카테고리 패턴 추출
        examples = re.findall(r'- `([^`]+)`', content)
        
        for example in examples:
            if '/' in example:
                parts = example.split('/')
                main_category = parts[0]
                
                # 알려진 패턴에 따라 분류
                if main_category in ['git', 'architecture', 'tdd', 'refactoring', 'oop', 'ddd']:
                    categories['Topic'].append(example)
                elif main_category in ['guide', 'tutorial', 'reference']:
                    categories['Document Type'].append(example)
                elif main_category in ['book', 'article', 'video', 'conference']:
                    categories['Source'].append(example)
                elif main_category in ['patterns', 'singleton', 'factory']:
                    categories['Patterns'].append(example)
                elif main_category in ['frameworks', 'spring', 'react', 'vue']:
                    categories['Frameworks'].append(example)
        
        return categories
    
    def _get_default_rules(self) -> Dict:
        """기본 규칙 반환"""
        return {
            'hierarchical_separator': '/',
            'force_lowercase': True,
            'replace_spaces_with_hyphens': True,
            'max_tags': 10,
            'exclude_directory_tags': True,
            'remove_development_prefix': True,
            'forbidden_prefixes': ['resources/', 'slipbox/', 'development/'],
            'categories': {
                'Topic': ['architecture', 'tdd', 'refactoring', 'oop', 'ddd'],
                'Document Type': ['guide', 'tutorial', 'reference'],
                'Source': ['book', 'article', 'video'],
                'Patterns': ['patterns'],
                'Frameworks': ['frameworks']
            }
        }
    
    def _load_category_mapping(self) -> Dict[str, str]:
        """카테고리 매핑 로딩"""
        return {
            # Topic 카테고리
            'architecture': 'Topic',
            'design': 'Topic',
            'tdd': 'Topic',
            'testing': 'Topic',
            'refactoring': 'Topic',
            'clean-code': 'Topic',
            'oop': 'Topic',
            'ddd': 'Topic',
            'microservices': 'Topic',
            'api': 'Topic',
            'database': 'Topic',
            'security': 'Topic',
            'performance': 'Topic',
            
            # Document Type 카테고리
            'guide': 'Document Type',
            'tutorial': 'Document Type',
            'reference': 'Document Type',
            'examples': 'Document Type',
            'notes': 'Document Type',
            'summary': 'Document Type',
            
            # Source 카테고리
            'book': 'Source',
            'article': 'Source',
            'video': 'Source',
            'conference': 'Source',
            'blog': 'Source',
            'documentation': 'Source',
            
            # Patterns 카테고리
            'patterns': 'Patterns',
            'singleton': 'Patterns',
            'factory': 'Patterns',
            'observer': 'Patterns',
            'strategy': 'Patterns',
            'template': 'Patterns',
            
            # Frameworks 카테고리
            'frameworks': 'Frameworks',
            'spring': 'Frameworks',
            'spring-boot': 'Frameworks',
            'react': 'Frameworks',
            'vue': 'Frameworks',
            'angular': 'Frameworks',
            'django': 'Frameworks',
            'fastapi': 'Frameworks'
        }
    
    def _load_validation_rules(self) -> Dict:
        """검증 규칙 로딩"""
        return {
            'min_length': 2,
            'max_length': 50,
            'allowed_chars': re.compile(r'^[a-z0-9\-/]+$'),
            'max_hierarchy_depth': 4,
            'forbidden_words': {'test', 'temp', 'tmp', 'example'},
            'required_separator': '/'
        }
    
    def validate_tag(self, tag: str) -> bool:
        """태그 규칙 검증"""
        try:
            if not tag or not isinstance(tag, str):
                return False
            
            # 길이 검증
            if (len(tag) < self.validation_rules['min_length'] or 
                len(tag) > self.validation_rules['max_length']):
                return False
            
            # 문자 패턴 검증
            if not self.validation_rules['allowed_chars'].match(tag):
                return False
            
            # 계층 깊이 검증
            depth = tag.count(self.rules['hierarchical_separator'])
            if depth > self.validation_rules['max_hierarchy_depth']:
                return False
            
            # 금지된 접두사 검증
            forbidden_prefixes = self.rules.get('forbidden_prefixes', [])
            for prefix in forbidden_prefixes:
                if tag.startswith(prefix):
                    return False
            
            # 금지된 단어 검증
            tag_words = set(tag.replace('/', '-').split('-'))
            forbidden_words = self.validation_rules.get('forbidden_words', set())
            if tag_words & forbidden_words:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"태그 검증 실패: {tag}, {e}")
            return False
    
    def normalize_tag(self, tag: str) -> str:
        """태그 정규화 (소문자, 하이픈 등)"""
        try:
            if not tag:
                return ""
            
            # 기본 정제
            normalized = tag.strip()
            
            # 소문자 변환
            if self.rules.get('force_lowercase', True):
                normalized = normalized.lower()
            
            # 공백을 하이픈으로 변환
            if self.rules.get('replace_spaces_with_hyphens', True):
                normalized = re.sub(r'\s+', '-', normalized)
            
            # development/ prefix 제거
            if self.rules.get('remove_development_prefix', True):
                if normalized.startswith('development/'):
                    normalized = normalized[12:]  # 'development/' 길이
            
            # 특수 문자 정제
            normalized = re.sub(r'[^\w\-/]', '', normalized)
            
            # 연속된 하이픈 정리
            normalized = re.sub(r'-+', '-', normalized)
            
            # 시작/끝 하이픈 제거
            normalized = normalized.strip('-')
            
            # 빈 계층 제거 (예: architecture//patterns -> architecture/patterns)
            separator = self.rules.get('hierarchical_separator', '/')
            normalized = re.sub(f'{separator}+', separator, normalized)
            
            return normalized
            
        except Exception as e:
            logger.error(f"태그 정규화 실패: {tag}, {e}")
            return tag
    
    def categorize_tags(self, tags: List[str]) -> Dict[str, List[str]]:
        """5가지 카테고리별 태그 분류"""
        try:
            categorized = {
                'Topic': [],
                'Document Type': [],
                'Source': [],
                'Patterns': [],
                'Frameworks': []
            }
            
            for tag in tags:
                # 계층의 첫 번째 레벨로 카테고리 판단
                if '/' in tag:
                    root_category = tag.split('/')[0]
                else:
                    root_category = tag
                
                # 매핑에서 카테고리 찾기
                category = self.category_mapping.get(root_category, 'Topic')  # 기본값은 Topic
                
                # 명시적 패턴 매칭
                if any(pattern in tag for pattern in ['pattern', 'singleton', 'factory', 'observer']):
                    category = 'Patterns'
                elif any(framework in tag for framework in ['spring', 'react', 'vue', 'framework']):
                    category = 'Frameworks'
                elif any(doctype in tag for doctype in ['guide', 'tutorial', 'reference', 'example']):
                    category = 'Document Type'
                elif any(source in tag for source in ['book', 'article', 'video', 'conference']):
                    category = 'Source'
                
                if category in categorized:
                    categorized[category].append(tag)
                else:
                    categorized['Topic'].append(tag)  # 기본 카테고리
            
            return categorized
            
        except Exception as e:
            logger.error(f"태그 분류 실패: {e}")
            return {category: [] for category in ['Topic', 'Document Type', 'Source', 'Patterns', 'Frameworks']}
    
    def apply_hierarchical_structure(self, semantic_concepts: List[str]) -> List[str]:
        """의미적 개념을 계층적 태그로 변환"""
        try:
            hierarchical_tags = []
            
            # 개념별 계층 구조 매핑
            concept_hierarchies = {
                'spring': 'frameworks/spring-boot',
                'test': 'testing/unit',
                'tdd': 'testing/tdd',
                'architecture': 'architecture/design',
                'pattern': 'patterns/design-patterns',
                'refactor': 'practices/refactoring',
                'clean': 'practices/clean-code',
                'database': 'data/database',
                'api': 'architecture/api',
                'microservice': 'architecture/microservices',
                'security': 'security/general',
                'performance': 'performance/optimization'
            }
            
            for concept in semantic_concepts:
                concept_lower = concept.lower()
                
                # 직접 매핑이 있는 경우
                if concept_lower in concept_hierarchies:
                    hierarchical_tags.append(concept_hierarchies[concept_lower])
                    continue
                
                # 부분 매칭으로 계층 구조 생성
                matched = False
                for key, hierarchy in concept_hierarchies.items():
                    if key in concept_lower:
                        hierarchical_tags.append(hierarchy)
                        matched = True
                        break
                
                # 매칭되지 않으면 기본 구조 적용
                if not matched:
                    # 단순한 개념은 topic 하위로
                    normalized_concept = self.normalize_tag(concept)
                    if self.validate_tag(normalized_concept):
                        hierarchical_tags.append(f"topic/{normalized_concept}")
            
            return hierarchical_tags
            
        except Exception as e:
            logger.error(f"계층 구조 적용 실패: {e}")
            return semantic_concepts
    
    def limit_tag_count(self, tags: List[str], max_count: int = 10) -> List[str]:
        """태그 개수 제한 (중요도 기반 선별)"""
        try:
            if len(tags) <= max_count:
                return tags
            
            # 카테고리별 제한 적용
            categorized = self.categorize_tags(tags)
            limited_tags = []
            
            # 카테고리별 최대 개수 설정
            category_limits = {
                'Topic': self.config.get('max_topic_tags', 4),
                'Document Type': self.config.get('max_doctype_tags', 1),
                'Source': self.config.get('max_source_tags', 1),
                'Patterns': self.config.get('max_pattern_tags', 3),
                'Frameworks': self.config.get('max_framework_tags', 2)
            }
            
            # 카테고리별로 제한 적용
            for category, category_tags in categorized.items():
                limit = category_limits.get(category, 2)
                
                if len(category_tags) <= limit:
                    limited_tags.extend(category_tags)
                else:
                    # 중요도 기반 선별 (더 구체적인 태그 우선)
                    sorted_tags = sorted(
                        category_tags, 
                        key=lambda x: (x.count('/'), len(x)), 
                        reverse=True
                    )
                    limited_tags.extend(sorted_tags[:limit])
            
            # 전체 제한 재적용
            if len(limited_tags) > max_count:
                # 최종 우선순위: 계층 깊이 > 카테고리 중요도
                priority_order = ['Document Type', 'Topic', 'Frameworks', 'Patterns', 'Source']
                final_tags = []
                
                for category in priority_order:
                    category_tags = [tag for tag in limited_tags 
                                   if tag in categorized.get(category, [])]
                    for tag in category_tags:
                        if len(final_tags) < max_count:
                            final_tags.append(tag)
                
                return final_tags
            
            return limited_tags
            
        except Exception as e:
            logger.error(f"태그 개수 제한 실패: {e}")
            return tags[:max_count]  # 안전장치
    
    def get_tag_suggestions(self, partial_tag: str, existing_tags: List[str]) -> List[str]:
        """부분 태그에 대한 제안 생성"""
        try:
            suggestions = []
            
            # 기존 태그에서 유사한 패턴 찾기
            for tag in existing_tags:
                if partial_tag.lower() in tag.lower():
                    suggestions.append(tag)
            
            # 알려진 계층 구조에서 제안
            known_hierarchies = [
                'architecture/design/patterns',
                'testing/tdd/practices',
                'frameworks/spring-boot/configuration',
                'practices/clean-code/refactoring',
                'patterns/design-patterns/singleton',
                'security/authentication/oauth2',
                'performance/optimization/caching'
            ]
            
            for hierarchy in known_hierarchies:
                if partial_tag.lower() in hierarchy.lower():
                    suggestions.append(hierarchy)
            
            # 중복 제거 및 정렬
            suggestions = list(set(suggestions))
            suggestions.sort(key=len)  # 짧은 것부터
            
            return suggestions[:10]  # 최대 10개
            
        except Exception as e:
            logger.error(f"태그 제안 생성 실패: {e}")
            return []
    
    def analyze_tag_consistency(self, all_tags: List[str]) -> Dict:
        """태그 일관성 분석"""
        try:
            analysis = {
                'total_tags': len(set(all_tags)),
                'tag_frequency': Counter(all_tags),
                'hierarchy_analysis': {},
                'inconsistencies': [],
                'suggestions': []
            }
            
            # 계층 분석
            hierarchy_counter = defaultdict(int)
            for tag in set(all_tags):
                if '/' in tag:
                    parts = tag.split('/')
                    for i in range(len(parts)):
                        hierarchy = '/'.join(parts[:i+1])
                        hierarchy_counter[hierarchy] += 1
            
            analysis['hierarchy_analysis'] = dict(hierarchy_counter)
            
            # 불일치 감지
            unique_tags = set(all_tags)
            for tag in unique_tags:
                # 유사한 태그 찾기 (오타 가능성)
                similar_tags = [
                    other_tag for other_tag in unique_tags 
                    if other_tag != tag and self._calculate_similarity(tag, other_tag) > 0.8
                ]
                
                if similar_tags:
                    analysis['inconsistencies'].append({
                        'tag': tag,
                        'similar': similar_tags,
                        'suggestion': 'consolidate'
                    })
            
            # 개선 제안
            # 1. 자주 사용되는 단일 레벨 태그를 계층화
            for tag, count in analysis['tag_frequency'].items():
                if count > 5 and '/' not in tag:
                    hierarchical_suggestion = self.apply_hierarchical_structure([tag])
                    if hierarchical_suggestion and hierarchical_suggestion[0] != tag:
                        analysis['suggestions'].append({
                            'type': 'hierarchical',
                            'original': tag,
                            'suggested': hierarchical_suggestion[0],
                            'frequency': count
                        })
            
            return analysis
            
        except Exception as e:
            logger.error(f"태그 일관성 분석 실패: {e}")
            return {}
    
    def _calculate_similarity(self, tag1: str, tag2: str) -> float:
        """두 태그 간 유사도 계산 (간단한 편집 거리 기반)"""
        try:
            len1, len2 = len(tag1), len(tag2)
            if len1 == 0 or len2 == 0:
                return 0.0
            
            # 간단한 Levenshtein 거리 계산
            matrix = [[0] * (len2 + 1) for _ in range(len1 + 1)]
            
            for i in range(len1 + 1):
                matrix[i][0] = i
            for j in range(len2 + 1):
                matrix[0][j] = j
            
            for i in range(1, len1 + 1):
                for j in range(1, len2 + 1):
                    if tag1[i-1] == tag2[j-1]:
                        cost = 0
                    else:
                        cost = 1
                    
                    matrix[i][j] = min(
                        matrix[i-1][j] + 1,      # 삭제
                        matrix[i][j-1] + 1,      # 삽입
                        matrix[i-1][j-1] + cost  # 교체
                    )
            
            distance = matrix[len1][len2]
            max_len = max(len1, len2)
            
            return 1.0 - (distance / max_len)
            
        except Exception:
            return 0.0


def test_tag_rule_engine():
    """태그 규칙 엔진 테스트"""
    try:
        # 테스트 설정
        config = {
            'max_topic_tags': 4,
            'max_pattern_tags': 3,
            'max_framework_tags': 2,
            'max_source_tags': 1,
            'max_doctype_tags': 1
        }
        
        engine = TagRuleEngine(config)
        
        # 태그 정규화 테스트
        test_tags = [
            "Development/Spring Boot",
            "architecture/Microservices",
            "Testing TDD",
            "Clean Code",
            "resources/books",
            "slipbox/notes"
        ]
        
        print("태그 정규화 테스트:")
        for tag in test_tags:
            normalized = engine.normalize_tag(tag)
            valid = engine.validate_tag(normalized)
            print(f"  {tag} -> {normalized} (valid: {valid})")
        
        # 카테고리 분류 테스트
        sample_tags = [
            "architecture/microservices",
            "testing/tdd",
            "frameworks/spring-boot",
            "patterns/singleton",
            "guide/tutorial",
            "book/clean-code"
        ]
        
        categorized = engine.categorize_tags(sample_tags)
        print(f"\n카테고리 분류 테스트:")
        for category, tags in categorized.items():
            if tags:
                print(f"  {category}: {tags}")
        
        # 태그 제한 테스트
        many_tags = sample_tags * 3  # 18개 태그
        limited = engine.limit_tag_count(many_tags, max_count=8)
        print(f"\n태그 제한 테스트:")
        print(f"  원본: {len(many_tags)}개 -> 제한: {len(limited)}개")
        print(f"  결과: {limited}")
        
        print("✅ 태그 규칙 엔진 테스트 완료!")
        return True
        
    except Exception as e:
        print(f"❌ 태그 규칙 엔진 테스트 실패: {e}")
        return False


if __name__ == "__main__":
    test_tag_rule_engine()