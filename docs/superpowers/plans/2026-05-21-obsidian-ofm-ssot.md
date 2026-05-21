# Obsidian OFM SSOT 단일화 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** vis CLI와 obsidian agent가 생성하는 모든 vault 문서가 OFM 규칙을 준수한다 — wikilink는 vault-relative 경로, frontmatter timestamp는 평문, 규칙 단일 출처(`ofm-rules.md`) 존재.

**Architecture:** ① `ofm-rules.md` (SSOT, LLM 소비) ② `src/utils/ofm.py` (Python 구현, vis 코드 소비) ③ obsidian agent 6개 + `shared-rules.md` (SSOT 참조 추가). Python은 마크다운을 못 읽으므로 별도 구현, 단위테스트로 SSOT와 동기화 고정.

**Tech Stack:** Python 3.10+, pytest, pathlib, `~/.claude/agents/*.md` (agent 정의), `~/.claude/commands/obsidian/` (skill 명령어)

---

## File Structure

| 파일 | 작업 | 책임 |
|------|------|------|
| `~/.claude/commands/obsidian/ofm-rules.md` | **신규** | OFM 전체 규약 SSOT — LLM 참조용 |
| `src/utils/ofm.py` | **신규** | `to_wikilink()` + `format_frontmatter_timestamp()` |
| `tests/test_ofm.py` | **신규** | ofm.py 단위테스트 |
| `src/features/topic_collector.py:423` | 수정 | `[[{doc.path}]]` → `ofm.to_wikilink()` |
| `src/features/moc_generator.py:608,628,657,682,695` | 수정 | `[[{doc.path}]]` → `ofm.to_wikilink()` |
| `src/features/related_docs_finder.py:136` | 수정 | `doc.title` → `ofm.to_wikilink(doc.path, …)` |
| `src/__main__.py:1216` (`save_clustering_results`) | 수정 | `doc.title` hack → `ofm.to_wikilink()`, `vault_path` 파라미터 추가 |
| `~/.claude/agents/youtube-obsidian-summarizer.md` | 수정 | `created_at: [[…]]` 버그 수정 + ofm-rules 참조 |
| `~/.claude/agents/article-obsidian-summarizer.md` | 수정 | ofm-rules 참조 추가 |
| `~/.claude/agents/obsidian-forward-related-injector.md` | 수정 | ofm-rules 참조 추가 |
| `~/.claude/agents/obsidian-related-notes-injector.md` | 수정 | ofm-rules 참조 추가 |
| `~/.claude/agents/obsidian-file-organizer.md` | 수정 | ofm-rules 참조 추가 |
| `~/.claude/agents/obsidian-tagger.md` | 수정 | ofm-rules 참조 추가 |
| `~/.claude/commands/obsidian/shared-rules.md` | 수정 | ofm-rules 참조 추가 |

---

### Task 1: `ofm-rules.md` SSOT 파일 생성

**Files:**
- Create: `~/.claude/commands/obsidian/ofm-rules.md`

- [ ] **Step 1: 파일 생성**

`~/.claude/commands/obsidian/ofm-rules.md` 전체 내용:

```markdown
# Obsidian Flavored Markdown (OFM) 규칙 — SSOT

이 파일은 vault 전체의 OFM 규약 단일 출처(SSOT)입니다.
- **LLM 소비자**: obsidian agent, shared-rules.md 가 이 파일을 텍스트 지침으로 참조한다.
- **코드 소비자**: `vis` Python 코드(`src/utils/ofm.py`)는 이 파일을 런타임 파싱하지 않는다.
  규칙을 코드로 구현하고, `tests/test_ofm.py`로 동기화를 고정한다.

---

## 1. Wikilink

**형식**: `[[folder/basename]]`  
- vault root 기준 상대경로, `.md` 확장자 없음  
- 절대경로 접두사(`/Users/...`) 금지  
- basename만 쓰면 vault 내 중복 시 모호 → vault-relative 경로 고정  
- Obsidian은 표시 시 basename만 보여줌 (경로는 소스뷰에서만 보임)  
- alias 형식: `[[folder/basename|표시텍스트]]`

**예시 (vis 출력 기준)**:
| 변환 전 (비표준) | 변환 후 (표준) |
|-----------------|---------------|
| `[[/Users/msbaek/DocumentsLocal/msbaek_vault/997-BOOKS/개발자로 살아남기.md]]` | `[[997-BOOKS/개발자로 살아남기]]` |
| `[[개발자로 살아남기]]` (basename만) | `[[997-BOOKS/개발자로 살아남기]]` |
| `[[Clean Code.md]]` | `[[997-BOOKS/Clean Code]]` |

---

## 2. Frontmatter (Properties)

```yaml
---
id: 원문 제목 (영문)
aliases:
  - 한국어 제목
