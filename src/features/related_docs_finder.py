#!/usr/bin/env python3
"""
Related Documents Finder for Vault Intelligence System V2

특정 Obsidian 문서에 대한 관련 문서를 찾아 "관련 문서" 섹션을 자동으로 추가하는 시스템
"""

import os
import re
import logging
from typing import List, Dict, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime

from ..core.vault_processor import Document
from .advanced_search import AdvancedSearchEngine, SearchResult
from ..utils.ofm import to_wikilink

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class RelatedDocResult:
    """관련 문서 결과"""
    target_file_path: str
    related_docs: List[SearchResult]
    success: bool
    error_message: str = ""
    processing_time: float = 0.0
    section_added: bool = False
    existing_section_updated: bool = False


class RelatedDocsFinder:
    """관련 문서 찾기 및 문서 업데이트 시스템"""
    
    def __init__(
        self,
        search_engine: AdvancedSearchEngine,
        config: Dict = None
    ):
        """
        Args:
            search_engine: 구축된 AdvancedSearchEngine 인스턴스
            config: 설정 딕셔너리
        """
        self.search_engine = search_engine
        self.config = config or {}
        
        # 기본 설정
        self.default_top_k = self.config.get('related_docs', {}).get('default_top_k', 5)
        self.default_threshold = self.config.get('related_docs', {}).get('default_threshold', 0.3)
        self.section_title = self.config.get('related_docs', {}).get('section_title', '## 관련 문서')
        self.show_similarity = self.config.get('related_docs', {}).get('show_similarity', True)
        self.show_snippet = self.config.get('related_docs', {}).get('show_snippet', False)
        
        logger.info("관련 문서 찾기 시스템 초기화 완료")
    
    def find_related_docs(
        self,
        file_path: str,
        top_k: int = None,
        threshold: float = None,
        include_centrality: bool = True
    ) -> List[SearchResult]:
        """
        특정 문서의 관련 문서들을 찾습니다.
        
        Args:
            file_path: 대상 문서 경로
            top_k: 반환할 관련 문서 수
            threshold: 유사도 임계값
            include_centrality: 중심성 점수 포함 여부
            
        Returns:
            관련 문서 목록 (SearchResult)
        """
        try:
            if top_k is None:
                top_k = self.default_top_k
            if threshold is None:
                threshold = self.default_threshold
            
            logger.info(f"관련 문서 검색: {file_path}")
            
            # 기존 AdvancedSearchEngine의 get_related_documents 메서드 활용
            related_results = self.search_engine.get_related_documents(
                document_path=file_path,
                top_k=top_k,
                include_centrality_boost=include_centrality,
                similarity_threshold=threshold
            )
            
            logger.info(f"관련 문서 {len(related_results)}개 발견")
            return related_results
            
        except Exception as e:
            logger.error(f"관련 문서 검색 실패: {e}")
            return []
    
    def format_related_section(
        self,
        related_docs: List[SearchResult],
        show_similarity: bool = None,
        show_snippet: bool = None,
        format_style: str = "detailed"
    ) -> str:
        """
        관련 문서 목록을 마크다운 섹션으로 포맷팅합니다.
        
        Args:
            related_docs: 관련 문서 목록
            show_similarity: 유사도 점수 표시 여부
            show_snippet: 스니펫 표시 여부  
            format_style: 포맷 스타일 ("simple", "detailed")
            
        Returns:
            마크다운 형식의 관련 문서 섹션
        """
        try:
            if not related_docs:
                return ""
            
            if show_similarity is None:
                show_similarity = self.show_similarity
            if show_snippet is None:
                show_snippet = self.show_snippet
            
            lines = [self.section_title, ""]
            
            for result in related_docs:
                doc = result.document
                
                # 위키링크 형식으로 문서 제목 생성 (vault-relative 경로 사용)
                link_text = to_wikilink(doc.path, self.search_engine.vault_path)
                
                if format_style == "simple":
                    # 간단한 형식: - [[문서제목]]
                    lines.append(f"- {link_text}")
                    
                elif format_style == "detailed":
                    # 상세 형식: - [[문서제목]] (유사도: 0.75)
                    line = f"- {link_text}"
                    
                    if show_similarity:
                        line += f" (유사도: {result.similarity_score:.3f})"
                    
                    lines.append(line)
                    
                    # 스니펫 추가 (선택적)
                    if show_snippet and result.snippet:
                        # 스니펫을 들여쓰기로 추가
                        snippet_lines = result.snippet.split('\n')
                        for snippet_line in snippet_lines:
                            if snippet_line.strip():
                                lines.append(f"  - {snippet_line.strip()}")
                    
                    # 태그 정보 추가 (선택적)
                    if doc.tags and len(doc.tags) > 0:
                        tags_str = ", ".join([f"#{tag}" for tag in doc.tags[:3]])  # 최대 3개까지
                        lines.append(f"  - 태그: {tags_str}")
            
            lines.append("")  # 마지막 빈 줄
            return "\n".join(lines)
            
        except Exception as e:
            logger.error(f"관련 문서 섹션 포맷팅 실패: {e}")
            return ""
    
    def update_document(
        self,
        file_path: str,
        related_docs: List[SearchResult] = None,
        top_k: int = None,
        threshold: float = None,
        update_existing: bool = True,
        backup: bool = False,
        dry_run: bool = False
    ) -> RelatedDocResult:
        """
        문서에 관련 문서 섹션을 추가하거나 업데이트합니다.
        
        Args:
            file_path: 대상 문서 경로
            related_docs: 미리 계산된 관련 문서 (None이면 새로 계산)
            top_k: 관련 문서 수
            threshold: 유사도 임계값
            update_existing: 기존 섹션 업데이트 여부
            backup: 백업 생성 여부
            dry_run: 실제 수정 없이 미리보기만
            
        Returns:
            RelatedDocResult: 처리 결과
        """
        start_time = datetime.now()
        
        try:
            file_path = Path(file_path)
            
            # 파일 존재 확인
            if not file_path.exists():
                return RelatedDocResult(
                    target_file_path=str(file_path),
                    related_docs=[],
                    success=False,
                    error_message=f"파일이 존재하지 않습니다: {file_path}"
                )
            
            # 관련 문서 찾기 (필요한 경우)
            if related_docs is None:
                related_docs = self.find_related_docs(
                    str(file_path), 
                    top_k=top_k, 
                    threshold=threshold
                )
            
            if not related_docs:
                return RelatedDocResult(
                    target_file_path=str(file_path),
                    related_docs=[],
                    success=False,
                    error_message="관련 문서를 찾을 수 없습니다"
                )
            
            # 파일 내용 읽기
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 백업 생성 (옵션)
            if backup and not dry_run:
                backup_path = file_path.with_suffix(f'.backup.{datetime.now().strftime("%Y%m%d_%H%M%S")}.md')
                with open(backup_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                logger.info(f"백업 생성: {backup_path}")
            
            # 기존 관련 문서 섹션 찾기
            section_pattern = r'^## 관련 문서.*?(?=^##|\Z)'
            existing_match = re.search(section_pattern, content, re.MULTILINE | re.DOTALL)
            
            # 새 관련 문서 섹션 생성
            new_section = self.format_related_section(related_docs)
            
            existing_section_updated = False
            section_added = False
            
            if existing_match:
                if update_existing:
                    # 기존 섹션 교체
                    new_content = re.sub(section_pattern, new_section, content, flags=re.MULTILINE | re.DOTALL)
                    existing_section_updated = True
                    logger.info("기존 관련 문서 섹션을 업데이트했습니다")
                else:
                    logger.info("기존 관련 문서 섹션이 있어 업데이트하지 않았습니다")
                    return RelatedDocResult(
                        target_file_path=str(file_path),
                        related_docs=related_docs,
                        success=True,
                        error_message="기존 섹션 존재 (업데이트 안함)",
                        processing_time=(datetime.now() - start_time).total_seconds()
                    )
            else:
                # 파일 끝에 새 섹션 추가
                new_content = content.rstrip() + "\n\n" + new_section
                section_added = True
                logger.info("새로운 관련 문서 섹션을 추가했습니다")
            
            # 실제 파일 쓰기 (dry_run이 아닌 경우)
            if not dry_run:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                logger.info(f"파일 업데이트 완료: {file_path}")
            else:
                logger.info(f"[DRY RUN] 파일 업데이트 미리보기: {file_path}")
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return RelatedDocResult(
                target_file_path=str(file_path),
                related_docs=related_docs,
                success=True,
                processing_time=processing_time,
                section_added=section_added,
                existing_section_updated=existing_section_updated
            )
            
        except Exception as e:
            logger.error(f"문서 업데이트 실패: {e}")
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return RelatedDocResult(
                target_file_path=str(file_path),
                related_docs=related_docs or [],
                success=False,
                error_message=str(e),
                processing_time=processing_time
            )
    
    def batch_process(
        self,
        file_patterns: List[str],
        top_k: int = None,
        threshold: float = None,
        update_existing: bool = True,
        backup: bool = False,
        dry_run: bool = False,
        progress_callback=None
    ) -> List[RelatedDocResult]:
        """
        여러 문서에 대해 일괄적으로 관련 문서 섹션을 추가/업데이트합니다.
        
        Args:
            file_patterns: 파일 패턴 목록 (glob 패턴 지원)
            top_k: 관련 문서 수
            threshold: 유사도 임계값
            update_existing: 기존 섹션 업데이트 여부
            backup: 백업 생성 여부
            dry_run: 실제 수정 없이 미리보기만
            progress_callback: 진행률 콜백
            
        Returns:
            처리 결과 목록
        """
        try:
            # 파일 목록 수집
            all_files = []
            vault_path = Path(self.search_engine.vault_path)
            
            for pattern in file_patterns:
                if "/" in pattern:
                    # 경로가 포함된 패턴
                    pattern_path = Path(pattern)
                    if pattern_path.is_absolute():
                        matches = list(Path("/").glob(str(pattern_path.relative_to("/"))))
                    else:
                        matches = list(vault_path.glob(pattern))
                else:
                    # 파일명만 있는 패턴 - vault 전체에서 검색
                    matches = list(vault_path.rglob(pattern))
                
                # .md 파일만 필터링
                md_files = [f for f in matches if f.suffix.lower() == '.md']
                all_files.extend(md_files)
            
            # 중복 제거
            all_files = list(set(all_files))
            
            logger.info(f"배치 처리 대상: {len(all_files)}개 파일")
            
            if not all_files:
                logger.warning("처리할 파일이 없습니다")
                return []
            
            results = []
            
            for i, file_path in enumerate(all_files):
                try:
                    logger.info(f"처리 중 ({i+1}/{len(all_files)}): {file_path.name}")
                    
                    # 각 파일 처리
                    result = self.update_document(
                        str(file_path),
                        top_k=top_k,
                        threshold=threshold,
                        update_existing=update_existing,
                        backup=backup,
                        dry_run=dry_run
                    )
                    
                    results.append(result)
                    
                    # 진행률 콜백
                    if progress_callback:
                        progress_callback(i + 1, len(all_files))
                
                except Exception as e:
                    logger.error(f"파일 처리 실패 {file_path}: {e}")
                    results.append(RelatedDocResult(
                        target_file_path=str(file_path),
                        related_docs=[],
                        success=False,
                        error_message=str(e)
                    ))
            
            # 배치 처리 결과 요약
            successful = sum(1 for r in results if r.success)
            logger.info(f"배치 처리 완료: {successful}/{len(results)}개 성공")
            
            return results
            
        except Exception as e:
            logger.error(f"배치 처리 실패: {e}")
            return []
    
    def analyze_related_docs_coverage(
        self,
        file_patterns: List[str] = None
    ) -> Dict[str, any]:
        """
        관련 문서 섹션 커버리지를 분석합니다.
        
        Args:
            file_patterns: 분석할 파일 패턴 목록 (None이면 전체 vault)
            
        Returns:
            커버리지 분석 결과
        """
        try:
            vault_path = Path(self.search_engine.vault_path)
            
            # 파일 목록 수집
            if file_patterns is None:
                all_files = list(vault_path.rglob("*.md"))
            else:
                all_files = []
                for pattern in file_patterns:
                    matches = list(vault_path.rglob(pattern))
                    md_files = [f for f in matches if f.suffix.lower() == '.md']
                    all_files.extend(md_files)
                all_files = list(set(all_files))
            
            logger.info(f"커버리지 분석 대상: {len(all_files)}개 파일")
            
            has_related_section = 0
            no_related_section = 0
            empty_related_section = 0
            
            files_with_sections = []
            files_without_sections = []
            
            section_pattern = r'^## 관련 문서.*?(?=^##|\Z)'
            
            for file_path in all_files:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    match = re.search(section_pattern, content, re.MULTILINE | re.DOTALL)
                    
                    if match:
                        section_content = match.group(0)
                        # 실제 링크가 있는지 확인
                        if re.search(r'\[\[.*?\]\]', section_content):
                            has_related_section += 1
                            files_with_sections.append(str(file_path.relative_to(vault_path)))
                        else:
                            empty_related_section += 1
                    else:
                        no_related_section += 1
                        files_without_sections.append(str(file_path.relative_to(vault_path)))
                
                except Exception as e:
                    logger.warning(f"파일 읽기 실패 {file_path}: {e}")
                    continue
            
            total_files = len(all_files)
            coverage_rate = has_related_section / total_files if total_files > 0 else 0
            
            analysis_result = {
                'total_files': total_files,
                'has_related_section': has_related_section,
                'no_related_section': no_related_section,
                'empty_related_section': empty_related_section,
                'coverage_rate': coverage_rate,
                'files_with_sections': files_with_sections,
                'files_without_sections': files_without_sections[:20]  # 최대 20개만 표시
            }
            
            logger.info(f"관련 문서 섹션 커버리지 분석 완료:")
            logger.info(f"  - 총 파일: {total_files}개")
            logger.info(f"  - 관련 문서 섹션 있음: {has_related_section}개")
            logger.info(f"  - 관련 문서 섹션 없음: {no_related_section}개")
            logger.info(f"  - 빈 관련 문서 섹션: {empty_related_section}개")
            logger.info(f"  - 커버리지: {coverage_rate:.1%}")
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"커버리지 분석 실패: {e}")
            return {}


