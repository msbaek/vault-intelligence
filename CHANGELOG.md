# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [2026-01-12]

### Changed
- 문서 재구조화 계획 수립 및 진행

## [2025-12-13]

### Added
- CLI 빠른 참조 가이드 (CLAUDE.md)
- 문서 감사 보고서 (DOCUMENTATION_AUDIT_REPORT.md)

## [2025-09-08]

### Added
- 포괄적인 보안 시스템 구현 (SECURITY.md)
- 취약점 보고 절차 문서화

## [2025-09-05]

### Added
- 관련 문서 찾기 기능 (`python -m src related`)

### Changed
- `__pycache__` 파일 정리

## [2025-08-27]

### Fixed
- ColBERT 메타데이터 무결성 문제 완전 해결
  - `store_colbert_embedding`에서 실제 배열 크기 추출로 수정
  - 100% 정확한 메타데이터 저장 보장
- ColBERT 재순위화 지원 추가
  - 모든 검색 방법(semantic, keyword, colbert, hybrid)에서 `--rerank` 옵션 지원

### Changed
- 전체 Vault 재인덱싱 완료 (2,316개 문서)
- 캐시 효율성 99%+ 달성

## [2025-08-26]

### Added
- ColBERT 버그 수정 계획 문서

## [2025-08-25]

### Added
- 폴더별 재인덱싱 자동화 스크립트

### Changed
- 동시 처리를 위한 시스템 성능 최적화
- claude 설정에서 vault 접근 권한 확장

## [2025-08-24] - Phase 9

### Added
- 다중 문서 요약 시스템 (`document_summarizer.py`)
- 문서 클러스터링 기능 (`content_clusterer.py`)
  - K-means, DBSCAN, Agglomerative 알고리즘 지원
- 학습 리뷰 시스템 (`learning_reviewer.py`)
  - 주간/월간/분기별 학습 활동 분석
- Claude Code LLM 통합 모듈 (`claude_code_integration.py`)

### Changed
- 오픈소스 공개 준비 완료
- 문서 중복 제거

## [2025-08-23] - Phase 8

### Added
- MOC(Map of Content) 자동 생성 시스템 (`moc_generator.py`)
- ColBERT 증분 캐싱 시스템으로 전체 vault 검색 지원

### Changed
- README.md에 MOC 기능 문서화

## [2025-08-22]

### Added
- 지식 그래프 시각화 시스템 (`knowledge_graph.py`)
- 한글 폰트 지원 (시각화)

## [2025-08-21] - Phase 5, 6, 7

### Added
- Phase 7: BGE-M3 기반 자동 태깅 시스템 (`semantic_tagger.py`)
- Phase 6: 지식 그래프 분석 시스템
- Phase 5: 검색 품질 향상 시스템
  - Cross-encoder 재순위화 (`reranker.py`) - BGE Reranker V2-M3
  - ColBERT 토큰 레벨 검색 (`colbert_search.py`)
  - 쿼리 확장 (`query_expansion.py`) - 동의어 + HyDE
- Phase 4: 성능 최적화 (25-40배 향상)
- 주제별 문서 수집에 쿼리 확장 지원

### Fixed
- 캐시 활용 검색 시스템 완전 복구
- 점진적 인덱싱 구현

## [2025-08-20] - Phase 1, 2, 3

### Added
- Phase 3: BGE-M3 기반 하이브리드 검색 시스템
  - Dense 임베딩 (의미적 검색)
  - Sparse 임베딩 (키워드 검색, BM25)
- Phase 2: 다층 검색 엔진 (`advanced_search.py`)
- Phase 1: Sentence Transformers 기반 임베딩 엔진 (`sentence_transformer_engine.py`)
- 폴더별 점진적 색인 기능
- SQLite 기반 임베딩 캐시 시스템 (`embedding_cache.py`)
- Vault 파일 처리기 (`vault_processor.py`)

### Changed
- 성능 최대화 설정 옵션 문서화

---

## Summary by Phase

| Phase | Date | Features |
|-------|------|----------|
| 1 | 2025-08-20 | Sentence Transformers 임베딩 엔진 |
| 2-3 | 2025-08-20 | BGE-M3 하이브리드 검색 (Dense + Sparse) |
| 4 | 2025-08-21 | 성능 최적화 (25-40배 향상) |
| 5 | 2025-08-21 | Reranking, ColBERT, 쿼리 확장 |
| 6 | 2025-08-21 | 지식 그래프 분석 |
| 7 | 2025-08-21 | 자동 태깅 시스템 |
| 8 | 2025-08-23 | MOC 자동 생성 |
| 9 | 2025-08-24 | 다중 문서 요약 시스템 |
