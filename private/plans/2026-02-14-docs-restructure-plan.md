# Documentation Restructure Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 외부 사용자 중심으로 문서 재구조화 — 중복 제거, 개인 문서 분리, README.md를 SSOT 시작점으로 정리

**Architecture:** 파일 이동(git mv) → 삭제(git rm) → 내용 수정(Edit) → 커밋 순서로 진행. 각 단계는 독립적으로 검증 가능.

**Tech Stack:** git mv, git rm, markdown editing

---

### Task 1: private/ 디렉토리 생성 및 파일 이동

**Files:**
- Create: `private/` directory
- Move: `DEVELOPMENT.md` → `private/DEVELOPMENT.md`
- Move: `docs/AI-PRACTICE-SUMMARY.md` → `private/AI-PRACTICE-SUMMARY.md`
- Move: `docs/DOCUMENTATION_AUDIT_REPORT.md` → `private/DOCUMENTATION_AUDIT_REPORT.md`
- Move: `docs/dev/` → `private/dev/`
- Move: `docs/plans/` → `private/plans/`
- Move: `samples/` → `private/samples/`

**Step 1: Create private/ directory and move files**

```bash
mkdir -p private
git mv DEVELOPMENT.md private/
git mv docs/AI-PRACTICE-SUMMARY.md private/
git mv docs/DOCUMENTATION_AUDIT_REPORT.md private/
git mv docs/dev private/
git mv samples private/
```

Note: `docs/plans/`는 .gitignore에 포함되어 있으므로 git mv 불가. 일반 mv 사용:

```bash
mv docs/plans private/
```

**Step 2: Verify moves**

```bash
ls private/
# Expected: DEVELOPMENT.md  AI-PRACTICE-SUMMARY.md  DOCUMENTATION_AUDIT_REPORT.md  dev/  plans/  samples/
ls docs/
# Expected: README.md  user/  (plans/ 없어야 함)
```

**Step 3: Commit**

```bash
git add -A && git commit -m "refactor(docs): 개인 문서를 private/ 폴더로 이동"
```

---

### Task 2: docs/user/ → docs/ 평탄화

**Files:**
- Move: `docs/user/QUICK_START.md` → `docs/QUICK_START.md`
- Move: `docs/user/USER_GUIDE.md` → `docs/USER_GUIDE.md`
- Move: `docs/user/EXAMPLES.md` → `docs/EXAMPLES.md`
- Move: `docs/user/TROUBLESHOOTING.md` → `docs/TROUBLESHOOTING.md`
- Delete: `docs/user/` (empty directory after moves)

**Step 1: Move files**

```bash
git mv docs/user/QUICK_START.md docs/QUICK_START.md
git mv docs/user/USER_GUIDE.md docs/USER_GUIDE.md
git mv docs/user/EXAMPLES.md docs/EXAMPLES.md
git mv docs/user/TROUBLESHOOTING.md docs/TROUBLESHOOTING.md
```

**Step 2: Verify**

```bash
ls docs/
# Expected: QUICK_START.md  USER_GUIDE.md  EXAMPLES.md  TROUBLESHOOTING.md  README.md
ls docs/user/ 2>&1
# Expected: No such file or directory (or empty)
```

**Step 3: Commit**

```bash
git add -A && git commit -m "refactor(docs): docs/user/ → docs/ 평탄화"
```

---

### Task 3: docs/README.md, todo.md 삭제

**Files:**
- Delete: `docs/README.md`
- Delete: `todo.md`

**Step 1: Delete files**

```bash
git rm docs/README.md
git rm todo.md
```

**Step 2: Verify**

```bash
ls docs/
# Expected: QUICK_START.md  USER_GUIDE.md  EXAMPLES.md  TROUBLESHOOTING.md (README.md 없음)
ls todo.md 2>&1
# Expected: No such file or directory
```

**Step 3: Commit**

```bash
git add -A && git commit -m "refactor(docs): 불필요한 docs/README.md, todo.md 삭제"
```

---

### Task 4: docs/*.md 내비게이션 바 경로 수정

**Files:**
- Modify: `docs/EXAMPLES.md:4` (nav bar)

