# 문서 업데이트 (2/7~2/14 변경사항 반영) Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 최근 1주일(2/7~2/14) 커밋 변경사항을 CHANGELOG.md, README.md, CLAUDE.md에 반영

**Architecture:** 3개 마크다운 파일에 대한 순차적 편집. 기존 문서 구조/패턴을 유지하면서 새 섹션/행을 삽입.

**Tech Stack:** Markdown editing only (no code changes)

---

### Task 1: CHANGELOG.md — 날짜 섹션 추가

**Files:**
- Modify: `CHANGELOG.md:8-9` (## [Unreleased] 아래)

**Step 1: `[Unreleased]`와 `[2026-02-11]` 사이에 2개 날짜 섹션 삽입**

Edit `CHANGELOG.md`:
- old_string: `## [Unreleased]\n\n## [2026-02-11]`
- new_string:

```markdown
## [Unreleased]

## [2026-02-13]

### Added
- 주제별 문서 연결 기능 (`connect-topic`, `list-tags`, `connect-status` 명령어)
- `tag_analyzer.py` — vault 태그 분석 및 집계 모듈
- `topic_connector.py` — 주제별 MOC 생성 + 관련 문서 링크 오케스트레이터

## [2026-02-08]

### Added
- 고립 태그 자동 정리 기능 (`clean-tags` 명령어)
- 최소 단어 수 필터링으로 저품질 문서 인덱싱 제외 (`settings.yaml: min_word_count`)

### Fixed
- centrality boost 검색에서 threshold 파라미터 올바르게 전달
- symlink 지원 및 캐시 무효화 정확도 개선

### Changed
- 라이센스 MIT → PolyForm Noncommercial 1.0.0

## [2026-02-11]
```

**Step 2: Summary by Phase 테이블 마지막 행 아래에 추가**

Edit `CHANGELOG.md`:
- old_string: `| 9 | 2025-08-24 | 다중 문서 요약 시스템 |`
- new_string:

```markdown
| 9 | 2025-08-24 | 다중 문서 요약 시스템 |
| 10+ | 2026-02-08 | 주제별 문서 연결, 고립 태그 정리, 인덱싱 품질 개선 |
```

**Step 3: 변경 확인 및 커밋**

```bash
git diff CHANGELOG.md
git add CHANGELOG.md
```

---

### Task 2: README.md — 주요 기능 표, 아키텍처, CLI 예시 업데이트

**Files:**
- Modify: `README.md:149-178` (주요 기능 표 + 아키텍처)
- Modify: `README.md:55-73` (CLI 예시)

**Step 1: 주요 기능 표에 3행 추가**

Edit `README.md`:
- old_string: `| **MOC** | 체계적 목차 생성 | `generate-moc --topic "주제"` |`
- new_string:

```markdown
| **MOC** | 체계적 목차 생성 | `generate-moc --topic "주제"` |
| **태그 분석** | vault 태그 집계 및 계층 분석 | `list-tags` |
| **주제 연결** | 주제별 MOC + 관련 문서 링크 삽입 | `connect-topic "주제"` |
| **고립 태그 정리** | 사용되지 않는 태그 자동 정리 | `clean-tags` |
```

**Step 2: 아키텍처 다이어그램에 항목 추가**

Edit `README.md`:
- old_string: `    └── 학습 패턴 분석`
- new_string:

```
    ├── 학습 패턴 분석
    └── 주제별 문서 연결
```

**Step 3: CLI 예시에 새 명령어 추가**

Edit `README.md`:
- old_string: `# 학습 리뷰 생성\nvis review --period weekly`
- new_string:

```bash
# 학습 리뷰 생성
vis review --period weekly

# 태그 분석
vis list-tags

# 주제별 문서 연결 (MOC 생성 + 관련 링크 삽입)
vis connect-topic "TDD"
```

**Step 4: 주요 특징에 문서 연결 항목 추가**

Edit `README.md`:
- old_string: `- 🇰🇷 **한국어 최적화**: 동의어 확장 및 HyDE 기술`
- new_string:

```markdown
- 🔗 **주제별 문서 연결**: 태그 기반 MOC 생성 + 관련 문서 자동 링크
- 🇰🇷 **한국어 최적화**: 동의어 확장 및 HyDE 기술
```

**Step 5: 변경 확인 및 커밋**

```bash
git diff README.md
git add README.md
```

---

### Task 3: CLAUDE.md — CLI 빠른 참조에 새 명령어 추가

**Files:**
- Modify: `CLAUDE.md:52-74` (기타 주요 명령어 섹션)

**Step 1: "기타 주요 명령어" 코드블록의 인덱싱 명령어 뒤에 새 명령어 추가**

Edit `CLAUDE.md`:
- old_string: `vis reindex --force            # 강제 전체 재인덱싱\n```\n`
- new_string:

```bash
vis reindex --force            # 강제 전체 재인덱싱

# 태그 분석
vis list-tags

# 주제별 문서 연결
vis connect-topic "TDD" --dry-run    # 미리보기
vis connect-topic "TDD"              # 실행

# 연결 상태 확인
vis connect-status

# 고립 태그 정리
vis clean-tags --dry-run
vis clean-tags
```

(코드블록 닫기)

**Step 2: 변경 확인 및 커밋**

```bash
git diff CLAUDE.md
git add CLAUDE.md
```

---

### Task 4: 최종 커밋

**Step 1: 모든 변경 파일 스테이징 및 커밋**

```bash
git add CHANGELOG.md README.md CLAUDE.md docs/plans/2026-02-14-docs-update-design.md
git commit -m "docs: 최근 1주일 변경사항 문서 반영 (connect-topic, clean-tags 등)"
```
