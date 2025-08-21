#!/usr/bin/env python3
"""
Vault File Processor for Vault Intelligence System V2

Obsidian vault의 마크다운 파일들을 처리하여 메타데이터를 추출하고 임베딩을 생성
"""

import os
import re
import yaml
import logging
import fnmatch
from typing import Dict, List, Optional, Tuple, Set
from pathlib import Path
from dataclasses import dataclass, asdict
from datetime import datetime
import hashlib

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class Document:
    """문서 정보를 담는 데이터 클래스"""
    path: str
    title: str
    content: str
    tags: List[str]
    frontmatter: Dict
    word_count: int
    char_count: int
    file_size: int
    modified_at: datetime
    file_hash: str
    embedding: Optional[object] = None


class VaultProcessor:
    """Vault 파일 처리기"""
    
    def __init__(
        self, 
        vault_path: str,
        excluded_dirs: Optional[List[str]] = None,
        excluded_files: Optional[List[str]] = None,
        file_extensions: Optional[List[str]] = None,
        include_folders: Optional[List[str]] = None,
        exclude_folders: Optional[List[str]] = None
    ):
        """
        Args:
            vault_path: Vault 루트 경로
            excluded_dirs: 제외할 디렉토리 목록
            excluded_files: 제외할 파일 패턴 목록 (glob 패턴 지원)
            file_extensions: 처리할 파일 확장자 목록
            include_folders: 포함할 폴더 목록 (설정 시 이 폴더들만 처리)
            exclude_folders: 제외할 폴더 목록
        """
        self.vault_path = Path(vault_path)
        
        self.excluded_dirs = excluded_dirs or [
            ".obsidian", ".trash", "ATTACHMENTS", ".git", 
            "__pycache__", ".DS_Store"
        ]
        
        self.excluded_files = excluded_files or [
            ".DS_Store", "Thumbs.db", "desktop.ini",
            "*.tmp", "*.temp", "*.backup", "*.bak", "*.log", "*~"
        ]
        
        self.file_extensions = file_extensions or [".md", ".markdown"]
        self.include_folders = include_folders  # 포함할 폴더 목록
        self.exclude_folders = exclude_folders  # 추가로 제외할 폴더 목록
        
        logger.info(f"Vault 프로세서 초기화: {self.vault_path}")
        logger.info(f"제외 디렉토리: {self.excluded_dirs}")
        logger.info(f"제외 파일 패턴: {self.excluded_files}")
        logger.info(f"처리 확장자: {self.file_extensions}")
        if self.include_folders:
            logger.info(f"포함 폴더: {self.include_folders}")
        if self.exclude_folders:
            logger.info(f"추가 제외 폴더: {self.exclude_folders}")
    
    def find_all_files(self) -> List[Path]:
        """Vault 내 모든 마크다운 파일 검색"""
        files = []
        
        try:
            for root, dirs, file_names in os.walk(self.vault_path):
                # 제외 디렉토리 필터링
                dirs[:] = [d for d in dirs if d not in self.excluded_dirs]
                
                # 폴더 필터링 로직
                current_path = Path(root)
                relative_path = current_path.relative_to(self.vault_path)
                relative_str = str(relative_path)
                
                # include_folders가 설정된 경우: 해당 폴더들만 포함
                if self.include_folders:
                    should_include = False
                    for include_folder in self.include_folders:
                        if relative_str == include_folder or relative_str.startswith(include_folder + '/') or relative_str == '.':
                            should_include = True
                            break
                    if not should_include:
                        continue
                
                # exclude_folders 추가 필터링
                if self.exclude_folders:
                    should_exclude = False
                    for exclude_folder in self.exclude_folders:
                        if relative_str == exclude_folder or relative_str.startswith(exclude_folder + '/'):
                            should_exclude = True
                            break
                    if should_exclude:
                        continue
                
                for file_name in file_names:
                    # 파일 확장자 필터링
                    if not any(file_name.endswith(ext) for ext in self.file_extensions):
                        continue
                    
                    # 제외 파일 패턴 필터링
                    if self._should_exclude_file(file_name):
                        continue
                    
                    file_path = Path(root) / file_name
                    files.append(file_path)
            
            logger.info(f"발견된 파일: {len(files)}개")
            return files
        
        except Exception as e:
            logger.error(f"파일 검색 실패: {e}")
            return []
    
    def _should_exclude_file(self, file_name: str) -> bool:
        """파일이 제외 패턴에 매칭되는지 확인"""
        for pattern in self.excluded_files:
            if fnmatch.fnmatch(file_name, pattern):
                logger.debug(f"파일 제외: {file_name} (패턴: {pattern})")
                return True
        return False
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """파일 해시 계산"""
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
                return hashlib.md5(content).hexdigest()
        except Exception as e:
            logger.error(f"파일 해시 계산 실패: {file_path}, {e}")
            return ""
    
    def _extract_frontmatter(self, content: str) -> Tuple[Dict, str]:
        """Frontmatter 추출"""
        frontmatter = {}
        main_content = content
        
        try:
            # YAML frontmatter 패턴 매칭
            frontmatter_pattern = r'^---\s*\n(.*?)\n---\s*\n'
            match = re.match(frontmatter_pattern, content, re.DOTALL)
            
            if match:
                yaml_content = match.group(1)
                try:
                    frontmatter = yaml.safe_load(yaml_content) or {}
                except yaml.YAMLError as e:
                    logger.debug(f"YAML 파싱 오류: {e}")  # WARNING에서 DEBUG로 변경
                
                # frontmatter 제거한 본문 추출
                main_content = content[match.end():]
        
        except Exception as e:
            logger.error(f"Frontmatter 추출 실패: {e}")
        
        return frontmatter, main_content
    
    def _extract_tags(self, frontmatter: Dict, content: str) -> List[str]:
        """태그 추출 (frontmatter + inline tags)"""
        tags = set()
        
        # Frontmatter 태그
        if 'tags' in frontmatter:
            fm_tags = frontmatter['tags']
            if isinstance(fm_tags, list):
                tags.update(fm_tags)
            elif isinstance(fm_tags, str):
                tags.add(fm_tags)
        
        # 인라인 태그 (#tag 형식)
        inline_tags = re.findall(r'#([a-zA-Z0-9가-힣_/-]+)', content)
        tags.update(inline_tags)
        
        return sorted(list(tags))
    
    def _extract_title(self, frontmatter: Dict, content: str, file_path: Path) -> str:
        """제목 추출"""
        # 1. Frontmatter의 title
        if 'title' in frontmatter:
            return str(frontmatter['title'])
        
        # 2. 첫 번째 H1 헤더
        h1_match = re.search(r'^# (.+)$', content, re.MULTILINE)
        if h1_match:
            return h1_match.group(1).strip()
        
        # 3. 파일명 (확장자 제거)
        return file_path.stem
    
    def _count_words(self, content: str) -> int:
        """단어 수 계산 (한글/영어 혼합 지원)"""
        try:
            # 마크다운 문법 제거
            clean_content = re.sub(r'[#*\-`]', '', content)
            clean_content = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', clean_content)
            
            # 단어 분리 (공백, 구두점 기준)
            words = re.findall(r'[a-zA-Z가-힣0-9]+', clean_content)
            return len(words)
        except Exception as e:
            logger.error(f"단어 수 계산 실패: {e}")
            return 0
    
    def _clean_content(self, content: str) -> str:
        """검색용 콘텐츠 정리"""
        try:
            # 마크다운 링크 정리 [텍스트](링크) -> 텍스트
            content = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', content)
            
            # 이미지 링크 제거
            content = re.sub(r'!\[([^\]]*)\]\([^\)]+\)', r'\1', content)
            
            # 인라인 코드 정리
            content = re.sub(r'`([^`]+)`', r'\1', content)
            
            # 헤더 마크 제거
            content = re.sub(r'^#{1,6}\s*', '', content, flags=re.MULTILINE)
            
            # 목록 마크 제거
            content = re.sub(r'^\s*[-*+]\s+', '', content, flags=re.MULTILINE)
            content = re.sub(r'^\s*\d+\.\s+', '', content, flags=re.MULTILINE)
            
            # 인용구 마크 제거
            content = re.sub(r'^>\s*', '', content, flags=re.MULTILINE)
            
            # 다중 공백/줄바꿈 정리
            content = re.sub(r'\n{3,}', '\n\n', content)
            content = re.sub(r' {2,}', ' ', content)
            
            return content.strip()
        
        except Exception as e:
            logger.error(f"콘텐츠 정리 실패: {e}")
            return content
    
    def process_file(self, file_path: Path) -> Optional[Document]:
        """단일 파일 처리"""
        try:
            # 파일 정보
            stat = file_path.stat()
            file_size = stat.st_size
            modified_at = datetime.fromtimestamp(stat.st_mtime)
            file_hash = self._calculate_file_hash(file_path)
            
            # 파일 읽기
            with open(file_path, 'r', encoding='utf-8') as f:
                raw_content = f.read()
            
            # Frontmatter와 본문 분리
            frontmatter, main_content = self._extract_frontmatter(raw_content)
            
            # 메타데이터 추출
            title = self._extract_title(frontmatter, main_content, file_path)
            tags = self._extract_tags(frontmatter, main_content)
            word_count = self._count_words(main_content)
            char_count = len(main_content)
            
            # 콘텐츠 정리
            clean_content = self._clean_content(main_content)
            
            # 검색용 전체 텍스트 구성 (제목 + 태그 + 본문)
            search_content = f"{title}\n{' '.join(tags)}\n{clean_content}"
            
            return Document(
                path=str(file_path),
                title=title,
                content=search_content,
                tags=tags,
                frontmatter=frontmatter,
                word_count=word_count,
                char_count=char_count,
                file_size=file_size,
                modified_at=modified_at,
                file_hash=file_hash
            )
        
        except Exception as e:
            logger.debug(f"파일 처리 실패: {file_path}, {e}")  # ERROR에서 DEBUG로 변경
            return None
    
    def process_all_files(self, progress_callback=None) -> List[Document]:
        """모든 파일 배치 처리"""
        files = self.find_all_files()
        documents = []
        
        logger.info(f"파일 처리 시작: {len(files)}개")
        
        for i, file_path in enumerate(files):
            try:
                document = self.process_file(file_path)
                if document:
                    documents.append(document)
                
                # 진행률 콜백
                if progress_callback and (i + 1) % 100 == 0:
                    progress_callback(i + 1, len(files))
            
            except Exception as e:
                logger.error(f"파일 처리 중 오류: {file_path}, {e}")
        
        logger.info(f"파일 처리 완료: {len(documents)}개 성공")
        return documents
    
    def get_vault_statistics(self) -> Dict:
        """Vault 통계 정보"""
        try:
            files = self.find_all_files()
            total_size = sum(f.stat().st_size for f in files if f.exists())
            
            # 디렉토리별 파일 수
            dir_counts = {}
            for file_path in files:
                parent_dir = str(file_path.parent.relative_to(self.vault_path))
                if parent_dir == '.':
                    parent_dir = 'root'
                dir_counts[parent_dir] = dir_counts.get(parent_dir, 0) + 1
            
            return {
                "vault_path": str(self.vault_path),
                "total_files": len(files),
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "directory_counts": dict(sorted(dir_counts.items())),
                "excluded_dirs": self.excluded_dirs,
                "file_extensions": self.file_extensions
            }
        
        except Exception as e:
            logger.error(f"통계 생성 실패: {e}")
            return {}
    
    def filter_by_tags(self, documents: List[Document], tags: List[str]) -> List[Document]:
        """태그로 문서 필터링"""
        if not tags:
            return documents
        
        filtered = []
        tag_set = set(tag.lower() for tag in tags)
        
        for doc in documents:
            doc_tags = set(tag.lower() for tag in doc.tags)
            if tag_set.intersection(doc_tags):
                filtered.append(doc)
        
        return filtered
    
    def filter_by_date_range(
        self, 
        documents: List[Document], 
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Document]:
        """날짜 범위로 문서 필터링"""
        filtered = []
        
        for doc in documents:
            if start_date and doc.modified_at < start_date:
                continue
            if end_date and doc.modified_at > end_date:
                continue
            filtered.append(doc)
        
        return filtered
    
    def search_by_content(self, documents: List[Document], query: str) -> List[Document]:
        """콘텐츠 텍스트 검색"""
        if not query:
            return documents
        
        query_lower = query.lower()
        results = []
        
        for doc in documents:
            if (query_lower in doc.title.lower() or 
                query_lower in doc.content.lower() or
                any(query_lower in tag.lower() for tag in doc.tags)):
                results.append(doc)
        
        return results