현재 상태 분석:
- USER_GUIDE.md nav: `../README.md`, `../CLAUDE.md` → docs/에서 정확히 루트를 가리킴. 변경 불필요.
- TROUBLESHOOTING.md nav: `../README.md`, `../CLAUDE.md` → 동일. 변경 불필요.
- QUICK_START.md: nav bar 없음. 변경 불필요.
- EXAMPLES.md nav: `../../README.md`, `../../CLAUDE.md` → docs/에서는 `../README.md`, `../CLAUDE.md`로 변경 필요.

**Step 1: Fix EXAMPLES.md navigation bar**

`docs/EXAMPLES.md` line 4를 수정:

```
# Before:
- [🏠 프로젝트 홈](../../README.md) | [🚀 빠른 시작](QUICK_START.md) | [📚 사용자 가이드](USER_GUIDE.md) | **💡 실전 예제** | [🔧 문제 해결](TROUBLESHOOTING.md) | [⚙️ 개발자 가이드](../../CLAUDE.md)

# After:
- [🏠 프로젝트 홈](../README.md) | [🚀 빠른 시작](QUICK_START.md) | [📚 사용자 가이드](USER_GUIDE.md) | **💡 실전 예제** | [🔧 문제 해결](TROUBLESHOOTING.md) | [⚙️ 개발자 가이드](../CLAUDE.md)
```

**Step 2: Verify all nav bar links resolve correctly**

```bash
# From docs/ directory, these relative paths should point to existing files:
ls ../README.md    # root README
ls ../CLAUDE.md    # root CLAUDE.md
ls QUICK_START.md  # same directory
ls USER_GUIDE.md   # same directory
ls EXAMPLES.md     # same directory
ls TROUBLESHOOTING.md  # same directory
```

**Step 3: Commit**

```bash
git add docs/EXAMPLES.md && git commit -m "fix(docs): EXAMPLES.md 내비게이션 경로 수정"
```

---

### Task 5: README.md 정리 — 빠른 시작 섹션 축소

**Files:**
- Modify: `README.md:20-82` ("빠른 시작" 섹션)

**Step 1: Replace "빠른 시작" section (lines 20-82)**

Replace from `## 🚀 빠른 시작` through `> **참고:** 주 명령어...` with:

```markdown
## 🚀 빠른 시작

```bash
pipx install -e ~/git/vault-intelligence  # 설치
vis init --vault-path /path/to/vault       # 초기화
vis search "TDD"                            # 검색
```

상세한 설치 및 사용법은 **[5분 빠른 시작](docs/QUICK_START.md)**을 참조하세요.
```

**Step 2: Verify README renders correctly**

README.md의 "빠른 시작" 섹션이 3줄 코드 + 1줄 링크로 축소되었는지 확인.

**Step 3: Commit**

```bash
git add README.md && git commit -m "docs(readme): 빠른 시작 섹션을 3줄 요약으로 축소"
```

---

### Task 6: README.md 정리 — 문서 인덱스 섹션 재작성

**Files:**
- Modify: `README.md:84-155` ("문서 인덱스" 섹션)

**Step 1: Replace "문서 인덱스" section**

Replace from `## 📖 문서 인덱스` through `archive/ai-practice/` 설명까지를 아래로 교체:

```markdown
## 📖 문서

### 사용자 가이드

- **[5분 빠른 시작](docs/QUICK_START.md)** — 설치부터 첫 검색까지
- **[전체 사용자 가이드](docs/USER_GUIDE.md)** — 모든 기능 상세 매뉴얼
- **[실전 예제](docs/EXAMPLES.md)** — 상황별 구체적 예제
- **[문제 해결](docs/TROUBLESHOOTING.md)** — 자주 발생하는 문제와 해결법

### 개발 참여

- **[기여 가이드](CONTRIBUTING.md)** — 코딩 표준, PR 프로세스
- **[보안 정책](SECURITY.md)** — 민감정보 관리, 보안 검사
- **[변경 이력](CHANGELOG.md)** — 버전별 변경사항
- **[개발자 가이드](CLAUDE.md)** — CLI 참조, 시스템 아키텍처, API
```

**Step 2: Verify**

