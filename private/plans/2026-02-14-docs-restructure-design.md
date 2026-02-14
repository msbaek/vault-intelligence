# Documentation Restructure Design

Created: 2026-02-14

## Goal

외부 사용자 중심으로 문서를 정리. README.md를 시작점으로, 중복 제거, 개인 문서 분리.

## Design Decisions

- **대상 독자**: 외부 사용자 (이 repo를 보고 사용/이해하려는 사람)
- **개인 문서**: `private/` 폴더로 분리 (README에서 링크 안 함)
- **docs/ 평탄화**: `docs/user/` 제거, `docs/` 직하에 4개 사용자 문서
- **SSOT**: 설치/빠른시작은 QUICK_START.md가 SSOT, README.md는 3줄 요약만

## Final Structure

```
vault-intelligence/
├── README.md                    ← SSOT: 프로젝트 소개 + 문서 인덱스
├── CLAUDE.md                    ← Claude Code 전용 (CLI 참조 중심)
├── CONTRIBUTING.md              ← 그대로
├── SECURITY.md                  ← 그대로
├── CHANGELOG.md                 ← 그대로
├── docs/
│   ├── QUICK_START.md           ← docs/user/에서 이동
│   ├── USER_GUIDE.md            ← docs/user/에서 이동
│   ├── EXAMPLES.md              ← docs/user/에서 이동
│   └── TROUBLESHOOTING.md       ← docs/user/에서 이동
├── private/                     ← 개인 문서
│   ├── DEVELOPMENT.md
│   ├── AI-PRACTICE-SUMMARY.md
│   ├── DOCUMENTATION_AUDIT_REPORT.md
│   ├── dev/                     ← docs/dev/ 전체
│   ├── plans/                   ← docs/plans/ 전체
│   └── samples/                 ← samples/ 전체
└── archive/                     ← 그대로
```

## Changes

### File Moves

| 원본 | 대상 |
|------|------|
| `docs/user/QUICK_START.md` | `docs/QUICK_START.md` |
| `docs/user/USER_GUIDE.md` | `docs/USER_GUIDE.md` |
| `docs/user/EXAMPLES.md` | `docs/EXAMPLES.md` |
| `docs/user/TROUBLESHOOTING.md` | `docs/TROUBLESHOOTING.md` |
| `DEVELOPMENT.md` | `private/DEVELOPMENT.md` |
| `docs/AI-PRACTICE-SUMMARY.md` | `private/AI-PRACTICE-SUMMARY.md` |
| `docs/DOCUMENTATION_AUDIT_REPORT.md` | `private/DOCUMENTATION_AUDIT_REPORT.md` |
| `docs/dev/` (전체) | `private/dev/` |
| `docs/plans/` (전체) | `private/plans/` |
| `samples/` (전체) | `private/samples/` |

### Deletions

- `docs/README.md` — README.md 인덱스가 역할 대체
- `todo.md` — 4줄 스크래치 노트

### Content Edits

#### README.md
1. "빠른 시작" 섹션: 30줄 → 3줄 요약 + QUICK_START.md 링크
2. "문서 인덱스" 섹션: 4카테고리 → 2카테고리 (사용자 가이드 + 개발 참여)
3. "보안" 섹션: 20줄 → 2줄 요약 + SECURITY.md 링크
4. "기여하기" 섹션: 제거 (문서 인덱스에 이미 링크)

#### CLAUDE.md
1. 아키텍처 다이어그램 중복 제거 (README.md 참조로 교체)
2. 경로 참조 업데이트 (`docs/user/` → `docs/`)

#### docs/*.md (4개 사용자 문서)
1. 내비게이션 바 경로 업데이트 (`../../README.md` → `../README.md` 등)