def test_processor():
    """프로세서 테스트"""
    import tempfile
    import shutil
    
    try:
        # 임시 vault 생성
        temp_vault = tempfile.mkdtemp()
        
        # 테스트 파일 생성
        test_content = """---
title: "테스트 문서"
tags:
  - test
  - vault-intelligence
---

# 테스트 문서

이것은 테스트용 마크다운 문서입니다.

## 섹션 1

여기에 내용이 있습니다. #inline-tag

- 목록 항목 1
- 목록 항목 2

[링크 텍스트](https://example.com)
"""
        
        test_file = Path(temp_vault) / "test.md"
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(test_content)
        
        # 프로세서 테스트
        processor = VaultProcessor(temp_vault)
        
        # 파일 검색 테스트
        files = processor.find_all_files()
        print(f"발견된 파일: {len(files)}개")
        
        # 파일 처리 테스트
        document = processor.process_file(test_file)
        print(f"문서 처리 성공: {document is not None}")
        
        if document:
            print(f"제목: {document.title}")
            print(f"태그: {document.tags}")
            print(f"단어 수: {document.word_count}")
        
        # 통계 테스트
        stats = processor.get_vault_statistics()
        print(f"Vault 통계: {stats}")
        
        # 정리
        shutil.rmtree(temp_vault)
        print("✅ 프로세서 테스트 완료!")
        return True
        
    except Exception as e:
        print(f"❌ 프로세서 테스트 실패: {e}")
        return False


if __name__ == "__main__":
    test_processor()