tags:
  - domain/subdomain/leaf
author: author-name-lowercase-hyphenated
created_at: YYYY-MM-DD HH:MM
related: []
source: https://...
---
```

- `created_at` / `updated_at`: **평문 문자열** `YYYY-MM-DD HH:MM`. `[[YYYY-MM-DD HH:mm]]` 형식(wikilink) 금지 — Obsidian이 날짜 타입으로 인식 못 함.
- `tags`: 계층형 슬래시 구분 `domain/subdomain`, 모두 소문자.
- 임시 파일 면제: `*-progress.md`, WIP 산출물 등 frontmatter 의무 없음.

---

## 3. Callout

```markdown
> [!note] 선택적 제목
> 본문 내용

> [!warning]- 접힌 callout (기본값)
> 내용
```

공통 타입: `note`, `tip`, `warning`, `info`, `example`, `quote`, `bug`, `danger`.

---

## 4. Embed

```markdown
![[folder/document]]          전체 노트 임베드
![[folder/document#섹션]]      섹션 임베드
![[image.png|400]]            이미지 임베드 (width)
```

---

## 5. 태그

- 인라인: `#domain/subdomain`
- frontmatter `tags` 배열 권장
- 숫자로 시작 금지, 공백 금지

---

## 6. vis 적용 범위 (Python `ofm.py` 구현 대상)

| OFM 요소 | vis가 생성하는가 | `ofm.py` 구현 |
|----------|----------------|--------------|
| wikilink `[[...]]` | ✅ collect/moc/related/summarize | ✅ `to_wikilink()` |
| frontmatter timestamp | ✅ 일부 출력물 | ✅ `format_frontmatter_timestamp()` |
| callout `> [!type]` | ❌ | ❌ (YAGNI) |
| embed `![[...]]` | ❌ | ❌ (YAGNI) |
| 태그 | ❌ (vis tag는 Obsidian MCP 경유) | ❌ |

---

## 7. cross-repo 동기화 (Accepted Risk)

이 파일(SSOT)은 `~/.claude/commands/obsidian/`(user-global),
Python 코드는 `vault-intelligence/`(repo)에 존재한다.
자동 동기화 트리거 없음 — SSOT 규칙 변경 시 `ofm.py`/`test_ofm.py` 수동 갱신 필요.
규칙 변경 빈도가 낮아 수용 가능한 리스크.
```

- [ ] **Step 2: 파일이 생성됐는지 확인**

```bash
cat ~/.claude/commands/obsidian/ofm-rules.md | head -5
```

Expected: `# Obsidian Flavored Markdown (OFM) 규칙 — SSOT` 첫 줄

---

### Task 2: `src/utils/ofm.py` TDD — 실패 테스트 먼저

**Files:**
- Create: `tests/test_ofm.py`
- Create: `src/utils/ofm.py`

- [ ] **Step 1: 실패 테스트 작성**

`tests/test_ofm.py` 전체 내용:

```python
"""Tests for OFM utilities.

SSOT: ~/.claude/commands/obsidian/ofm-rules.md
Rule: wikilink is vault-relative path, no .md extension.
"""
import pytest
from datetime import datetime
from src.utils.ofm import to_wikilink, format_frontmatter_timestamp


VAULT = "/fake/vault"


# --- to_wikilink ---

def test_absolute_path_stripped_to_vault_relative():
    result = to_wikilink(f"{VAULT}/997-BOOKS/개발자로 살아남기.md", VAULT)
    assert result == "[[997-BOOKS/개발자로 살아남기]]"


def test_md_extension_removed():
    result = to_wikilink(f"{VAULT}/001-INBOX/TDD.md", VAULT)
    assert result == "[[001-INBOX/TDD]]"


def test_nested_directory():
    result = to_wikilink(f"{VAULT}/003-RESOURCES/oop/SOLID.md", VAULT)
    assert result == "[[003-RESOURCES/oop/SOLID]]"


def test_alias_appended():
    result = to_wikilink(f"{VAULT}/997-BOOKS/Clean Code.md", VAULT, alias="클린코드")
    assert result == "[[997-BOOKS/Clean Code|클린코드]]"


def test_already_vault_relative_with_extension():
    # path already relative to vault
    result = to_wikilink("001-INBOX/TDD.md", VAULT)
    assert result == "[[001-INBOX/TDD]]"


def test_no_extension_input():
    result = to_wikilink(f"{VAULT}/001-INBOX/TDD", VAULT)
    assert result == "[[001-INBOX/TDD]]"


def test_top_level_file():
    result = to_wikilink(f"{VAULT}/README.md", VAULT)
    assert result == "[[README]]"


# --- format_frontmatter_timestamp ---

def test_timestamp_fixed_datetime():
    dt = datetime(2026, 5, 21, 10, 30)
    assert format_frontmatter_timestamp(dt) == "2026-05-21 10:30"


def test_timestamp_no_arg_returns_string():
    ts = format_frontmatter_timestamp()
    import re
    assert re.match(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}$", ts)


def test_timestamp_not_wikilink():
    ts = format_frontmatter_timestamp(datetime(2026, 5, 21, 10, 30))
    assert "[[" not in ts
    assert "]]" not in ts
```

- [ ] **Step 2: 테스트 실패 확인 (ofm.py 없으므로 ImportError)**

```bash
cd /Users/msbaek/git/vault-intelligence && python -m pytest tests/test_ofm.py -v 2>&1 | head -20
```

Expected: `ImportError: cannot import name 'to_wikilink' from 'src.utils.ofm'` 또는 `ModuleNotFoundError`

- [ ] **Step 3: `src/utils/ofm.py` 구현**

```python
"""OFM (Obsidian Flavored Markdown) utilities for vis output.

SSOT: ~/.claude/commands/obsidian/ofm-rules.md
Wikilink rule: vault-relative path, no .md extension → [[folder/basename]]
Frontmatter timestamp rule: YYYY-MM-DD HH:MM (plain text, NOT wikilink).

Scope: only wikilink and frontmatter timestamp — what vis actually emits.
callout/embed helpers are NOT here (YAGNI).
"""

from datetime import datetime
from pathlib import Path


def to_wikilink(path: str, vault_path: str, alias: str = None) -> str:
    """Convert a file path to an Obsidian vault-relative wikilink.

    SSOT: ~/.claude/commands/obsidian/ofm-rules.md §1-Wikilink
    Input: absolute path or vault-relative path (with or without .md).
    Output: [[folder/basename]] or [[folder/basename|alias]].
    """
    p = Path(path)
    vault = Path(vault_path)

    # Strip vault root prefix if absolute path given
    try:
        rel = p.relative_to(vault)
    except ValueError:
        rel = p  # already relative — use as-is

    # Build wikilink path: strip .md suffix from final component
    parts = rel.parts
    stem = Path(parts[-1]).stem  # removes .md (or any extension)
    wikilink_path = "/".join(list(parts[:-1]) + [stem])

    if alias:
        return f"[[{wikilink_path}|{alias}]]"
    return f"[[{wikilink_path}]]"


def format_frontmatter_timestamp(dt: datetime = None) -> str:
    """Return a frontmatter-safe timestamp string.

    SSOT: ~/.claude/commands/obsidian/ofm-rules.md §2-Frontmatter
    Format: YYYY-MM-DD HH:MM  (plain text, NOT [[wikilink]]).
    """
    if dt is None:
        dt = datetime.now()
    return dt.strftime("%Y-%m-%d %H:%M")
```

- [ ] **Step 4: 테스트 통과 확인**

```bash
cd /Users/msbaek/git/vault-intelligence && python -m pytest tests/test_ofm.py -v
```

Expected: 모든 테스트 PASSED

- [ ] **Step 5: 커밋**

```bash
git add tests/test_ofm.py src/utils/ofm.py
git commit -m "feat(ofm): to_wikilink + format_frontmatter_timestamp 유틸 추가 (TDD)"
```

---

### Task 3: `topic_collector.py` wikilink 수정

**Files:**
- Modify: `src/features/topic_collector.py:423`

- [ ] **Step 1: 현재 상태 확인**

```bash
grep -n "\[\[{doc" src/features/topic_collector.py
```

Expected: `423:                    content += f"- **[[{doc.path}]]**"`

- [ ] **Step 2: import 추가 및 L423 수정**

파일 상단 import 블록에 추가:
```python
from src.utils.ofm import to_wikilink
```

L423 수정 (before → after):
```python
# before
content += f"- **[[{doc.path}]]**"

# after
content += f"- **{to_wikilink(doc.path, self.search_engine.vault_path)}**"
```

- [ ] **Step 3: 기존 테스트 통과 확인**

```bash
cd /Users/msbaek/git/vault-intelligence && python -m pytest tests/ -v --ignore=tests/test_server.py 2>&1 | tail -20
```

Expected: test_ofm.py 포함 기존 테스트 전부 PASSED (서버 테스트는 별도 데몬 필요)

- [ ] **Step 4: 커밋**

```bash
git add src/features/topic_collector.py
git commit -m "fix(topic_collector): wikilink를 vault-relative 경로로 수정"
```

---

### Task 4: `moc_generator.py` wikilink 수정

**Files:**
- Modify: `src/features/moc_generator.py:608,628,657,682,695`

- [ ] **Step 1: 수정 대상 확인**

```bash
grep -n "\[\[{doc\|rel\.source_doc\|rel\.target_doc" src/features/moc_generator.py
```

Expected (5개 라인):
```
608:                    lines.append(f"{i}. **[[{doc.path}]]**")
628:                        lines.append(f"- **[[{doc.path}]]**")
657:                        lines.append(f"- [[{doc.path}]]")
682:                    lines.append(f"- **[[{doc.path}]]** ({update_date})")
695:                    lines.append(f"- {strength_emoji} [[{rel.source_doc.path}]] ↔ [[{rel.target_doc.path}]] ({rel.strength:.2f})")
```

- [ ] **Step 2: import 추가 및 5개 라인 수정**

파일 상단 import 블록에 추가:
```python
from src.utils.ofm import to_wikilink
```

5개 라인 수정:

**L608** (before → after):
```python
# before
lines.append(f"{i}. **[[{doc.path}]]**")
# after
lines.append(f"{i}. **{to_wikilink(doc.path, self.search_engine.vault_path)}**")
```

**L628** (before → after):
```python
# before
lines.append(f"- **[[{doc.path}]]**")
# after
lines.append(f"- **{to_wikilink(doc.path, self.search_engine.vault_path)}**")
```

**L657** (before → after):
```python
# before
lines.append(f"- [[{doc.path}]]")
# after
lines.append(f"- {to_wikilink(doc.path, self.search_engine.vault_path)}")
```

**L682** (before → after):
```python
# before
lines.append(f"- **[[{doc.path}]]** ({update_date})")
# after
lines.append(f"- **{to_wikilink(doc.path, self.search_engine.vault_path)}** ({update_date})")
```

**L695** (before → after):
```python
# before
lines.append(f"- {strength_emoji} [[{rel.source_doc.path}]] ↔ [[{rel.target_doc.path}]] ({rel.strength:.2f})")
# after
vp = self.search_engine.vault_path
lines.append(f"- {strength_emoji} {to_wikilink(rel.source_doc.path, vp)} ↔ {to_wikilink(rel.target_doc.path, vp)} ({rel.strength:.2f})")
```

- [ ] **Step 3: 테스트 통과 확인**

```bash
cd /Users/msbaek/git/vault-intelligence && python -m pytest tests/ -v --ignore=tests/test_server.py 2>&1 | tail -20
```

Expected: PASSED

- [ ] **Step 4: 커밋**

```bash
git add src/features/moc_generator.py
git commit -m "fix(moc_generator): wikilink를 vault-relative 경로로 수정"
```

---

### Task 5: `related_docs_finder.py` wikilink 수정

**Files:**
- Modify: `src/features/related_docs_finder.py:136`

- [ ] **Step 1: 현재 상태 확인**

```bash
sed -n '133,142p' src/features/related_docs_finder.py
```

Expected: L136에 `link_text = f"[[{doc.title}]]"` 포함

- [ ] **Step 2: import 추가 및 L136 수정**

파일 상단 import 블록에 추가:
```python
from src.utils.ofm import to_wikilink
```

L136 수정 (before → after):
```python
# before
link_text = f"[[{doc.title}]]"

# after
link_text = to_wikilink(doc.path, self.search_engine.vault_path)
```

> 주의: `link_text`가 `[[...]]`으로 둘러싸인 문자열이어야 함. `to_wikilink()`는 `[[...]]`을 포함한 전체 wikilink를 반환하므로 별도 wrapping 불필요.

- [ ] **Step 3: 테스트 통과 확인**

```bash
cd /Users/msbaek/git/vault-intelligence && python -m pytest tests/ -v --ignore=tests/test_server.py 2>&1 | tail -20
```

Expected: PASSED

- [ ] **Step 4: 커밋**

```bash
git add src/features/related_docs_finder.py
git commit -m "fix(related_docs_finder): doc.title wikilink를 doc.path 기반으로 교체"
```

---

### Task 6: `save_clustering_results()` wikilink 수정

**Files:**
- Modify: `src/__main__.py:1216,1256`

- [ ] **Step 1: 현재 상태 확인**

```bash
sed -n '1216,1220p' src/__main__.py
sed -n '1253,1258p' src/__main__.py
```

Expected:
```
1216: def save_clustering_results(clustering_result, output_file: str, topic: Optional[str] = None):
...
1255:             title = doc.title.replace('[', '').replace(']', '')
1256:             content.append(f"{j}. [[{title}]]")
```

- [ ] **Step 2: 함수 시그니처에 `vault_path` 추가 + import + L1255-1256 수정**

**(a) 파일 상단 import 블록**에 추가 (다른 `from src.` import 근처):
```python
from src.utils.ofm import to_wikilink
```

**(b) L1216 함수 시그니처 수정** (before → after):
```python
# before
def save_clustering_results(clustering_result, output_file: str, topic: Optional[str] = None):
# after
def save_clustering_results(clustering_result, output_file: str, vault_path: str, topic: Optional[str] = None):
```

**(c) L1255-1256 수정** (before → after):
```python
# before
title = doc.title.replace('[', '').replace(']', '')  # 대괄호 제거
content.append(f"{j}. [[{title}]]")

# after
content.append(f"{j}. {to_wikilink(doc.path, vault_path)}")
```

**(d) L1169 호출부 수정** (before → after):
```python
# before
save_clustering_results(clustering_result, output_file, topic)
# after
save_clustering_results(clustering_result, output_file, search_engine.vault_path, topic)
```

- [ ] **Step 3: 테스트 통과 확인**

```bash
cd /Users/msbaek/git/vault-intelligence && python -m pytest tests/ -v --ignore=tests/test_server.py 2>&1 | tail -20
```

Expected: PASSED

- [ ] **Step 4: 커밋**

```bash
git add src/__main__.py
git commit -m "fix(summarize): save_clustering_results wikilink를 vault-relative 경로로 수정"
```

---

### Task 7: obsidian agent 및 shared-rules 업데이트

**Files:**
- Modify: `~/.claude/agents/youtube-obsidian-summarizer.md` (버그 수정 + ofm-rules 참조)
- Modify: `~/.claude/agents/article-obsidian-summarizer.md` (ofm-rules 참조)
- Modify: `~/.claude/agents/obsidian-forward-related-injector.md` (ofm-rules 참조)
- Modify: `~/.claude/agents/obsidian-related-notes-injector.md` (ofm-rules 참조)
- Modify: `~/.claude/agents/obsidian-file-organizer.md` (ofm-rules 참조)
- Modify: `~/.claude/agents/obsidian-tagger.md` (ofm-rules 참조)
- Modify: `~/.claude/commands/obsidian/shared-rules.md` (ofm-rules 참조)

---

#### Step 1: youtube-obsidian-summarizer.md — `created_at` 버그 수정

현재 L23:
```yaml
created_at: [[YYYY-MM-DD HH:mm]]
```
→ 수정 후:
```yaml
created_at: YYYY-MM-DD HH:MM
```

`~/.claude/agents/youtube-obsidian-summarizer.md`에서 해당 라인을 찾아 교체.

- [ ] **Step 1: 수정 전 확인**

```bash
grep -n "created_at" ~/.claude/agents/youtube-obsidian-summarizer.md
```

Expected: `23:created_at: [[YYYY-MM-DD HH:mm]]`

- [ ] **Step 2: 버그 수정**

`~/.claude/agents/youtube-obsidian-summarizer.md` L23:
```
# before
created_at: [[YYYY-MM-DD HH:mm]]
# after
created_at: YYYY-MM-DD HH:MM
```

- [ ] **Step 3: 수정 확인**

```bash
grep -n "created_at" ~/.claude/agents/youtube-obsidian-summarizer.md
```

Expected: `23:created_at: YYYY-MM-DD HH:MM` (no `[[`)

---

#### Step 2: 6개 agent에 `ofm-rules.md` 참조 추가

각 agent 파일에서 "## References" 섹션 또는 맨 끝에 다음을 추가한다.
섹션이 없으면 파일 끝에 추가:

```markdown
## OFM 규칙 참조

vault 문서 작성 시 `~/.claude/commands/obsidian/ofm-rules.md`를 따른다:
- wikilink: `[[folder/basename]]` (vault-relative, .md 없음)
- frontmatter timestamp: `YYYY-MM-DD HH:MM` (평문, wikilink 아님)
```

**대상 파일 목록 (순서대로 수정)**:

- [ ] **Step 4: youtube-obsidian-summarizer.md 참조 추가**

```bash
echo '
## OFM 규칙 참조

vault 문서 작성 시 `~/.claude/commands/obsidian/ofm-rules.md`를 따른다:
- wikilink: `[[folder/basename]]` (vault-relative, .md 없음)
- frontmatter timestamp: `YYYY-MM-DD HH:MM` (평문, wikilink 아님)
' >> ~/.claude/agents/youtube-obsidian-summarizer.md
```

- [ ] **Step 5: article-obsidian-summarizer.md 참조 추가**

```bash
echo '
## OFM 규칙 참조

vault 문서 작성 시 `~/.claude/commands/obsidian/ofm-rules.md`를 따른다:
- wikilink: `[[folder/basename]]` (vault-relative, .md 없음)
- frontmatter timestamp: `YYYY-MM-DD HH:MM` (평문, wikilink 아님)
' >> ~/.claude/agents/article-obsidian-summarizer.md
```

- [ ] **Step 6: obsidian-forward-related-injector.md 참조 추가**

```bash
echo '
## OFM 규칙 참조

vault 문서 작성 시 `~/.claude/commands/obsidian/ofm-rules.md`를 따른다:
- wikilink: `[[folder/basename]]` (vault-relative, .md 없음)
- frontmatter timestamp: `YYYY-MM-DD HH:MM` (평문, wikilink 아님)
' >> ~/.claude/agents/obsidian-forward-related-injector.md
```

- [ ] **Step 7: obsidian-related-notes-injector.md 참조 추가**

```bash
echo '
## OFM 규칙 참조

vault 문서 작성 시 `~/.claude/commands/obsidian/ofm-rules.md`를 따른다:
- wikilink: `[[folder/basename]]` (vault-relative, .md 없음)
- frontmatter timestamp: `YYYY-MM-DD HH:MM` (평문, wikilink 아님)
' >> ~/.claude/agents/obsidian-related-notes-injector.md
```

- [ ] **Step 8: obsidian-file-organizer.md 참조 추가**

```bash
echo '
## OFM 규칙 참조

vault 문서 작성 시 `~/.claude/commands/obsidian/ofm-rules.md`를 따른다:
- wikilink: `[[folder/basename]]` (vault-relative, .md 없음)
- frontmatter timestamp: `YYYY-MM-DD HH:MM` (평문, wikilink 아님)
' >> ~/.claude/agents/obsidian-file-organizer.md
```

- [ ] **Step 9: obsidian-tagger.md 참조 추가**

```bash
echo '
## OFM 규칙 참조

vault 문서 작성 시 `~/.claude/commands/obsidian/ofm-rules.md`를 따른다:
- wikilink: `[[folder/basename]]` (vault-relative, .md 없음)
- frontmatter timestamp: `YYYY-MM-DD HH:MM` (평문, wikilink 아님)
' >> ~/.claude/agents/obsidian-tagger.md
```

---

#### Step 3: `shared-rules.md` 참조 추가

- [ ] **Step 10: shared-rules.md 첫 줄 직후에 ofm-rules 참조 삽입**

`~/.claude/commands/obsidian/shared-rules.md` 파일 상단에서 첫 섹션 시작 전에 추가:

```markdown
> **OFM 규칙**: vault 문서 작성 시 `~/.claude/commands/obsidian/ofm-rules.md`를 따른다.
> wikilink: `[[folder/basename]]` / frontmatter timestamp: `YYYY-MM-DD HH:MM` (평문).
```

이 두 줄을 파일 첫 번째 `##` 헤딩 바로 위에 삽입한다.

- [ ] **Step 11: 최종 확인**

```bash
grep -l "ofm-rules" ~/.claude/agents/youtube-obsidian-summarizer.md \
  ~/.claude/agents/article-obsidian-summarizer.md \
  ~/.claude/agents/obsidian-forward-related-injector.md \
  ~/.claude/agents/obsidian-related-notes-injector.md \
  ~/.claude/agents/obsidian-file-organizer.md \
  ~/.claude/agents/obsidian-tagger.md \
  ~/.claude/commands/obsidian/shared-rules.md
```

Expected: 7개 파일 모두 출력됨

- [ ] **Step 12: 전체 테스트 마지막 확인**

```bash
cd /Users/msbaek/git/vault-intelligence && python -m pytest tests/test_ofm.py -v
```

Expected: 9개 테스트 PASSED

- [ ] **Step 13: 커밋**

```bash
git add src/ tests/test_ofm.py
git commit -m "feat(ofm-ssot): SSOT 파일 생성, vis 호출처 교체, agent 참조 추가"
```

> Note: `~/.claude/` 파일들은 git-tracked 아님 — vis repo 커밋 대상 아님. vis Python 변경만 커밋.

---

## Self-Review

### 1. Spec Coverage

| Spec 요구사항 | 커버 Task |
|--------------|-----------|
| Goal #1: wikilink `[[folder/basename]]` 형식 | Task 2(ofm.py) + Task 3-6(call sites) |
| Goal #2: frontmatter timestamp 일관성 | Task 2(format_frontmatter_timestamp) + Task 7(youtube 버그) |
| Goal #3: SSOT(`ofm-rules.md`) 존재, 양쪽 참조 | Task 1(SSOT) + Task 7(agent 참조) |
| Goal #4: `created_at: [[...]]` 문법 오류 수정 | Task 7 Step 1-2 |
| `topic_collector.py` L423 | Task 3 |
| `moc_generator.py` L608/628/657/682/695 | Task 4 |
| `related_docs_finder.py` L136 | Task 5 |
| `save_clustering_results()` L1256 | Task 6 |
| 6개 agent + shared-rules.md | Task 7 |

### 2. Placeholder Scan

- 모든 step에 실제 코드·명령어 포함됨 ✅
- "TBD", "TODO" 없음 ✅

### 3. Type Consistency

- `to_wikilink(path, vault_path, alias=None) -> str` — Task 2 정의, Task 3-6 모두 동일 시그니처 사용 ✅
- `self.search_engine.vault_path` — Task 3/4/5에서 일관 사용 ✅
- Task 6에서 `save_clustering_results(..., vault_path: str, ...)` 시그니처 변경 후 호출부(L1169)도 함께 수정 ✅
