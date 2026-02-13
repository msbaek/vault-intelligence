# Plan: Obsidian Graph View 최대 활용 — 주제별 점진적 문서 연결

**Status**: Phase 1 완료 (구현), Phase 2 대기 (실행)
**Created**: 2026-02-13
**Resume point**: Phase 2 시작 → `vis connect-topic "tdd"` 실행부터

## Context

Obsidian vault(3,203개 문서)에서 graph view를 의미 있는 탐색 도구로 활용하기 위해
태그 기반 주제 추출 → MOC 생성 + 관련 문서 링크 삽입을 반복하여 문서를 연결한다.

## Phase 1: 구현 ✅ 완료

### 완료된 작업
- [x] `src/features/tag_analyzer.py` — 태그 분석/집계 모듈 (신규)
- [x] `src/features/topic_connector.py` — 주제별 연결 오케스트레이터 (신규)
- [x] `src/__main__.py` — 3개 subparser 추가 (+202줄)
- [x] CLI 검증: `list-tags`, `connect-topic`, `connect-status` 모두 정상 동작
- [x] dry-run 검증: TDD 147문서, 138개 링크 추가 가능 확인
- [x] `feature/graph-connect` 브랜치 → main 머지 완료 (db43b7c)

### 구현된 명령어
```bash
vis list-tags [--depth N] [--min-count N] [--output FILE]
vis connect-topic "주제" [--dry-run] [--skip-moc] [--skip-related] [--related-k N]
vis connect-status [--detailed]
```

## Phase 2: 실제 주제 연결 실행 ⬚ 대기

### Vault 현황 (2026-02-13 기준)
- 총 문서: 3,203개
- 태그됨: 2,457개 (76.7%)
- 미태그: 746개 (23.3%)
- 10개 이상 문서 주제: 24개

### 실행 순서 (문서 수 기준 내림차순)
- [ ] tdd (147 docs) — dry-run 완료, 실행 대기
- [ ] daily-notes (215 docs)
- [ ] code-review (54 docs)
- [ ] testing (44 docs)
- [ ] refactoring (38 docs)
- [ ] ai (35 docs)
- [ ] team (32 docs)
- [ ] career (29 docs)
- [ ] kent-beck (26 docs)
- [ ] database (25 docs)
- [ ] java (21 docs)
- [ ] architecture (19 docs)
- [ ] article (19 docs)
- [ ] reference (16 docs)
- [ ] guide (14 docs)
- [ ] tutorial (13 docs)
- [ ] performance (13 docs)
- [ ] agile (12 docs)
- [ ] javascript (11 docs)
- [ ] excalidraw (11 docs)
- [ ] productivity (10 docs)
- [ ] 나머지 소규모 주제들

### 실행 방법
```bash
# 주제별 반복 실행
vis --vault-path ~/DocumentsLocal/msbaek_vault connect-topic "tdd"
vis --vault-path ~/DocumentsLocal/msbaek_vault connect-status
# Obsidian graph view 확인 후 다음 주제
```

## Phase 3: 최종 정리 ⬚ 대기
- [ ] 미태그 문서 746개 태깅 (`vis tag`)
- [ ] 남은 고립 노드 처리
- [ ] `#ai` vs `ai` 등 중복 태그 정규화 검토

## 알려진 이슈
- knowledge_graph 로그가 `--verbose` 없이도 INFO 레벨로 대량 출력됨 (기능에 영향 없음)
- `#ai`, `#legacy-code` 등 해시 접두사 태그가 별도 집계 (frontmatter에 `#` 포함 저장)
