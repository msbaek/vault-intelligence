# vis-backlink Reverse Update Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 새 Obsidian 문서 A 생성 시, A 의 vis Top 5 기존 문서 각각의 `## Related Notes` 섹션을 **full refresh** 하는 역방향 compounding 파이프라인을 구축한다. 첫 실행은 sync dry-run, 이후는 background subagent 비동기 실행. 메인 Claude blocking 은 2초 이내.

**Architecture:** CLAUDE.md 훅 확장(`<when-creating-obsidian-document>`)으로 forward 절차 뒤에 backward 블록을 추가한다. vis daemon 은 read-only, 실제 파일 수정은 Claude 도구(Read/MultiEdit) + background subagent 가 수행. 상태는 `~/.claude/state/vis-backlink/{active,history}/` 의 per-job JSON 으로 추적. 별도 상태 조회 skill `vis-backlink-status` 를 독립 신설.

**Tech Stack:** LLM 절차 지시문(CLAUDE.md, SKILL.md 텍스트) · Claude Code 도구(Read, MultiEdit, Bash, Agent) · vis daemon HTTP(`localhost:8741`) · 샌드박스 vault(`/tmp/vault-test/`) + test vis daemon(`localhost:8742`).

**Implementation Strategy (중요 결정):** 파서·필터·state I/O 등의 결정성 로직을 Python 유틸로 추출하지 않고 **LLM 절차 지시문으로 직접 수행**한다. 근거:
- Spec C1/C2 가 훅 메인·Subagent 가 Claude 도구로 직접 수행하는 구조를 전제
- 훅의 self-contained 성질 유지(외부 Python 의존 없음)
- 결정성은 T2 샌드박스 시나리오로 검증
- v2 에서 파서 재사용 요구가 명확해지면 그때 `scripts/related_notes_parser.py` 로 추출

> ⚠️ **Risk R3 — VAULT_ROOT 환경변수 미지원**: 훅이 환경변수 기반 vault 전환을 지원하지 않으므로 Task 1~12 의 샌드박스 검증은 "수동 시뮬레이션" 형태(훅 텍스트를 따라가며 `/tmp/vault-test/` 경로 직접 호출). Task 4 진입 시 `VAULT_ROOT` 분기를 Task 2 훅에 추가할지 결정해야 한다. 추가하면 Task 2 로 루프백 필요.

**Spec 참조:** `docs/superpowers/specs/2026-04-15-vis-backlink-reverse-update-design.md` (approved 2026-04-15).

**Failure Conditions (전체 plan):**
- 기존 `## Related Notes` 섹션 포맷 파괴 (스펙 C3)
- 중복 링크 삽입
- 경쟁 조건으로 파일 손상
- forward 작업 blocking 2초 초과
- production `.trusted` 없이 비동기 dispatch 가 발생

---

## File Structure

**Create** (vault-intelligence repo):
- `tests/fixtures/sandbox_vault/` — 미니 vault (정상/일탈 md 10개)
- `tests/fixtures/sandbox_vault/README.md` — fixture 파일 카탈로그
- `tests/fixtures/sandbox_vault/.obsidian/` — Obsidian 설정 더미 (vis 인덱싱 호환)
- `scripts/start-test-vis.sh` — test daemon runner (`port=8742`, `VIS_VAULT_PATH=/tmp/vault-test`)
- `scripts/sync-sandbox.sh` — fixture → `/tmp/vault-test/` 초기화
- `tests/scenarios/01-parser.md` — T2.1 파서 시나리오 체크리스트
- `tests/scenarios/02-regression-forward.md` — T2.8
- `tests/scenarios/03-flow1-dryrun.md` — T2.2
- `tests/scenarios/04-flow2-async.md` — T2.3
- `tests/scenarios/05-flow3-sequential.md` — T2.4
- `tests/scenarios/06-flow4-errors.md` — T2.5
- `tests/scenarios/07-skill-status.md` — T2.6
- `tests/scenarios/08-bootstrap-mode.md` — T2.7
- `tests/scenarios/09-performance.md` — T3
- `tests/scenarios/10-production-rollout.md` — T5

**Create** (global, `~/.claude/`):
- `~/.claude/skills/vis-backlink-status/SKILL.md` (C11)
- `~/.claude/state/vis-backlink/{active,history}/` 는 훅이 런타임 부트스트랩하므로 plan 상 create 대상 아님

**Modify** (global):
- `~/.claude/CLAUDE.md:265-272` — `<when-creating-obsidian-document>` 블록 확장

**Non-goal (이 plan 에서 만들지 않음)**:
- Python 파서/필터 유틸 → v2 후보
- vault 전체 backfill 스크립트 → v2a
- file-level mutex → v2c
- 병렬 subagent → v2d

---

## Task 1 — Sandbox vault fixture 구축

**Why this matters:** 이후 모든 T2 시나리오의 기반. production vault 를 건드리지 않고 훅 동작을 반복 검증할 수 있어야 한다. 일탈 케이스(image link, multi-line desc, 주석)를 포함한 고정 fixture 가 있어야 파서 회귀가 가능.

**Files:**
- Create: `tests/fixtures/sandbox_vault/README.md`
- Create: `tests/fixtures/sandbox_vault/001-INBOX/.gitkeep`
- Create: `tests/fixtures/sandbox_vault/003-RESOURCES/foo.md`
- Create: `tests/fixtures/sandbox_vault/003-RESOURCES/bar.md`
- Create: `tests/fixtures/sandbox_vault/003-RESOURCES/baz.md`
- Create: `tests/fixtures/sandbox_vault/003-RESOURCES/deviant-multiline.md`
- Create: `tests/fixtures/sandbox_vault/003-RESOURCES/deviant-image.md`
- Create: `tests/fixtures/sandbox_vault/003-RESOURCES/no-section.md`
- Create: `tests/fixtures/sandbox_vault/997-BOOKS/quux.md`
- Create: `tests/fixtures/sandbox_vault/work-log/2026-04-14.md`
- Create: `tests/fixtures/sandbox_vault/ATTACHMENTS/dummy-image.md`
- Create: `tests/fixtures/sandbox_vault/.obsidian/app.json`
- Create: `scripts/sync-sandbox.sh`
- Create: `scripts/start-test-vis.sh`

- [ ] **Step 1.1: Create fixture README with exhaustive catalogue**

Write `tests/fixtures/sandbox_vault/README.md`:

