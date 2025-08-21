#!/usr/bin/env python3
"""
Topic Collector for Vault Intelligence System V2

주제별 문서 수집 및 통합 문서 생성 (기존 collect 기능)
"""

import os
import logging
from typing import List, Dict, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass, asdict
from datetime import datetime
from collections import defaultdict, Counter

from ..core.vault_processor import Document
from ..features.advanced_search import SearchResult

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class CollectionMetadata:
    """수집 메타데이터"""
    topic: str
    total_documents: int
    total_word_count: int
    total_size_bytes: int
    collection_date: datetime
    search_query: str
    similarity_threshold: float
    tag_distribution: Dict[str, int]
    directory_distribution: Dict[str, int]


@dataclass
class DocumentCollection:
    """문서 컬렉션"""
    metadata: CollectionMetadata
    documents: List[Document]
    grouped_documents: Dict[str, List[Document]]
    statistics: Dict[str, any]


class TopicCollector:
    """주제별 문서 수집기"""
    
    def __init__(
        self,
        search_engine,
        config: Dict = None
    ):
        """
        Args:
            search_engine: AdvancedSearchEngine 인스턴스
            config: 수집 설정
        """
        self.search_engine = search_engine
        self.config = config or {}
        
        # 기본 설정
        self.min_documents = self.config.get('collection', {}).get('min_documents', 3)
        self.group_by_tags = self.config.get('collection', {}).get('group_by_tags', True)
        self.include_statistics = self.config.get('collection', {}).get('include_statistics', True)
        self.output_format = self.config.get('collection', {}).get('output_format', 'markdown')
        
        logger.info(f"주제 수집기 초기화")
    
    def collect_topic(
        self,
        topic: str,
        top_k: int = 100,
        threshold: float = 0.3,
        min_word_count: Optional[int] = None,
        tags_filter: Optional[List[str]] = None,
        output_file: Optional[str] = None,
        use_expansion: bool = False,
        include_synonyms: bool = True,
        include_hyde: bool = True
    ) -> DocumentCollection:
        """주제별 문서 수집"""
        try:
            if not self.search_engine.indexed:
                logger.warning("검색 엔진이 인덱싱되지 않았습니다.")
                return self._create_empty_collection(topic)
            
            logger.info(f"주제 '{topic}' 문서 수집 시작...")
            if use_expansion:
                expand_features = []
                if include_synonyms:
                    expand_features.append("동의어")
                if include_hyde:
                    expand_features.append("HyDE")
                logger.info(f"📝 쿼리 확장 모드 활성화: {', '.join(expand_features)}")
            
            # 확장된 하이브리드 검색 수행 (의미적 + 키워드 + 선택적 확장)
            if use_expansion:
                search_results = self.search_engine.expanded_search(
                    query=topic,
                    search_method="hybrid",
                    top_k=top_k,
                    threshold=threshold,
                    include_synonyms=include_synonyms,
                    include_hyde=include_hyde
                )
            else:
                search_results = self.search_engine.hybrid_search(
                    topic,
                    top_k=top_k,
                    threshold=threshold
                )
            
            if not search_results:
                logger.warning(f"주제 '{topic}'에 대한 문서를 찾을 수 없습니다.")
                return self._create_empty_collection(topic)
            
            # 문서 추출
            documents = [result.document for result in search_results]
            
            # 추가 필터링
            filtered_documents = self._apply_filters(
                documents, min_word_count, tags_filter
            )
            
            if len(filtered_documents) < self.min_documents:
                logger.warning(f"필터링 후 문서가 너무 적습니다: {len(filtered_documents)}")
            
            logger.info(f"수집된 문서: {len(filtered_documents)}개")
            
            # 메타데이터 생성
            metadata = self._create_metadata(
                topic, filtered_documents, topic, threshold
            )
            
            # 문서 그룹화
            grouped_documents = self._group_documents(filtered_documents)
            
            # 통계 생성
            statistics = self._generate_statistics(filtered_documents)
            
            # 컬렉션 생성
            collection = DocumentCollection(
                metadata=metadata,
                documents=filtered_documents,
                grouped_documents=grouped_documents,
                statistics=statistics
            )
            
            # 출력 파일 생성
            if output_file:
                self.export_collection(collection, output_file)
            
            logger.info(f"주제 수집 완료: {len(filtered_documents)}개 문서")
            return collection
            
        except Exception as e:
            logger.error(f"주제 수집 실패: {e}")
            return self._create_empty_collection(topic)
    
    def _apply_filters(
        self,
        documents: List[Document],
        min_word_count: Optional[int],
        tags_filter: Optional[List[str]]
    ) -> List[Document]:
        """문서 필터링"""
        filtered = documents
        
        # 최소 단어 수 필터
        if min_word_count:
            filtered = [doc for doc in filtered if doc.word_count >= min_word_count]
            logger.info(f"최소 단어 수 필터 적용 후: {len(filtered)}개")
        
        # 태그 필터
        if tags_filter:
            tag_set = set(tag.lower() for tag in tags_filter)
            filtered = [
                doc for doc in filtered
                if any(tag.lower() in tag_set for tag in doc.tags)
            ]
            logger.info(f"태그 필터 적용 후: {len(filtered)}개")
        
        return filtered
    
    def _create_metadata(
        self,
        topic: str,
        documents: List[Document],
        search_query: str,
        threshold: float
    ) -> CollectionMetadata:
        """컬렉션 메타데이터 생성"""
        try:
            # 기본 통계
            total_documents = len(documents)
            total_word_count = sum(doc.word_count for doc in documents)
            total_size_bytes = sum(doc.file_size for doc in documents)
            
            # 태그 분포
            tag_counter = Counter()
            for doc in documents:
                if doc.tags:
                    tag_counter.update(doc.tags)
            tag_distribution = dict(tag_counter.most_common(20))
            
            # 디렉토리 분포
            dir_counter = Counter()
            for doc in documents:
                dir_path = str(Path(doc.path).parent)
                if dir_path == '.':
                    dir_path = 'root'
                dir_counter[dir_path] += 1
            directory_distribution = dict(dir_counter.most_common(10))
            
            return CollectionMetadata(
                topic=topic,
                total_documents=total_documents,
                total_word_count=total_word_count,
                total_size_bytes=total_size_bytes,
                collection_date=datetime.now(),
                search_query=search_query,
                similarity_threshold=threshold,
                tag_distribution=tag_distribution,
                directory_distribution=directory_distribution
            )
            
        except Exception as e:
            logger.error(f"메타데이터 생성 실패: {e}")
            return CollectionMetadata(
                topic=topic,
                total_documents=0,
                total_word_count=0,
                total_size_bytes=0,
                collection_date=datetime.now(),
                search_query=search_query,
                similarity_threshold=threshold,
                tag_distribution={},
                directory_distribution={}
            )
    
    def _group_documents(self, documents: List[Document]) -> Dict[str, List[Document]]:
        """문서 그룹화"""
        try:
            if not self.group_by_tags:
                return {"전체": documents}
            
            grouped = defaultdict(list)
            untagged = []
            
            for doc in documents:
                if doc.tags:
                    # 첫 번째 태그를 기준으로 그룹화
                    primary_tag = doc.tags[0]
                    
                    # 계층적 태그의 경우 최상위 카테고리 사용
                    if '/' in primary_tag:
                        primary_tag = primary_tag.split('/')[0]
                    
                    grouped[primary_tag].append(doc)
                else:
                    untagged.append(doc)
            
            # 태그 없는 문서
            if untagged:
                grouped["기타"] = untagged
            
            # 문서 수가 적은 그룹들을 "기타"로 통합
            final_grouped = {}
            misc_docs = []
            
            for tag, docs in grouped.items():
                if len(docs) >= 2 or tag == "기타":  # 최소 2개 또는 이미 기타
                    final_grouped[tag] = docs
                else:
                    misc_docs.extend(docs)
            
            if misc_docs:
                if "기타" in final_grouped:
                    final_grouped["기타"].extend(misc_docs)
                else:
                    final_grouped["기타"] = misc_docs
            
            return dict(final_grouped)
            
        except Exception as e:
            logger.error(f"문서 그룹화 실패: {e}")
            return {"전체": documents}
    
    def _generate_statistics(self, documents: List[Document]) -> Dict:
        """통계 정보 생성"""
        try:
            if not documents:
                return {}
            
            word_counts = [doc.word_count for doc in documents]
            file_sizes = [doc.file_size for doc in documents]
            
            statistics = {
                "document_count": len(documents),
                "word_count": {
                    "total": sum(word_counts),
                    "average": sum(word_counts) / len(word_counts),
                    "min": min(word_counts),
                    "max": max(word_counts)
                },
                "file_size": {
                    "total_bytes": sum(file_sizes),
                    "total_mb": sum(file_sizes) / (1024 * 1024),
                    "average_bytes": sum(file_sizes) / len(file_sizes)
                },
                "modification_dates": {
                    "newest": max(doc.modified_at for doc in documents),
                    "oldest": min(doc.modified_at for doc in documents)
                }
            }
            
            return statistics
            
        except Exception as e:
            logger.error(f"통계 생성 실패: {e}")
            return {}
    
    def _create_empty_collection(self, topic: str) -> DocumentCollection:
        """빈 컬렉션 생성"""
        metadata = CollectionMetadata(
            topic=topic,
            total_documents=0,
            total_word_count=0,
            total_size_bytes=0,
            collection_date=datetime.now(),
            search_query=topic,
            similarity_threshold=0.0,
            tag_distribution={},
            directory_distribution={}
        )
        
        return DocumentCollection(
            metadata=metadata,
            documents=[],
            grouped_documents={},
            statistics={}
        )
    
    def export_collection(
        self,
        collection: DocumentCollection,
        output_file: str,
        format_type: Optional[str] = None
    ) -> bool:
        """컬렉션을 파일로 내보내기"""
        try:
            format_type = format_type or self.output_format
            
            if format_type.lower() == "markdown":
                return self._export_as_markdown(collection, output_file)
            elif format_type.lower() == "json":
                return self._export_as_json(collection, output_file)
            else:
                logger.warning(f"지원하지 않는 형식: {format_type}, 마크다운으로 내보냅니다.")
                return self._export_as_markdown(collection, output_file)
                
        except Exception as e:
            logger.error(f"컬렉션 내보내기 실패: {e}")
            return False
    
    def _export_as_markdown(self, collection: DocumentCollection, output_file: str) -> bool:
        """마크다운 형식으로 내보내기"""
        try:
            metadata = collection.metadata
            
            # 마크다운 콘텐츠 생성
            content = f"""---
tags:
  - vault-intelligence/collection
  - topic/{metadata.topic.lower().replace(' ', '-')}
generated: {metadata.collection_date.isoformat()}
topic: {metadata.topic}
total_documents: {metadata.total_documents}
---

# {metadata.topic} 문서 컬렉션

**생성일**: {metadata.collection_date.strftime('%Y-%m-%d %H:%M:%S')}  
**수집된 문서**: {metadata.total_documents}개  
**총 단어 수**: {metadata.total_word_count:,}개  
**검색 쿼리**: "{metadata.search_query}"

## 📊 개요

이 문서는 '{metadata.topic}' 주제와 관련된 모든 문서들을 체계적으로 정리한 컬렉션입니다.

### 수집 통계
- **총 문서 수**: {metadata.total_documents}개
- **총 단어 수**: {metadata.total_word_count:,}개  
- **총 파일 크기**: {metadata.total_size_bytes / (1024*1024):.2f}MB
- **유사도 임계값**: {metadata.similarity_threshold}

"""
            
            # 태그 분포 (상위 10개)
            if metadata.tag_distribution:
                content += "\n### 🏷️ 주요 태그\n\n"
                for tag, count in list(metadata.tag_distribution.items())[:10]:
                    content += f"- **{tag}**: {count}개 문서\n"
            
            # 디렉토리 분포
            if metadata.directory_distribution:
                content += "\n### 📁 디렉토리별 분포\n\n"
                for dir_path, count in metadata.directory_distribution.items():
                    content += f"- **{dir_path}**: {count}개 문서\n"
            
            content += "\n## 📑 문서 목록\n\n"
            
            # 그룹별 문서 나열
            for group_name, docs in collection.grouped_documents.items():
                content += f"### {group_name}\n\n"
                
                # 단어 수 기준으로 정렬
                sorted_docs = sorted(docs, key=lambda d: d.word_count, reverse=True)
                
                for doc in sorted_docs:
                    content += f"- **[[{doc.path}]]**"
                    
                    if doc.word_count:
                        content += f" ({doc.word_count:,} 단어)"
                    
                    if doc.tags:
                        tags_str = ", ".join(f"#{tag}" for tag in doc.tags[:3])
                        content += f" - {tags_str}"
                    
                    content += "\n"
                
                content += "\n"
            
            # 통계 섹션
            if self.include_statistics and collection.statistics:
                stats = collection.statistics
                content += f"""## 📈 상세 통계

### 문서 통계
- **총 문서**: {stats['document_count']}개
- **평균 단어 수**: {stats['word_count']['average']:.0f}개
- **최대 단어 수**: {stats['word_count']['max']:,}개
- **최소 단어 수**: {stats['word_count']['min']:,}개

### 파일 크기
- **총 크기**: {stats['file_size']['total_mb']:.2f}MB
- **평균 크기**: {stats['file_size']['average_bytes']/1024:.1f}KB

### 수정 일자
- **가장 최신**: {stats['modification_dates']['newest'].strftime('%Y-%m-%d %H:%M')}
- **가장 오래된**: {stats['modification_dates']['oldest'].strftime('%Y-%m-%d %H:%M')}

"""
            
            content += f"""---

**컬렉션 정보**  
- 생성 시스템: Vault Intelligence System V2
- 생성 일시: {metadata.collection_date.strftime('%Y-%m-%d %H:%M:%S')}
- 검색 방식: Sentence Transformers (768차원)
- 임계값: {metadata.similarity_threshold}
"""
            
            # 파일 저장
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info(f"마크다운 컬렉션 저장 완료: {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"마크다운 내보내기 실패: {e}")
            return False
    
    def _export_as_json(self, collection: DocumentCollection, output_file: str) -> bool:
        """JSON 형식으로 내보내기"""
        try:
            import json
            
            # JSON 직렬화 가능한 형태로 변환
            export_data = {
                "metadata": {
                    "topic": collection.metadata.topic,
                    "total_documents": collection.metadata.total_documents,
                    "total_word_count": collection.metadata.total_word_count,
                    "total_size_bytes": collection.metadata.total_size_bytes,
                    "collection_date": collection.metadata.collection_date.isoformat(),
                    "search_query": collection.metadata.search_query,
                    "similarity_threshold": collection.metadata.similarity_threshold,
                    "tag_distribution": collection.metadata.tag_distribution,
                    "directory_distribution": collection.metadata.directory_distribution
                },
                "documents": [
                    {
                        "path": doc.path,
                        "title": doc.title,
                        "word_count": doc.word_count,
                        "file_size": doc.file_size,
                        "tags": doc.tags,
                        "modified_at": doc.modified_at.isoformat()
                    }
                    for doc in collection.documents
                ],
                "grouped_documents": {
                    group: [
                        {
                            "path": doc.path,
                            "title": doc.title,
                            "word_count": doc.word_count
                        }
                        for doc in docs
                    ]
                    for group, docs in collection.grouped_documents.items()
                },
                "statistics": collection.statistics
            }
            
            # 날짜 객체 처리
            if collection.statistics and 'modification_dates' in collection.statistics:
                export_data['statistics']['modification_dates'] = {
                    'newest': collection.statistics['modification_dates']['newest'].isoformat(),
                    'oldest': collection.statistics['modification_dates']['oldest'].isoformat()
                }
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"JSON 컬렉션 저장 완료: {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"JSON 내보내기 실패: {e}")
            return False
    
    def suggest_related_topics(self, topic: str, top_k: int = 5) -> List[Tuple[str, int]]:
        """관련 주제 제안"""
        try:
            # 주제 수집
            collection = self.collect_topic(topic, top_k=50, threshold=0.2)
            
            if not collection.documents:
                return []
            
            # 태그에서 관련 주제 추출
            tag_suggestions = []
            for tag, count in collection.metadata.tag_distribution.items():
                if tag.lower() != topic.lower() and count >= 2:
                    tag_suggestions.append((tag, count))
            
            # 문서 제목에서 공통 키워드 추출
            title_words = []
            for doc in collection.documents:
                words = doc.title.split()
                title_words.extend([w.lower().strip('.,!?') for w in words if len(w) > 3])
            
            word_counter = Counter(title_words)
            title_suggestions = [
                (word, count) for word, count in word_counter.most_common(10)
                if word.lower() != topic.lower() and count >= 2
            ]
            
            # 통합 및 정렬
            all_suggestions = tag_suggestions + title_suggestions
            all_suggestions.sort(key=lambda x: x[1], reverse=True)
            
            return all_suggestions[:top_k]
            
        except Exception as e:
            logger.error(f"관련 주제 제안 실패: {e}")
            return []


def test_topic_collector():
    """주제 수집기 테스트"""
    import tempfile
    import shutil
    from ..features.advanced_search import AdvancedSearchEngine
    
    try:
        # 임시 vault 및 캐시 생성
        temp_vault = tempfile.mkdtemp()
        temp_cache = tempfile.mkdtemp()
        
        # 다양한 주제의 테스트 문서들 생성
        test_docs = [
            ("tdd_basics.md", """---
tags:
  - development/tdd
  - testing/unit
---

# TDD 기본 개념

TDD는 테스트 주도 개발 방법론입니다.
Red-Green-Refactor 사이클을 따릅니다.
단위 테스트를 먼저 작성하고 구현합니다."""),
            
            ("tdd_practice.md", """---
tags:
  - development/tdd  
  - practice/coding
---

# TDD 실습 가이드

테스트를 먼저 작성하는 실습을 해봅시다.
실패하는 테스트를 만들고 구현으로 통과시킵니다."""),
            
            ("refactoring_guide.md", """---
tags:
  - development/refactoring
  - code-quality/improvement
---

# 리팩토링 가이드

코드의 구조를 개선하는 방법들입니다.
테스트가 있어야 안전하게 리팩토링할 수 있습니다."""),
            
            ("clean_code.md", """---
tags:
  - development/clean-code
  - best-practices/coding
---

# Clean Code 원칙

깨끗한 코드 작성의 기본 원칙들입니다.
읽기 쉽고 이해하기 쉬운 코드를 만드는 것이 목표입니다."""),
            
            ("architecture.md", """---
tags:
  - architecture/software
  - design/system
---

# 소프트웨어 아키텍처

시스템의 전체적인 구조를 설계하는 방법입니다.
모듈화와 의존성 관리가 핵심입니다.""")
        ]
        
        for filename, content in test_docs:
            with open(Path(temp_vault) / filename, 'w', encoding='utf-8') as f:
                f.write(content)
        
        # 검색 엔진 초기화 및 인덱싱
        config = {
            "model": {"name": "paraphrase-multilingual-mpnet-base-v2"},
            "vault": {"excluded_dirs": [], "file_extensions": [".md"]},
            "collection": {
                "min_documents": 1,
                "group_by_tags": True,
                "include_statistics": True,
                "output_format": "markdown"
            }
        }
        
        search_engine = AdvancedSearchEngine(temp_vault, temp_cache, config)
        print("검색 엔진 인덱싱 중...")
        if not search_engine.build_index():
            print("❌ 인덱싱 실패")
            return False
        
        # 주제 수집기 초기화
        collector = TopicCollector(search_engine, config)
        
        # TDD 주제 수집 테스트
        print("\n📚 'TDD' 주제 문서 수집 중...")
        collection = collector.collect_topic(
            topic="TDD",
            top_k=10,
            threshold=0.2
        )
        
        print(f"\n📊 수집 결과:")
        print(f"- 주제: {collection.metadata.topic}")
        print(f"- 총 문서: {collection.metadata.total_documents}개")
        print(f"- 총 단어: {collection.metadata.total_word_count:,}개")
        print(f"- 검색 쿼리: '{collection.metadata.search_query}'")
        
        print(f"\n🏷️ 태그 분포:")
        for tag, count in collection.metadata.tag_distribution.items():
            print(f"  - {tag}: {count}개")
        
        print(f"\n📁 그룹별 문서:")
        for group, docs in collection.grouped_documents.items():
            print(f"  {group}:")
            for doc in docs:
                print(f"    - {doc.path} ({doc.word_count} 단어)")
        
        # 마크다운 내보내기 테스트
        output_file = Path(temp_cache) / "tdd_collection.md"
        if collector.export_collection(collection, str(output_file), "markdown"):
            print(f"\n💾 마크다운 저장: {output_file}")
            
            # 생성된 파일 일부 확인
            with open(output_file, 'r', encoding='utf-8') as f:
                content = f.read()
                print("\n📝 생성된 마크다운 파일 일부:")
                print(content[:500] + "...")
        
        # JSON 내보내기 테스트
        json_file = Path(temp_cache) / "tdd_collection.json"
        if collector.export_collection(collection, str(json_file), "json"):
            print(f"\n💾 JSON 저장: {json_file}")
        
        # 관련 주제 제안 테스트
        print(f"\n🔗 'TDD' 관련 주제 제안:")
        suggestions = collector.suggest_related_topics("TDD", top_k=5)
        for topic, count in suggestions:
            print(f"  - {topic} ({count}회 언급)")
        
        # 개발 주제 수집 테스트
        print(f"\n📚 'development' 주제 문서 수집 중...")
        dev_collection = collector.collect_topic(
            topic="development",
            top_k=20,
            threshold=0.1
        )
        
        print(f"- 개발 관련 문서: {dev_collection.metadata.total_documents}개")
        
        # 정리
        shutil.rmtree(temp_vault)
        shutil.rmtree(temp_cache)
        
        print("✅ 주제 수집기 테스트 완료!")
        return True
        
    except Exception as e:
        print(f"❌ 주제 수집기 테스트 실패: {e}")
        return False


if __name__ == "__main__":
    test_topic_collector()