def test_related_docs_finder():
    """관련 문서 찾기 시스템 테스트"""
    import tempfile
    import shutil
    
    try:
        # 임시 vault 생성
        temp_vault = tempfile.mkdtemp()
        temp_cache = tempfile.mkdtemp()
        
        # 테스트 문서들 생성
        test_docs = [
            ("tdd-basics.md", """# TDD 기본 개념

TDD(Test-Driven Development)는 테스트 주도 개발 방법론입니다.

## Red-Green-Refactor 사이클
1. Red: 실패하는 테스트 작성
2. Green: 테스트를 통과하는 최소한의 코드 작성  
3. Refactor: 코드 개선

#development #tdd #testing"""),
            
            ("refactoring-guide.md", """# 리팩토링 가이드

리팩토링은 코드의 구조를 개선하는 과정입니다.

## 안전한 리팩토링
테스트가 있어야 안전하게 리팩토링할 수 있습니다.
TDD와 함께 사용하면 매우 효과적입니다.

#development #refactoring #testing"""),
            
            ("clean-code.md", """# Clean Code 원칙

깨끗한 코드 작성법을 다룹니다.

## 핵심 원칙
- 의미 있는 이름
- 작은 함수
- 좋은 주석

좋은 테스트는 깨끗한 코드의 기반입니다.

#development #clean-code #best-practices""")
        ]
        
        for filename, content in test_docs:
            with open(Path(temp_vault) / filename, 'w', encoding='utf-8') as f:
                f.write(content)
        
        # 검색 엔진 초기화
        config = {
            "model": {"name": "paraphrase-multilingual-mpnet-base-v2"},
            "vault": {"excluded_dirs": [], "file_extensions": [".md"]}
        }
        
        from .advanced_search import AdvancedSearchEngine
        search_engine = AdvancedSearchEngine(temp_vault, temp_cache, config)
        
        print("인덱스 구축 중...")
        if not search_engine.build_index():
            print("❌ 인덱스 구축 실패")
            return False
        
        # 관련 문서 찾기 시스템 초기화
        finder = RelatedDocsFinder(search_engine, config)
        
        # 테스트 1: 관련 문서 찾기
        print("\n🔍 관련 문서 찾기 테스트")
        target_file = str(Path(temp_vault) / "tdd-basics.md")
        related_docs = finder.find_related_docs(target_file, top_k=3)
        
        print(f"'{target_file}'의 관련 문서:")
        for doc in related_docs:
            print(f"  - {doc.document.title} (유사도: {doc.similarity_score:.3f})")
        
        # 테스트 2: 관련 문서 섹션 포맷팅
        print("\n📝 섹션 포맷팅 테스트")
        section = finder.format_related_section(related_docs, format_style="detailed")
        print("생성된 섹션:")
        print(section)
        
        # 테스트 3: 문서 업데이트 (드라이런)
        print("\n📄 문서 업데이트 테스트 (드라이런)")
        result = finder.update_document(target_file, related_docs, dry_run=True)
        print(f"결과: 성공={result.success}, 처리시간={result.processing_time:.2f}초")
        
        # 테스트 4: 커버리지 분석
        print("\n📊 커버리지 분석 테스트")
        coverage = finder.analyze_related_docs_coverage()
        print(f"커버리지: {coverage.get('coverage_rate', 0):.1%}")
        
        # 정리
        shutil.rmtree(temp_vault)
        shutil.rmtree(temp_cache)
        
        print("✅ 관련 문서 찾기 시스템 테스트 완료!")
        return True
        
    except Exception as e:
        print(f"❌ 테스트 실패: {e}")
        return False


if __name__ == "__main__":
    test_related_docs_finder()