```markdown
# Sandbox Vault Fixture

vis-backlink reverse update 훅 검증용 미니 vault. `scripts/sync-sandbox.sh` 로 `/tmp/vault-test/` 에 복사된다.

## 파일 카탈로그

| 경로 | 역할 | Related Notes 섹션 | 일탈 케이스 |
|---|---|---|---|
| `003-RESOURCES/foo.md` | 정상 A 후보 | 있음 (2 links) | — |
| `003-RESOURCES/bar.md` | 정상 B 후보 | 있음 (3 links) | — |
| `003-RESOURCES/baz.md` | 정상 C 후보 | 있음 (1 link) | — |
| `003-RESOURCES/deviant-multiline.md` | 파서 skip 대상 | 있음 (multi-line desc) | multi-line description |
| `003-RESOURCES/deviant-image.md` | 필터 대상 | 있음 | `![[pic.png]]` 링크 포함 |
| `003-RESOURCES/no-section.md` | bootstrap 대상 | 없음 | — |
| `997-BOOKS/quux.md` | 정상 후보 | 없음 | — |
| `work-log/2026-04-14.md` | 자동 제외 대상 | 없음 | `work-log/**` |
| `ATTACHMENTS/dummy-image.md` | 자동 제외 대상 | 없음 | `ATTACHMENTS/**` |
| `001-INBOX/.gitkeep` | A 생성 위치 | — | — |

## 재생성

```bash
./scripts/sync-sandbox.sh          # /tmp/vault-test/ 재생성 (rm -rf 후 cp)
./scripts/start-test-vis.sh        # test daemon 실행 (port 8742)
```
```

- [ ] **Step 1.2: Create content for normal fixture files**

Write `tests/fixtures/sandbox_vault/003-RESOURCES/foo.md`:

```markdown
---
title: Foo Concept
tags: [concept/foo]
---

# Foo

Foo 는 샌드박스용 정상 문서. bar, baz 와 연결되어 있다.

## Related Notes

- [[003-RESOURCES/bar]] — bar 와 상호 연결된 샌드박스 기준 문서
- [[003-RESOURCES/baz]] — 요약 대상으로 활용
```

Write `tests/fixtures/sandbox_vault/003-RESOURCES/bar.md`:

```markdown
---
title: Bar Concept
tags: [concept/bar]
---

# Bar

bar 는 foo, baz, quux 와 연결된 허브 문서.

## Related Notes

- [[003-RESOURCES/foo]] — foo 쪽으로 참조
- [[003-RESOURCES/baz]] — baz 요약 연결
- [[997-BOOKS/quux]] — 책 레퍼런스
```

Write `tests/fixtures/sandbox_vault/003-RESOURCES/baz.md`:

```markdown
---
title: Baz Concept
tags: [concept/baz]
---

# Baz

baz 는 foo 하나와만 강하게 연결된다.

## Related Notes

- [[003-RESOURCES/foo]] — foo 의 요약 판본
```

Write `tests/fixtures/sandbox_vault/003-RESOURCES/no-section.md`:

```markdown
---
title: No Section Yet
tags: [concept/no-section]
---

# No Section

이 문서는 Related Notes 섹션이 없는 상태. bootstrap_mode 테스트용.

본문은 아직 짧다.
```

Write `tests/fixtures/sandbox_vault/997-BOOKS/quux.md`:

```markdown
---
title: Quux Reading Notes
tags: [book/quux]
---

# Quux

책 참고용 문서. bar 와 연결된다.

본문 요약...
```

- [ ] **Step 1.3: Create deviant fixture files (parser skip 대상)**

Write `tests/fixtures/sandbox_vault/003-RESOURCES/deviant-multiline.md`:

```markdown
---
title: Deviant Multiline
---

# Deviant Multiline

파서 skip 회귀 케이스: Related Notes 설명이 여러 줄.

## Related Notes

- [[003-RESOURCES/foo]] — foo 쪽으로
  추가 설명 두 번째 줄이 들여쓰기로 이어짐
- [[003-RESOURCES/bar]] — bar
```

Write `tests/fixtures/sandbox_vault/003-RESOURCES/deviant-image.md`:

```markdown
---
title: Deviant Image
---

# Deviant Image

파서 skip 회귀 케이스: 이미지 링크가 섹션 안에 섞임.

## Related Notes

- [[003-RESOURCES/foo]] — foo 정상
- ![[diagram.png]]
- [[003-RESOURCES/bar]] — bar 정상
```

- [ ] **Step 1.4: Create auto-excluded fixtures**

Write `tests/fixtures/sandbox_vault/work-log/2026-04-14.md`:

```markdown
---
title: Work Log 2026-04-14
tags: [work-log]
---

# 2026-04-14 Daily

- foo 관련 작업 진행
- bar 리뷰 완료
```

Write `tests/fixtures/sandbox_vault/ATTACHMENTS/dummy-image.md`:

```markdown
---
title: Attachment placeholder
---

ATTACHMENTS 경로 자동 제외 테스트용. 실제로는 바이너리지만 md 로 모사.
```

Write `tests/fixtures/sandbox_vault/.obsidian/app.json`:

```json
{
  "attachmentFolderPath": "ATTACHMENTS",
  "alwaysUpdateLinks": true
}
```

Create empty marker: `tests/fixtures/sandbox_vault/001-INBOX/.gitkeep` (empty file).

- [ ] **Step 1.5: Write sync-sandbox.sh**

Write `scripts/sync-sandbox.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC="$REPO_ROOT/tests/fixtures/sandbox_vault"
DST="/tmp/vault-test"

if [[ ! -d "$SRC" ]]; then
  echo "ERROR: sandbox fixture missing at $SRC" >&2
  exit 1
fi

rm -rf "$DST"
cp -a "$SRC" "$DST"
echo "sandbox synced: $DST"
```

Then: `chmod +x scripts/sync-sandbox.sh`.

- [ ] **Step 1.6: Write start-test-vis.sh**

Write `scripts/start-test-vis.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VAULT="${VIS_VAULT_PATH:-/tmp/vault-test}"
PORT="${VIS_TEST_PORT:-8742}"

if [[ ! -d "$VAULT" ]]; then
  "$REPO_ROOT/scripts/sync-sandbox.sh"
fi

echo "starting test vis daemon on :$PORT against $VAULT"
VIS_VAULT_PATH="$VAULT" \
  python -m src serve --port "$PORT" --no-watch
```

Then: `chmod +x scripts/start-test-vis.sh`.

- [ ] **Step 1.7: Verify fixture**

Run:
```bash
./scripts/sync-sandbox.sh
find /tmp/vault-test -name '*.md' -type f | sort
```

Expected output (10 md 파일):
```
/tmp/vault-test/003-RESOURCES/bar.md
/tmp/vault-test/003-RESOURCES/baz.md
/tmp/vault-test/003-RESOURCES/deviant-image.md
/tmp/vault-test/003-RESOURCES/deviant-multiline.md
/tmp/vault-test/003-RESOURCES/foo.md
/tmp/vault-test/003-RESOURCES/no-section.md
/tmp/vault-test/997-BOOKS/quux.md
/tmp/vault-test/ATTACHMENTS/dummy-image.md
/tmp/vault-test/README.md
/tmp/vault-test/work-log/2026-04-14.md
```

- [ ] **Step 1.8: Verify test daemon boot (smoke)**

Run in background:
```bash
./scripts/start-test-vis.sh &
TEST_VIS_PID=$!
sleep 5
curl -sf http://localhost:8742/health
kill $TEST_VIS_PID
```

Expected: `{"status":"ok",...}` JSON. Port 8742 에서 daemon 응답.

If daemon boot 이 실패하면 `python -m src --help` 로 현 CLI 지원 여부 확인. 불일치 시 `src/__main__.py` 의 `serve` 커맨드 존재 여부를 Grep 해 보고 필요 시 이 step 을 Task 1 re-scope 대상으로 표시 (추가 유틸 필요).

- [ ] **Step 1.9: Commit**

```bash
cd ~/git/vault-intelligence
git add tests/fixtures/sandbox_vault scripts/sync-sandbox.sh scripts/start-test-vis.sh
git commit -m "test(sandbox): add vault fixture and test vis launcher for vis-backlink"
```

**Success criteria:** 10개 md 파일이 `/tmp/vault-test/` 에 나타나고, test daemon 이 port 8742 에서 health 응답.

---

## Task 2 — CLAUDE.md backward 블록 확장 (C1~C9)

> ⚠️ **Risk R1 — LLM 절차 지시문 복잡성 + 루프백 정책**: C3 파서 규칙이 훅 텍스트로만 존재해 유지보수는 텍스트 수정으로만 가능. **Task 4(T2.1 파서 시나리오)에서 케이스 누락이 발견되면 이 Task 로 루프백하여 규칙 재작성**. 실행 에이전트는 Task 4 실패 시 자동으로 Task 2 수정 → Task 4 재실행 사이클을 한 번 허용한다. 두 번째 실패는 사용자에게 에스컬레이션.

**Why this matters:** 본 기능의 오케스트레이터. LLM 이 읽고 그대로 수행하므로 **절차·조건·에러 처리가 명시적**이어야 한다. 빠진 분기 하나가 Flow 4 에러로 이어진다.

**Files:**
- Modify: `~/.claude/CLAUDE.md:265-272` (전체 블록 교체)

- [ ] **Step 2.1: Read current block for precise Edit**

Run (reference only, not a modification):
```
Read ~/.claude/CLAUDE.md offset 265 limit 10
```

Expected current content (lines 265-272, verified 2026-04-15):
```
<when-creating-obsidian-document>
Obsidian 문서를 생성하거나 정리한 후, vis daemon HTTP API로 관련 문서를 검색하여 Related Notes 섹션을 추가한다.
1. `curl -s --get --data-urlencode "query=핵심 키워드" "http://localhost:8741/search?search_method=hybrid&rerank=true&top_k=10"` 실행 (서버 미실행 시 fallback: `vis search`)
2. 자기 자신, daily notes 제외하고 관련도 높은 후보 선별
3. 상위 5개를 자동 추가 (사용자가 inbox 검토 시 수정하므로 별도 승인 불필요)
4. 문서 하단에 `## Related Notes` 섹션으로 추가 (각 링크에 한 줄 맥락 설명 포함)
5. frontmatter `related:` 필드는 명시적 요청 시에만 업데이트
</when-creating-obsidian-document>
```

- [ ] **Step 2.2: Replace block with extended forward + backward structure**

Use Edit tool on `~/.claude/CLAUDE.md`:

**old_string** (현재 CLAUDE.md 실제 내용, 2026-04-26 확인):
```
<when-creating-obsidian-document>
After creating: `curl -s --get --data-urlencode "query=키워드" "http://localhost:8741/search?search_method=hybrid&rerank=true&top_k=10"` (fallback: `vis search`). Add top 5 as `## Related Notes` (exclude self/daily, 1-line context each). No `related:` frontmatter unless asked.
</when-creating-obsidian-document>
```

**new_string** (forward + backward 통합):
```
<when-creating-obsidian-document>
Obsidian 문서 A 를 생성하거나 정리한 후 수행한다. forward 는 기존과 동일, backward 는 신규.

### Forward (A 자체에 Related Notes 추가)

1. `curl -s --get --data-urlencode "query=핵심 키워드" "http://localhost:8741/search?search_method=hybrid&rerank=true&top_k=10"` 실행 (서버 미실행 시 fallback: `vis search`)
2. 자기 자신, daily notes 제외하고 관련도 높은 후보 선별
3. 상위 5개를 자동 추가 (사용자가 inbox 검토 시 수정하므로 별도 승인 불필요)
4. 문서 하단에 `## Related Notes` 섹션으로 추가 (각 링크에 한 줄 맥락 설명 포함)
5. frontmatter `related:` 필드는 명시적 요청 시에만 업데이트

### Backward (A 의 Top 5 각각에 대해 역방향 Related Notes full refresh)

**Config (변경 시 이 블록만 수정):**
- `top_k`: 5
- `bootstrap_mode`: `"minimal"` (없는 섹션은 A 링크 1 줄만 신설. `"full"` 로 전환 시 Top 5 전체 신설)
- `exclude_patterns`: `["work-log/*.md", "ATTACHMENTS/**", "<A-path>", "frontmatter.draft == true"]`
- `first_run_policy`: `"sync_dryrun_once"` (`.trusted` 없으면 강제 동기 dry-run)
- `concurrency`: `"sequential"` (active/*.json polling)
- `state_dir`: `~/.claude/state/vis-backlink/`
- `log_path`: `~/.claude/logs/vis-backlink-YYYYMMDD.log` (자동 rollover, append-only)

**사전 가드 (모두 통과해야 backward 진입):**

1. git dirty tree 체크: `cd <vault_root> && git status --porcelain` 결과가 비어있지 않으면 `ENV_DIRTY_TREE` → backward 스킵, forward 는 유지, 사용자에게 "vault dirty → backward 생략" 인라인 고지.
2. `state_dir` 부트스트랩: `mkdir -p ~/.claude/state/vis-backlink/{active,history}` (이미 있으면 noop).
3. 동시성 체크: `ls ~/.claude/state/vis-backlink/active/*.json 2>/dev/null` 에 결과가 있으면 2초 주기 polling. 5초 경과 후에도 대기 중이면 "선행 backward job 대기 중" 1회 알림. `phase in {completed, failed, partial_failure, crashed}` 가 되면 해제.

**분기 (.trusted 마커로 1회 gate):**

- `.trusted` 부재 → 동기 dry-run (Flow 1). 아래 "Dry-run 프로시저" 수행.
- `.trusted` 존재 → 비동기 dispatch (Flow 2). 아래 "Async dispatch 프로시저" 수행.

**Dry-run 프로시저 (Flow 1, 첫 실행 한 번):**

1. vis `/search` 호출: `curl -s --get --data-urlencode "query=<A 핵심 키워드>" "http://localhost:8741/search?search_method=hybrid&rerank=true&top_k=5"`
2. 응답의 각 후보 X 에 대해 `exclude_patterns` 적용. A 자신은 무조건 제외.
3. 각 X 에 대해 "X 처리 서브루틴" 을 **드라이런 모드** 로 수행 (실제 쓰기 없이 diff 계산).
4. 대화 내 C6 포맷으로 diff 출력:
   ```
   역방향 Related Notes 업데이트 미리보기
   새 문서: A = <A_path>
   역방향 대상 (vis Top 5, 자동 제외 적용 후):
     [1] B = ... (섹션 있음)
     [2] C = ... (섹션 없음 → bootstrap minimal)
     [3] D = ... (제외: work-log/**)
     ...
   실제 수정 대상: B, C
   B 변경안 diff: ...
   [계속 적용 / 취소 / 선택 적용]
   ```
5. 사용자 승인 → MultiEdit 순차 적용 → `touch ~/.claude/state/vis-backlink/.trusted`.
6. 사용자 거부 → 변경 없음, `.trusted` 생성 안 함. 다음 새 문서 생성 시 다시 dry-run.

**Async dispatch 프로시저 (Flow 2, `.trusted` 이후):**

1. `job_id=$(date +%Y%m%d-%H%M%S)-$(basename A .md)` 형태로 생성.
2. `~/.claude/state/vis-backlink/active/<job_id>.json` 에 초기 state 기록 (atomic: tmp → rename):
   ```json
   {"job_id": "...", "source": "<A_path>", "started_at": "<ISO8601>",
    "updated_at": "<ISO8601>", "phase": "dispatched",
    "subagent_name": "vis-backlink-<hash>",
    "progress": {"total": 0, "done": 0, "failed": 0},
    "targets": [],
    "log_path": "~/.claude/logs/vis-backlink-<date>.log"}
   ```
3. Agent 도구로 subagent dispatch:
   - `subagent_type`: `"general-purpose"`
   - `name`: `"vis-backlink-<short-hash>"`
   - `run_in_background`: `true`
   - `prompt`: "X 처리 서브루틴" 섹션 전체 + config + state JSON 경로 + 대상 후보 (Top 5, 제외 적용 후) 를 인용. subagent 는 반드시 (a) atomic state rewrite, (b) C3 파서 규칙, (c) 에러 카탈로그 대응 수행.
4. 메인 Claude 는 즉시 해제. 사용자는 다음 forward 작업 가능. 2초 이내 해제되어야 함 (T3).

**X 처리 서브루틴 (C2, subagent 또는 dry-run 메인이 수행):**

입력: `X_path`. 출력: X 수정 또는 skip 이유 + state update.

1. `Read X_path` → 원본 전체.
2. C3 파서로 섹션 분해: `(before, related_lines, after)`.
   - 섹션 시작: `^## Related Notes\s*$`
   - 섹션 종료: 다음 `^## ` 또는 EOF
   - 각 줄 문법: `^-\s+\[\[(?P<link>[^\]]+)\]\](\s+—\s+(?P<desc>.+))?$`
   - 일탈 줄 (멀티라인 desc, 주석, `![[...]]` 이미지 링크, 확장자 있는 링크): **해당 파일 skip**. state `targets[X].status="skipped_parse"`, 사유 기록.
3. vis `/search` 호출 (`top_k=5`, `rerank=true`) → X 의 최신 Top 5. `exclude_patterns` 적용 (X 자신은 무조건 제외).
4. 각 링크 L 에 대해 설명(desc) 결정:
   - L 이 기존 related_lines 에 있음 → 기존 desc 보존
   - L 이 신규 → LLM 생성 (1-2 문장 맥락 설명). 실패 → vis 응답의 snippet fallback, state 에 `llm_desc_fail` 플래그.
5. `bootstrap_mode=="minimal"` and 기존 섹션 없음 → new lines = `[- [[A]] — <A 요약>]` 단 1줄. `"full"` → Top 5 전체.
6. `assembled = before + "## Related Notes\n\n" + "\n".join(new_lines) + "\n" + after`.
7. `MultiEdit(X_path, old=원본, new=assembled)`.
8. state atomic update: `targets[X].status="done"`, `duration_ms`, `changes={added, preserved, removed}`.

**완료 · 정리:**

- 모든 targets 처리 완료 → state `phase="completed"`, `mv active/<id>.json history/<id>.json`.
- 일부 실패 → `phase="partial_failure"`, active/ 유지.
- `history/` 30개 초과 → 가장 오래된 것 삭제 (`ls -t | tail -n +31 | xargs rm`).
- 로그: `[DONE] <job_id> total=N done=N failed=N skipped=N duration=...s` append.

**에러 카탈로그 (spec §8 E1 요약, subagent 는 엄격 준수):**

| 코드 | 감지 | 처리 |
|---|---|---|
| `ENV_DIRTY_TREE` | git status | backward 중단, forward 유지, 인라인 안내 |
| `ENV_VIS_DOWN` | curl timeout 5s | Abort, notification |
| `ENV_NO_TRUSTED` | `.trusted` 부재 | 동기 dry-run 진입 |
| `DATA_PARSE_FAIL` | C3 일탈 | 해당 X skip, 로그 |
| `DATA_FILE_MISSING` | Read 실패 | skip |
| `DATA_SELF_REFERENCE` | filter | 조용히 제외 |
| `LLM_CONTEXT_FULL` | 내부 | Abort, notification |
| `LLM_DESC_GEN_FAIL` | 응답 파싱 | snippet fallback |
| `IO_WRITE_FAIL` | MultiEdit | skip, notification |
| `CONCURRENT_DISPATCH` | active/ 존재 | polling |
| `SUBAGENT_CRASH` | Claude Code | phase=crashed, 수동 정리 힌트 (`/vis-backlink-status --clear-failed` 안내, 인라인 알림 즉시 출력) |

**상태 조회:** `/vis-backlink-status` 스킬 사용 (별도 파일).
</when-creating-obsidian-document>
```

> ⚠️ **Risk R2 — `.trusted` 부재 시 무한 dry-run**: 사용자가 계속 거부하면 매 문서 생성마다 동기 dry-run이 강제된다. 탈출구: `touch ~/.claude/state/vis-backlink/.trusted` 수동 실행으로 dry-run 건너뛰기. 이 명령은 Task 13 production 체크리스트에도 명시할 것.

- [ ] **Step 2.3: Verify the edit**

Run:
```bash
grep -n 'when-creating-obsidian-document' ~/.claude/CLAUDE.md
```

Expected: 시작 · 종료 태그 라인 번호 2개. 두 번째 - 첫 번째 ≈ 100 이상 (확장 전 8 → 확장 후 100+).

Run:
```bash
grep -c '^###' <(sed -n '/<when-creating-obsidian-document>/,/<\/when-creating-obsidian-document>/p' ~/.claude/CLAUDE.md)
```

Expected: `2` (Forward, Backward 2개 서브헤더).

- [ ] **Step 2.4: Commit**

CLAUDE.md 는 `~/.claude/` 레포(일반적으로 dotfiles 리포). vault-intelligence repo 가 아니다. 해당 경로의 git repo 에서 commit:

```bash
cd ~/.claude
git status CLAUDE.md
git add CLAUDE.md
git commit -m "feat(hook): extend when-creating-obsidian-document with backward reverse update

- Add backward block orchestrating vis Top5 reverse Related Notes refresh
- Define .trusted gating, sync dry-run on first run, async subagent after
- Embed X-processing subroutine, C3 parser rules, and error catalogue
- Follows docs/superpowers/specs/2026-04-15-vis-backlink-reverse-update-design.md"
```

만약 `~/.claude` 가 git repo 가 아니면 사용자에게 확인 후 `git init` 여부 결정. 일단은 `git rev-parse --is-inside-work-tree` 로 점검.

**Success criteria:** CLAUDE.md 의 훅 블록이 forward/backward 두 섹션으로 확장, `grep -n` 으로 태그 확인 가능.

---

## Task 3 — vis-backlink-status SKILL 신설 (C11)

**Why this matters:** backward 가 비동기로 돌아갈 때 사용자가 상태를 확인할 유일한 인터페이스. LLM 호출/vis daemon 의존 없이 state JSON 만 읽어 요약해야 한다.

**Files:**
- Create: `~/.claude/skills/vis-backlink-status/SKILL.md`

- [ ] **Step 3.1: Write SKILL.md**

Write `~/.claude/skills/vis-backlink-status/SKILL.md`:

```markdown
---
name: vis-backlink-status
description: Use when user asks about background vis-backlink (reverse Related Notes update) progress. Reads ~/.claude/state/vis-backlink/ and reports active/recent/failed jobs with progress bars. Trigger on "vis-backlink 상태", "역방향 진행", "backlink 어디까지", "/vis-backlink-status".
---

# vis-backlink-status

background vis-backlink job (새 Obsidian 문서 생성 시 역방향 Related Notes 업데이트) 의 진행 상태를 보고한다. LLM 호출 없음, vis daemon 비의존.

## When to use

- 슬래시 커맨드: `/vis-backlink-status [options]`
- 자연어: "vis-backlink 상태", "역방향 진행 어디까지", "백링크 작업 현황", "backlink job 확인"

## Options

| Option | 동작 |
|---|---|
| (없음) | 기본 요약 (활성 + 최근 5 history + 실패) |
| `--clear-failed` | `active/` 의 `failed`/`partial_failure`/`crashed` job 을 `history/` 로 이동 |
| `--json` | 파싱된 전체 상태를 JSON 덤프 |
| `--follow` | v2 (미구현, 안내만) |

## Procedure

1. Bash: `ls ~/.claude/state/vis-backlink/active/*.json 2>/dev/null` → 활성 목록.
2. Bash: `ls -t ~/.claude/state/vis-backlink/history/*.json 2>/dev/null | head -5` → 최근 history.
3. 각 JSON 파일을 Read.
4. 집계 후 아래 포맷으로 출력:

```
=== vis-backlink 상태 (YYYY-MM-DD HH:MM:SS) ===

활성 (N):
  [20260415-104523-new-doc] phase=processing
    source: 001-INBOX/new-doc.md
    progress: [####----] 2/3 (current: 003-RESOURCES/baz.md)
    elapsed: 34s
    subagent: vis-backlink-a1b2

최근 완료 (5):
  [20260415-093011-foo] done=3/3 duration=78s
  [20260415-083512-bar] done=2/3 duration=52s partial (1 skipped)
  ...

실패 (M):
  [20260414-221045-crash] phase=crashed
    source: 001-INBOX/whatever.md
    last step: llm_description_generation (target=baz.md)
    힌트: /vis-backlink-status --clear-failed 로 정리
```

5. 실패 존재 시 마지막에 `--clear-failed` 힌트 표시.

## --clear-failed 서브프로시저

```
for each active/*.json where phase in {failed, partial_failure, crashed}:
  mv active/<id>.json history/<id>.json
report: "cleared N failed jobs → history/"
```

파일 권한 실패 시 skip 하고 사유 보고.

## --json

모든 active + 최근 30 history 를 단일 JSON 으로 출력:

```json
{
  "now": "<ISO8601>",
  "active": [<job-json>, ...],
  "history_recent": [<job-json>, ...]
}
```

## 의존성

- Tools: Read, Bash (ls, mv, jq 선택적)
- 파일: `~/.claude/state/vis-backlink/active/*.json`, `~/.claude/state/vis-backlink/history/*.json`
- **LLM 호출 없음, vis daemon 비의존.**

## 에러 처리

- state_dir 부재 → "아직 vis-backlink job 이 실행된 적이 없습니다" 안내.
- JSON 파싱 실패 → 해당 파일은 `[corrupted: <path>]` 로 표시, 나머지는 계속.
- 동시 쓰기로 인한 partial read → 재시도 1 회 후 실패 시 위와 동일하게 표시.

## References

- Spec: `~/git/vault-intelligence/docs/superpowers/specs/2026-04-15-vis-backlink-reverse-update-design.md` (§C11)
- Hook: `~/.claude/CLAUDE.md` `<when-creating-obsidian-document>` backward 블록
```

- [ ] **Step 3.2: Verify**

Run:
```bash
ls ~/.claude/skills/vis-backlink-status/
head -5 ~/.claude/skills/vis-backlink-status/SKILL.md
```

Expected: `SKILL.md` 존재, frontmatter 에 `name:` `description:` 포함.

- [ ] **Step 3.3: Commit**

`~/.claude` 레포에서:

```bash
cd ~/.claude
git add skills/vis-backlink-status/SKILL.md
git commit -m "feat(skill): add vis-backlink-status for state inspection

- Reports active/recent/failed jobs under ~/.claude/state/vis-backlink/
- No LLM calls, no vis daemon dependency
- Supports --clear-failed, --json (--follow deferred to v2)"
```

**Success criteria:** `/vis-backlink-status` 를 호출하면 스킬이 로드되고 위 포맷을 출력 준비가 됨 (실제 동작 검증은 Task 7 에서).

---

## Task 4 — T2.1 파서 샌드박스 시나리오 실행

**Why this matters:** 파서의 결정성을 보장하는 첫 관문. 일탈 케이스를 skip 하지 못하면 파일 손상 위험(Failure Condition #1).

**Files:**
- Create: `tests/scenarios/01-parser.md`

- [ ] **Step 4.1: Write scenario checklist**

Write `tests/scenarios/01-parser.md`:

```markdown
# T2.1 — C3 파서 샌드박스 시나리오

## 전제

- `scripts/sync-sandbox.sh` 실행으로 `/tmp/vault-test/` 재생성
- test vis daemon 실행 (`scripts/start-test-vis.sh`)
- `~/.claude/state/vis-backlink/.trusted` **삭제** (dry-run 유도)
- `~/.claude/state/vis-backlink/active/` 비움

## 실행

사용자 프롬프트 시뮬레이션:
> "다음 내용으로 `/tmp/vault-test/001-INBOX/parser-probe.md` 를 만들어줘 —
> 본문은 'foo, bar, quux 를 연결하는 허브'. vis daemon 은 localhost:8742 사용."

훅이 forward + backward 를 순차 수행. `.trusted` 부재라 dry-run 진입.

## 검증 체크리스트

- [ ] forward: `001-INBOX/parser-probe.md` 에 `## Related Notes` 섹션이 Top 5 로 삽입됨
- [ ] backward: vis Top 5 로 `foo.md`, `bar.md`, `baz.md`, `quux.md`, `no-section.md` 중 상위 5개가 candidate
- [ ] `work-log/2026-04-14.md` 는 `exclude_patterns` 에 의해 자동 제외
- [ ] `ATTACHMENTS/dummy-image.md` 는 자동 제외
- [ ] `deviant-multiline.md` 는 파서 skip 대상으로 보고 (수정 없음)
- [ ] `deviant-image.md` 는 섹션 내부에 `![[...]]` 존재 → 파서 skip
- [ ] `no-section.md` 는 bootstrap minimal 로 `## Related Notes\n\n- [[parser-probe]] — ...` 1줄만 신설
- [ ] 정상 케이스(`foo.md`, `bar.md`, `baz.md`, `quux.md`): 기존 desc 보존, 신규 링크만 LLM desc 생성
- [ ] C6 dry-run diff 출력이 대화 내에 보임
- [ ] 사용자 거부 테스트: 거부 시 `/tmp/vault-test/` 의 어떤 md 도 수정되지 않음 (`git -C /tmp/vault-test diff` 로 확인, vault-test 는 git repo 아니므로 `find /tmp/vault-test -newer <start-marker> -name '*.md'` 로 대체)
- [ ] 사용자 승인 테스트: 승인 후 `~/.claude/state/vis-backlink/.trusted` 생성됨

## 실패 시 조치

- 파서가 일탈 라인을 수정하면 → Task 2 에서 C3 파서 규칙 재작성 (섹션 종료 판정, 이미지 링크 필터 재검토)
- bootstrap minimal 이 전체 Top 5 를 넣으면 → 훅 Backward 서브섹션 "5. bootstrap_mode" 재작성

## Commit after pass

`git add tests/scenarios/01-parser.md && git commit -m "test(scenario): T2.1 parser sandbox checklist"`
```

- [ ] **Step 4.2: Execute scenario manually**

체크리스트의 "실행" 단계를 실제로 수행:

1. `~/.claude/state/vis-backlink/.trusted` 제거: `rm -f ~/.claude/state/vis-backlink/.trusted`.
2. `rm -rf ~/.claude/state/vis-backlink/active/*`.
3. 새 세션 또는 현 세션에서 "파서 probe 문서 만들어줘" 프롬프트. 단, **실제 production vault 가 아닌 샌드박스 대상**으로 훅이 작동하게 `VAULT_ROOT=/tmp/vault-test` 환경변수 설정 필요. 환경변수가 훅에 반영되지 않으면, 이 step 은 제약사항으로 기록하고 수동 시뮬레이션 (훅 텍스트를 보면서 각 절차를 직접 따라가기).

**주의:** 환경변수 기반 vault 전환이 훅에 없으므로, 샌드박스 모드는 "사용자가 훅 절차를 손으로 따라가면서 `/tmp/vault-test/` 경로로 호출" 하는 형태. 이 제약은 이 Task 안에서 완화 권고: 훅에 `VAULT_ROOT` 환경변수 존중 추가 또는 "샌드박스 실행 모드" 주석 추가. 반영 결정은 Task 2 수정으로 되돌아갈 수 있음.

- [ ] **Step 4.3: Record outcomes in scenario file**

체크리스트의 각 항목에 `[x]` 체크 또는 실패 사유 inline 기록.

- [ ] **Step 4.4: Commit**

```bash
cd ~/git/vault-intelligence
git add tests/scenarios/01-parser.md
git commit -m "test(scenario): T2.1 parser sandbox checklist"
```

**Success criteria:** 체크리스트 모든 항목 통과. 일탈 파일(`deviant-*.md`) 0 수정, 정상 파일만 올바르게 업데이트.

---

## Task 5 — T2.8 회귀 (forward 독립성)

**Why this matters:** 기존 forward-only 사용자들이 영향받지 않아야 한다. backward 비활성화 시 훅은 원래와 동일하게 동작해야 한다.

**Files:**
- Create: `tests/scenarios/02-regression-forward.md`

- [ ] **Step 5.1: Define "backward disabled" toggle**

훅에는 명시적 on/off 토글이 없다. 회귀 검증은 두 가지 방법으로 수행:

- 방법 A: `.trusted` 없이 dry-run 에서 **즉시 거부** → backward 변경 0.
- 방법 B: vis daemon 이 `top_k=5` 빈 응답 반환하도록 mock (샌드박스에서 `/search` 응답 수동 주입 어려우면 skip).

실용적으로 **방법 A** 를 채택.

- [ ] **Step 5.2: Write scenario**

Write `tests/scenarios/02-regression-forward.md`:

```markdown
# T2.8 — forward 독립성 회귀

## 목적

backward 추가가 기존 forward 동작을 깨지 않음을 보장.

## 전제

- `/tmp/vault-test/` 재생성 (`scripts/sync-sandbox.sh`)
- `~/.claude/state/vis-backlink/.trusted` 제거 (dry-run 강제)

## 실행

1. `/tmp/vault-test/001-INBOX/regression-probe.md` 를 "quux 책 리딩 노트" 로 생성.
2. 훅 forward 단계 완료 후 dry-run 미리보기 출력됨.
3. 사용자 응답: **거부 (취소)**.

## 검증

- [ ] `001-INBOX/regression-probe.md` 에 `## Related Notes` 가 forward 단계에서 정상 삽입
- [ ] 그 외 어떤 md 파일도 수정되지 않음 (백워드 차단)
- [ ] `~/.claude/state/vis-backlink/.trusted` 생성 안 됨
- [ ] `~/.claude/state/vis-backlink/active/*.json` 파일 0개
- [ ] 로그에 `[DRYRUN_REJECTED]` 기록

## Commit

`git add tests/scenarios/02-regression-forward.md && git commit -m "test(scenario): T2.8 forward regression"`
```

- [ ] **Step 5.3: Execute and commit**

Task 4 와 동일 방식으로 수동 실행 후 체크, 커밋.

**Success criteria:** forward 만 동작, backward 로 인한 부수 변경 0건.

---

## Task 6 — T2.2 Flow 1 dry-run 완전 시나리오

**Why this matters:** `.trusted` gating 의 전체 플로우 (승인/거부 양방향) 검증. 이게 안전한지가 production 전환의 결정 요소.

**Files:**
- Create: `tests/scenarios/03-flow1-dryrun.md`

- [ ] **Step 6.1: Write scenario**

Write `tests/scenarios/03-flow1-dryrun.md`:

```markdown
# T2.2 — Flow 1 (sync dry-run) 완전 시나리오

## 전제

- 샌드박스 초기화
- `.trusted` 제거

## Case A: 거부

1. `001-INBOX/flow1-a.md` 생성.
2. dry-run 출력 확인 → "취소" 선택.
3. 검증:
   - [ ] 어떤 md 도 수정되지 않음
   - [ ] `.trusted` 부재 유지
   - [ ] 로그 `[DRYRUN_REJECTED]`

## Case B: 승인

1. `.trusted` 제거 확인.
2. `001-INBOX/flow1-b.md` 생성.
3. dry-run 출력 → "적용" 선택.
4. 검증:
   - [ ] 실제 수정 대상(정상 파일들) 의 `## Related Notes` 섹션 갱신
   - [ ] 일탈 파일 무변경
   - [ ] `.trusted` 생성
   - [ ] `active/*.json` 없음 (sync 이므로 history 바로 생성 또는 state 생략)
   - [ ] 로그 `[DRYRUN_APPROVED]` + 각 target 결과

## Case C: 선택 적용 (partial)

1. `.trusted` 재제거.
2. `001-INBOX/flow1-c.md` 생성.
3. dry-run → "선택 적용: B 만".
4. 검증:
   - [ ] B 만 갱신, C/E 등 나머지 무변경
   - [ ] `.trusted` 생성 (1회 통과로 간주)

## Commit

`git add tests/scenarios/03-flow1-dryrun.md && git commit -m "test(scenario): T2.2 Flow1 dry-run approve/reject/partial"`
```

- [ ] **Step 6.2: Execute and commit**

**Success criteria:** 3 case 모두 예상대로 동작. 특히 "거부 시 `.trusted` 미생성" 이 핵심.

---

## Task 7 — T2.6 skill 동작 검증

**Why this matters:** Task 3 에서 작성한 `vis-backlink-status` 가 실제로 state 를 읽고 포맷을 뱉는지 확인. daemon 비의존성 확증.

**Files:**
- Create: `tests/scenarios/07-skill-status.md`

- [ ] **Step 7.1: Pre-seed state fixtures**

```bash
mkdir -p ~/.claude/state/vis-backlink/{active,history}

cat > ~/.claude/state/vis-backlink/active/20260415-120000-probe.json <<'EOF'
{
  "job_id": "20260415-120000-probe",
  "source": "001-INBOX/probe.md",
  "started_at": "2026-04-15T12:00:00+09:00",
  "updated_at": "2026-04-15T12:00:34+09:00",
  "phase": "processing",
  "subagent_name": "vis-backlink-a1b2",
  "progress": {"total": 3, "done": 1, "failed": 0, "current": "003-RESOURCES/baz.md"},
  "targets": [
    {"path": "003-RESOURCES/foo.md", "status": "done", "duration_ms": 12400, "changes": {"added": 2, "preserved": 3, "removed": 1}},
    {"path": "003-RESOURCES/baz.md", "status": "in_progress", "step": "llm_description_generation"},
    {"path": "997-BOOKS/quux.md", "status": "pending"}
  ],
  "log_path": "~/.claude/logs/vis-backlink-20260415.log"
}
EOF

cat > ~/.claude/state/vis-backlink/history/20260414-093011-old.json <<'EOF'
{
  "job_id": "20260414-093011-old",
  "source": "001-INBOX/old.md",
  "phase": "completed",
  "progress": {"total": 3, "done": 3, "failed": 0},
  "started_at": "2026-04-14T09:30:11+09:00",
  "updated_at": "2026-04-14T09:31:29+09:00"
}
EOF

cat > ~/.claude/state/vis-backlink/active/20260414-221045-crash.json <<'EOF'
{
  "job_id": "20260414-221045-crash",
  "source": "001-INBOX/whatever.md",
  "phase": "crashed",
  "progress": {"total": 2, "done": 0, "failed": 0},
  "targets": [{"path": "003-RESOURCES/baz.md", "status": "in_progress", "step": "llm_description_generation"}],
  "started_at": "2026-04-14T22:10:45+09:00",
  "updated_at": "2026-04-14T22:11:10+09:00"
}
EOF
```

- [ ] **Step 7.2: Invoke /vis-backlink-status**

새 Claude 세션 (또는 현 세션) 에서 `/vis-backlink-status` 호출.

- [ ] **Step 7.3: Verify output**

Write `tests/scenarios/07-skill-status.md` with expected output matching Task 3 step 3.1 의 포맷. 체크리스트:
- [ ] 활성 2 (processing + crashed) 모두 표시
- [ ] 최근 history 1 건 표시
- [ ] 진행률 bar `[####----]` 형태 출력
- [ ] crashed 항목 강조 + `--clear-failed` 힌트
- [ ] vis daemon 을 중단해도 (`kill`) 결과가 동일 (daemon 비의존 증명)
- [ ] `--clear-failed` 실행 시 `crashed` 만 history 로 이동, `processing` 은 유지
- [ ] `--json` 덤프에 모든 필드 포함

- [ ] **Step 7.4: Cleanup fixtures + commit**

```bash
rm -rf ~/.claude/state/vis-backlink/active/20260415-120000-probe.json
rm -rf ~/.claude/state/vis-backlink/active/20260414-221045-crash.json
rm -rf ~/.claude/state/vis-backlink/history/20260414-093011-old.json

cd ~/git/vault-intelligence
git add tests/scenarios/07-skill-status.md
git commit -m "test(scenario): T2.6 skill status fixture + invocation checklist"
```

**Success criteria:** 스킬이 daemon 중단 상태에서도 정확히 동작, `--clear-failed` 가 failed/crashed 만 이동.

---

## Task 8 — T2.5 에러 카탈로그 시나리오

**Why this matters:** 11개 에러 코드 중 주요 4개 (`ENV_DIRTY_TREE`, `ENV_VIS_DOWN`, `DATA_PARSE_FAIL`, `CONCURRENT_DISPATCH`) 가 설계대로 감지·처리되는지 검증.

**Files:**
- Create: `tests/scenarios/06-flow4-errors.md`

- [ ] **Step 8.1: Write scenario**

Write `tests/scenarios/06-flow4-errors.md`:

```markdown
# T2.5 — Error catalogue 시나리오

## E1. ENV_DIRTY_TREE

전제: `/tmp/vault-test/` 에 임의의 md 수정 (commit 하지 않음) 로 dirty 상태. `.trusted` 존재.

- 새 문서 생성 → backward 진입 전 dirty 감지.
- [ ] forward 만 수행
- [ ] 인라인 메시지 "vault dirty → backward 생략"
- [ ] `active/*.json` 생성 안 됨

## E2. ENV_VIS_DOWN

전제: test vis daemon 중단. `.trusted` 존재.

- 새 문서 생성 → backward 진입 시 curl timeout (5초) 후 Abort.
- [ ] notification 발생
- [ ] forward 는 수행되었는지 (forward 도 vis 의존 — 이 경우 forward 역시 실패해야 자연스러움)
- [ ] state `phase="vis_unavailable"` 기록 (dispatched 후 즉시 전이)

## E3. DATA_PARSE_FAIL

전제: 샌드박스 정상 상태. vis Top 5 안에 `deviant-multiline.md` 또는 `deviant-image.md` 가 포함.

- [ ] 해당 대상 `targets[X].status="skipped_parse"` + 사유 기록
- [ ] 다른 target 은 계속 처리
- [ ] phase=partial_failure (다른 target 도 실패하면) 또는 completed + skipped 표시

## E4. CONCURRENT_DISPATCH

전제: `.trusted` 존재. `active/dummy.json` 에 `phase=processing` 수동 주입.

- 새 문서 생성 → polling 진입.
- [ ] 2초 주기 polling 확인
- [ ] 5초 경과 시점에서 "선행 backward job 대기 중" 1회 알림
- [ ] 수동으로 `mv active/dummy.json history/` 하면 즉시 새 dispatch 진행

## Commit

`git add tests/scenarios/06-flow4-errors.md && git commit -m "test(scenario): T2.5 error catalogue (DIRTY/VIS_DOWN/PARSE/CONCURRENT)"`
```

- [ ] **Step 8.2: Execute all 4 errors**

- [ ] **Step 8.3: Commit**

**Success criteria:** 4개 에러 코드 모두 정확히 감지·처리됨. git diff 손상 0 건.

---

## Task 9 — T2.3 Flow 2 async dispatch

**Why this matters:** 본 기능의 프로덕션 기본 경로. **메인 Claude blocking < 2초** 가 T3 성능 목표이자 Failure Condition.

**Files:**
- Create: `tests/scenarios/04-flow2-async.md`

- [ ] **Step 9.1: Write scenario**

Write `tests/scenarios/04-flow2-async.md`:

```markdown
# T2.3 — Flow 2 async dispatch

## 전제

- 샌드박스 초기화
- `.trusted` 존재 (없으면 `touch ~/.claude/state/vis-backlink/.trusted`)
- `active/` 비움

## 실행

1. `date +%s%3N > /tmp/flow2-start.txt` (타임스탬프 ms)
2. `001-INBOX/flow2-probe.md` 생성.
3. 메인 Claude 해제 시점 측정.

## 검증

- [ ] forward 완료 + async dispatch 까지 총 시간 < 2000ms (T3 목표)
  - 측정: `date +%s%3N > /tmp/flow2-end.txt && echo $(($(cat /tmp/flow2-end.txt) - $(cat /tmp/flow2-start.txt)))`
- [ ] `active/<job_id>.json` 생성되고 `phase="dispatched"` → `"processing"` 전이
- [ ] 각 target 처리 시 state atomic update (`updated_at` 변화)
- [ ] 전체 완료 후 `phase="completed"`, `active/<id>.json` → `history/<id>.json` 이동
- [ ] subagent 로그가 `~/.claude/logs/vis-backlink-<date>.log` 에 append
- [ ] 메인 Claude 가 dispatch 후 후속 사용자 요청에 즉시 응답 가능

## Commit

`git add tests/scenarios/04-flow2-async.md && git commit -m "test(scenario): T2.3 Flow2 async dispatch latency + state transitions"`
```

- [ ] **Step 9.2: Execute**

실제로 새 문서 생성 → subagent dispatch 관찰 → state JSON 전이 확인.

- [ ] **Step 9.3: Fix if latency > 2000ms**

2초 초과 시:
- forward 단계 `curl` 응답 지연? → top_k=5 로 줄이고 rerank off 테스트
- backward state 초기 기록이 동기적으로 너무 오래? → atomic write 를 subagent 첫 step 으로 위임
Task 2 의 "Async dispatch 프로시저" 재작성.

- [ ] **Step 9.4: Commit**

**Success criteria:** 메인 blocking < 2초, subagent 완료 후 active → history 이동.

---

## Task 10 — T2.4 Flow 3 sequential polling

> ⚠️ **Risk R5 — 5초 timeout UX**: 연속 문서 생성 시 2초 주기 polling → 5초 경과 후 "대기 중" 1회 알림. 이후에도 대기 중이면 사용자는 `/vis-backlink-status` 를 수동 호출해야 한다. 이는 현재 scope 한계이며 v2d(병렬 subagent)로 해결 예정. 시나리오 검증 시 UX 이슈로 **Task fail 처리하지 말 것** — 설계 제약으로 기록만.

**Why this matters:** 연속 문서 생성 시 backward 큐가 안전하게 직렬화되는지. P1.a (순차 실행) 결정의 정확성 확인.

**Files:**
- Create: `tests/scenarios/05-flow3-sequential.md`

- [ ] **Step 10.1: Write scenario**

Write `tests/scenarios/05-flow3-sequential.md`:

```markdown
# T2.4 — Flow 3 sequential polling

## 전제

- 샌드박스 + `.trusted` 존재

## 실행

t=0: `001-INBOX/flow3-a.md` 생성 → #1 dispatch.
t=5s: `001-INBOX/flow3-b.md` 생성. 훅의 polling 진입.

## 검증

- [ ] t=5s 시점에 `active/` 에 #1 존재
- [ ] #2 는 polling 루프 (2초 주기)
- [ ] #1 완료 후 5초 이내 #2 dispatch
- [ ] 두 job 의 `started_at` 간격 ≤ #1 duration + 5초
- [ ] 로그: polling 중 "선행 backward job 대기 중" 1회 표시 (5초 경과 후)

## Commit

`git add tests/scenarios/05-flow3-sequential.md && git commit -m "test(scenario): T2.4 Flow3 sequential polling"`
```

- [ ] **Step 10.2: Execute + commit**

**Success criteria:** 순차 dispatch, 동시 실행 없음.

---

## Task 11 — T2.7 bootstrap_mode 전환

**Why this matters:** minimal → full 전환이 **훅 config 한 줄 변경만으로** 작동해야 한다. 코드 변경 0.

**Files:**
- Create: `tests/scenarios/08-bootstrap-mode.md`

- [ ] **Step 11.1: Scenario**

Write `tests/scenarios/08-bootstrap-mode.md`:

```markdown
# T2.7 — bootstrap_mode minimal ↔ full

## Case A: minimal (default)

- `no-section.md` → `## Related Notes\n\n- [[<A>]] — ...` 1 줄
- [ ] 정확히 1 줄 신설 확인

## Case B: full

1. `~/.claude/CLAUDE.md` 의 backward config 에서 `bootstrap_mode: "minimal"` → `"full"` 변경 (임시).
2. 샌드박스 새로 초기화 + `no-section.md` 복구.
3. 새 문서 생성 → `no-section.md` 의 Related Notes 가 Top 5 전체로 신설.
4. [ ] 5개 링크 삽입 확인
5. 테스트 후 config 되돌림 (`minimal`).

## Commit

`git add tests/scenarios/08-bootstrap-mode.md && git commit -m "test(scenario): T2.7 bootstrap_mode minimal↔full toggle"`
```

- [ ] **Step 11.2: Execute + commit**

**Success criteria:** config 한 줄 변경만으로 동작 전환.

---

## Task 12 — T3 성능 측정

**Why this matters:** 성능 목표 수치화. 사용자 경험의 객관적 근거.

**Files:**
- Create: `tests/scenarios/09-performance.md`

- [ ] **Step 12.1: Scenario**

Write `tests/scenarios/09-performance.md`:

```markdown
# T3 — 성능 측정

## 지표

| 지표 | 목표 | 측정 방법 |
|---|---|---|
| Forward blocking | < 2초 | forward 시작~종료 timestamp |
| Backward 5 대상 완료 | < 90초 | dispatch~`phase=completed` |
| Polling 오버헤드 | < 5초 | polling 진입~해제 |
| vis `/search` 1회 | < 500ms | curl `-w '%{time_total}'` |
| 스킬 응답 | < 1초 | `/vis-backlink-status` 실행 시간 |

## 방법

샌드박스 3회 반복 측정 평균값 기록.

- [ ] 각 지표 3회 측정
- [ ] 평균값이 목표 이내
- [ ] 목표 초과 시 원인 분석 inline 기록

## Commit

`git add tests/scenarios/09-performance.md && git commit -m "test(scenario): T3 performance measurements"`
```

- [ ] **Step 12.2: Execute + commit**

**Success criteria:** 모든 지표 목표 이내.

---

## Task 13 — Production 첫 실행 가이드

**Why this matters:** 샌드박스에서 production 으로 전환. 사용자가 직접 수행하며 plan 은 체크리스트만 제공.

**Files:**
- Create: `tests/scenarios/10-production-rollout.md`

- [ ] **Step 13.1: Scenario**

Write `tests/scenarios/10-production-rollout.md`:

```markdown
# T5 — Production 첫 실행 체크리스트

## 사전

- [ ] T2 전체 통과 (01~08)
- [ ] T3 성능 목표 달성 (09)
- [ ] CLAUDE.md diff 리뷰 완료 (Task 2)
- [ ] SKILL.md 리뷰 완료 (Task 3)

## Production 첫 실행

1. `~/.claude/state/vis-backlink/.trusted` 가 없는지 확인:
   ```bash
   test ! -f ~/.claude/state/vis-backlink/.trusted && echo "ready"
   ```
2. 실제 vault (`$VAULT_ROOT`) 가 clean 한지 확인:
   ```bash
   cd $VAULT_ROOT && git status --porcelain
   ```
3. Obsidian 문서 1건 생성 요청 (e.g. "오늘 공부한 X 주제 정리 문서").
4. 훅 forward 후 dry-run 미리보기 출력 확인.
5. diff 를 섹션별로 읽고 수동 검토.
6. 승인 → MultiEdit 적용 → `.trusted` 생성.
7. `/vis-backlink-status` 로 첫 job 확인.

> ⚠️ dry-run 을 반복 거부하고 싶지 않을 때 수동 우회:
> ```bash
> mkdir -p ~/.claude/state/vis-backlink
> touch ~/.claude/state/vis-backlink/.trusted
> ```
> 단, 이 경우 최초 실사용 diff 검토를 생략하므로 **권장하지 않음**.

## 1주 실사용 후 후속

- [ ] `~/.claude/state/vis-backlink/history/` 의 최근 30 건 분석
  - 실패율 (`failed + partial_failure / total`)
  - 평균 duration
  - 가장 자주 skip 되는 파일 패턴
- [ ] 피드백 기반 exclude_patterns 조정
- [ ] v2 후보 triage (spec §11)

## Commit (사용자 수행 후)

`git add tests/scenarios/10-production-rollout.md && git commit -m "test(scenario): T5 production rollout checklist"`
```

- [ ] **Step 13.2: Commit**

**Success criteria:** 사용자가 production 1건 생성 → 승인 → `/vis-backlink-status` 첫 history 확인.

---

## Self-Review

### 1. Spec coverage

| Spec 섹션 | Plan 커버 |
|---|---|
| §4 Decisions (Q1~Q4, P1~P2, 접근 B) | Task 2 Backward 블록에 전량 반영 |
| §5 Architecture | Task 2, 3 |
| §C1 훅 구조 | Task 2 |
| §C2 X 서브루틴 | Task 2 |
| §C3 파서 | Task 2 (규칙) + Task 4 (검증) |
| §C4 exclude 필터 | Task 2 (config) + Task 4 (검증) |
| §C5 rollback | Task 2 (git 가드), 별도 Task 없음 |
| §C6 dry-run 포맷 | Task 2 + Task 6 |
| §C7 background dispatch | Task 2 + Task 9 |
| §C8 동시성 polling | Task 2 + Task 10 |
| §C9 결과 표시 | Task 2 |
| §C10 state JSON 스키마 | Task 2 + Task 7 fixture |
| §C11 skill | Task 3 + Task 7 |
| §7 Flow 1~5 | Task 6/9/10/8/7 |
| §8 Error catalogue | Task 2 (카탈로그) + Task 8 (주요 4개 검증) |
| §9 T2.1~T2.8 | Task 4~11 |
| §9 T3 | Task 12 |
| §9 T5 | Task 13 |

누락 없음. E1 의 11개 중 6개(LLM_CONTEXT_FULL, LLM_DESC_GEN_FAIL, IO_WRITE_FAIL, DATA_FILE_MISSING, DATA_SELF_REFERENCE, SUBAGENT_CRASH)는 Task 8 에서 별도 case 로 다루지 않고 훅의 에러 카탈로그 텍스트 (Task 2) 로만 대응. 이는 spec T2.5 요구 범위를 초과하지 않음.

### 2. Placeholder scan

- "implement later", "TODO" — 없음
- "similar to Task N" — 없음 (각 task 독립 서술)
- "add error handling" — 없음 (에러 카탈로그는 Task 2 에 구체적)
- 구체 file path 모든 Task 에 명시
- 구체 commit message 모든 Task 에 명시

### 3. Type consistency

LLM 절차 지시문 plan 이므로 타입 시그니처 없음. 확인 대상은 **용어 일관성**:
- "forward" / "backward" 용어 일관 ✓
- "X 처리 서브루틴" / "X" (target) 용어 일관 ✓
- `phase` 값: `dispatched`, `processing`, `completed`, `partial_failure`, `failed`, `crashed`, `skipped_*`, `vis_unavailable` — spec §7 상태 전이와 일치 ✓
- `state_dir` 경로 `~/.claude/state/vis-backlink/` 모든 Task 에서 동일 ✓
- `bootstrap_mode` 값: `minimal` | `full` 일관 ✓

### 4. 구조적 경고

- **Task 4 Step 4.2** 에 샌드박스 vault 전환을 위한 환경변수 부재 문제 명시. 필요 시 Task 2 의 훅에 `VAULT_ROOT` 환경변수 존중 로직 추가하도록 이 plan 실행 중 루프백 가능. 이는 plan 흐름상 자연스러운 Red → Green 사이클.
- **Task 2 Step 2.4** 의 `~/.claude` git repo 존재 여부는 실행 시점 검증 항목. 없으면 사용자 확인 후 처리.

---

## 실행 핸드오프

- 권장: `superpowers:subagent-driven-development` — 각 Task 를 fresh subagent 로 실행, task 간 리뷰.
- 대안: `superpowers:executing-plans` — 현 세션에서 순차 실행, 체크포인트 단위 배치.

**다음 단계:** 사용자가 실행 방식 선택 → 해당 sub-skill 발동.