"설계 문서", "산출물" 카테고리가 제거되고 2개 카테고리만 남았는지 확인.

**Step 3: Commit**

```bash
git add README.md && git commit -m "docs(readme): 문서 인덱스를 사용자/개발 2카테고리로 정리"
```

---

### Task 7: README.md 정리 — 보안/기여 섹션 축소

**Files:**
- Modify: `README.md` ("기여하기" + "보안" 섹션)

**Step 1: Remove "기여하기" section**

`## 🤝 기여하기` 섹션 전체 삭제 (문서 인덱스에 CONTRIBUTING.md 링크가 이미 존재).

**Step 2: Replace "보안" section**

`## 🔒 보안` 섹션을 아래로 축소:

```markdown
## 🔒 보안

Pre-commit hook, Gitleaks 통합 등 자동 보안 검사 시스템을 갖추고 있습니다.
자세한 내용은 **[SECURITY.md](SECURITY.md)**를 참조하세요.
```

**Step 3: Verify and commit**

```bash
git add README.md && git commit -m "docs(readme): 보안/기여 섹션 축소 및 중복 제거"
```

---

### Task 8: CLAUDE.md 경로 업데이트

**Files:**
- Modify: `CLAUDE.md` (docs/user/ → docs/ 경로 참조)

**Step 1: Find and fix all docs/user/ references**

```bash
grep -n "docs/user/" CLAUDE.md
```

All occurrences of `docs/user/` → `docs/`:
- `docs/user/TROUBLESHOOTING.md` → `docs/TROUBLESHOOTING.md`
- `docs/user/USER_GUIDE.md` → `docs/USER_GUIDE.md`
- `docs/user/EXAMPLES.md` → `docs/EXAMPLES.md`
- `docs/user/QUICK_START.md` → `docs/QUICK_START.md`

Also fix references to moved/deleted files:
- `docs/README.md` 참조 제거
- `docs/dev/*` → `private/dev/*` (또는 참조 제거)
- `docs/AI-PRACTICE-SUMMARY.md` → 참조 제거
- `docs/DOCUMENTATION_AUDIT_REPORT.md` → 참조 제거

**Step 2: Verify no broken references remain**

```bash
grep -n "docs/user/\|docs/README\|docs/dev/\|docs/AI-PRACTICE\|docs/DOCUMENTATION" CLAUDE.md
# Expected: no matches
```

**Step 3: Commit**

```bash
git add CLAUDE.md && git commit -m "fix(claude-md): docs/user/ → docs/ 경로 업데이트"
```

---

### Task 9: 최종 검증

**Step 1: Check directory structure**

```bash
# Public docs (외부 사용자용)
ls README.md CLAUDE.md CONTRIBUTING.md SECURITY.md CHANGELOG.md
ls docs/QUICK_START.md docs/USER_GUIDE.md docs/EXAMPLES.md docs/TROUBLESHOOTING.md

# Private docs (개인용)
ls private/DEVELOPMENT.md private/AI-PRACTICE-SUMMARY.md private/DOCUMENTATION_AUDIT_REPORT.md
ls private/dev/ private/plans/ private/samples/

# Deleted files should not exist
ls docs/README.md docs/user/ todo.md 2>&1 | grep "No such file"
```

**Step 2: Verify no broken links in public docs**

```bash
# Check README.md links
grep -oP '\[.*?\]\((.*?)\)' README.md | grep -oP '\((.*?)\)' | tr -d '()' | while read link; do
  [[ "$link" == http* ]] && continue
  [[ "$link" == \#* ]] && continue
  [ -e "$link" ] || echo "BROKEN: $link"
done

# Check docs/ links (run from project root)
for f in docs/*.md; do
  dir=$(dirname "$f")
  grep -oP '\[.*?\]\((.*?)\)' "$f" | grep -oP '\((.*?)\)' | tr -d '()' | while read link; do
    [[ "$link" == http* ]] && continue
    [[ "$link" == \#* ]] && continue
    resolved="$dir/$link"
    [ -e "$resolved" ] || echo "BROKEN in $f: $link → $resolved"
  done
done
```

**Step 3: Verify git status is clean**

```bash
git status
# Expected: nothing to commit, working tree clean
```
