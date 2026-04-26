# vis-backlink Smart Trigger Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** backward Related Notes 갱신의 진입점을 분류·이동 명령어(`/obsidian:add-tag`, `/obsidian:add-tag-and-move-file`)로 이전하고, 휴리스틱 5개 신호 기반으로 proceed(자동) / skip(prompt) 를 결정하는 `vis-backlink-trigger` 헬퍼 스킬을 신설한다.

**Architecture:** 3-tier 위임 구조 — (1) 명령어 마지막 step 에서 vis-backlink-trigger 스킬 invoke, (2) 스킬이 사전 가드 → 휴리스틱 평가 → per-file dirty 체크 → Agent dispatch 수행, (3) background subagent 가 기존 C2 서브루틴으로 실제 파일 수정. CLAUDE.md `<when-creating-obsidian-document>` 의 backward 블록은 완전 제거, forward 만 유지.

**Tech Stack:** LLM 절차 지시문(SKILL.md, 명령어 .md 텍스트) · Claude Code 도구(Read, MultiEdit, Bash, Agent) · vis daemon HTTP(`localhost:8741`) · 기존 샌드박스 vault(`/tmp/vault-test/`, port 8742) · 기존 spec C2~C10 서브루틴(변경 없음).

**Implementation Strategy:** 패치 1 과 동일 — Python 유틸 추출 없이 LLM 절차 지시문으로 수행. 휴리스틱 평가도 SKILL.md 본문에 의사 코드로 명시. 결정성은 시나리오(수동 검증 체크리스트)로 보장.

**Spec 참조:** `docs/superpowers/specs/2026-04-26-vis-backlink-smart-trigger-design.md` (approved 2026-04-26).

**Failure Conditions (전체 plan):**
- `.disabled` ON 상태에서 vis `/search` 호출됨 (비용 발생 — 가드 0 이 먼저여야 함)
- 메인 Claude blocking 4초 초과
- per-file dirty 체크에서 A 자신이 dirty 로 잡혀 skip 됨
- hard veto 발화 없이 skip 추천이 나옴 (soft signal 이 veto 역할을 하면 안 됨)
- CHG1 이후 CLAUDE.md 에 backward 블록이 남아 있어 이중 발화 발생
- `--recursive` 모드에서 trigger 가 호출됨

---

## File Structure

**Create** (vault-intelligence repo):
- `tests/scenarios/12-trigger-guard.md` — T6.5(ENV_DISABLED), T6.6(ENV_VIS_DOWN) 시나리오
- `tests/scenarios/13-heuristic.md` — T6.2(S4 veto), T6.3(S5 veto), T6.9(uncommitted 비간주)
- `tests/scenarios/14-perfile-dirty.md` — T6.4(per-file dirty 일부 skip)
- `tests/scenarios/15-ux.md` — skip prompt [y/N], proceed 인라인 알림
- `tests/scenarios/16-recursive-skip.md` — T6.8(--recursive 모드 trigger skip)
- `tests/scenarios/17-e2e.md` — T6.1(전체 Flow A end-to-end), T6.10(메시지 정확성)
- `tests/fixtures/sandbox_vault/003-RESOURCES/draft-note.md` — S5 signal 검증용 fixture (frontmatter draft: true)
- `tests/fixtures/sandbox_vault/003-RESOURCES/short-note.md` — S1 signal 검증용 (300자 본문)
- `tests/fixtures/sandbox_vault/daily/2026-04-26.md` — S2 signal 검증용 (시간성 경로)

**Create** (global):
- `~/.claude/skills/vis-backlink-trigger/SKILL.md` — 헬퍼 스킬 (NC1~NC5 전체)

**Modify** (global):
- `~/.claude/CLAUDE.md` — `<when-creating-obsidian-document>` backward 블록 제거 + footer 추가 (CHG1)
- `~/.claude/commands/obsidian/add-tag.md` — 마지막 step 추가 (CHG2)
- `~/.claude/commands/obsidian/add-tag-and-move-file.md` — 마지막 step 추가 (CHG2)

**Reuse** (변경 없음):
- `tests/fixtures/sandbox_vault/` 기존 fixture (foo.md, bar.md, baz.md, work-log/, ATTACHMENTS/ 등)
- `scripts/sync-sandbox.sh`, `scripts/start-test-vis.sh`
- `~/.claude/skills/vis-backlink-status/SKILL.md`
- 기존 spec C2~C10 서브루틴 (CLAUDE.md 내부, forward + subagent 로직)

---

## Task 1 — 샌드박스 fixture 보강

**Why:** 휴리스틱 신호 S1(짧은 본문)·S2(시간성 경로)·S5(frontmatter draft) 검증을 위한 fixture 가 기존 샌드박스에 없음. Task 4(휴리스틱) 시나리오가 이 파일들에 의존.

**Files:**
- Create: `tests/fixtures/sandbox_vault/003-RESOURCES/draft-note.md`
- Create: `tests/fixtures/sandbox_vault/003-RESOURCES/short-note.md`
- Create: `tests/fixtures/sandbox_vault/daily/2026-04-26.md`

- [ ] **Step 1.1: draft-note.md 생성**

`tests/fixtures/sandbox_vault/003-RESOURCES/draft-note.md` 내용:

```markdown
---
title: Draft Note
status: draft
tags: []
---

# Draft Note

이 노트는 아직 작성 중인 드래프트 상태입니다. vis-backlink 휴리스틱 S5 신호 검증용.

본문에 충분한 내용이 있어도 frontmatter status: draft 이면 hard veto 가 발화해야 한다.
```

- [ ] **Step 1.2: short-note.md 생성**

`tests/fixtures/sandbox_vault/003-RESOURCES/short-note.md` 내용:

```markdown
---
title: Short Note
tags: []
---

# Short Note

짧은 노트. S1 신호(500자 미만) 검증용. soft signal 이므로 단독으로 skip veto 유발 안 됨.
```

- [ ] **Step 1.3: daily/2026-04-26.md 생성**

`tests/fixtures/sandbox_vault/daily/2026-04-26.md` 내용:

```markdown
---
title: 2026-04-26 Daily Note
tags: []
---

# 2026-04-26

오늘의 작업 로그. S2 신호(시간성 경로) 검증용. soft signal 이므로 단독으로 skip veto 유발 안 됨.
```

- [ ] **Step 1.4: sync-sandbox.sh 실행해서 /tmp/vault-test/ 에 반영됐는지 확인**

```bash
bash scripts/sync-sandbox.sh
ls /tmp/vault-test/003-RESOURCES/ | grep -E "draft|short"
ls /tmp/vault-test/daily/
```

Expected output:
```
draft-note.md
short-note.md
2026-04-26.md
```

- [ ] **Step 1.5: commit**

```bash
git add tests/fixtures/sandbox_vault/003-RESOURCES/draft-note.md \
        tests/fixtures/sandbox_vault/003-RESOURCES/short-note.md \
        tests/fixtures/sandbox_vault/daily/2026-04-26.md
git commit -m "test(fixture): 휴리스틱 신호 S1·S2·S5 검증용 sandbox fixture 추가"
```

---

## Task 2 — 사전 가드 시나리오 작성 (TDD red)

**Why:** SKILL.md 구현 전에 ENV_DISABLED·ENV_VIS_DOWN 동작을 명세화. 구현 후 이 체크리스트를 재실행해서 통과 확인.

**Files:**
- Create: `tests/scenarios/12-trigger-guard.md`

- [ ] **Step 2.1: 시나리오 파일 생성**

`tests/scenarios/12-trigger-guard.md` 내용:

```markdown
# T6.5/T6.6 — vis-backlink-trigger 사전 가드 시나리오

## 전제

- `scripts/sync-sandbox.sh` 실행으로 `/tmp/vault-test/` 최신화
- test vis daemon 실행: `bash scripts/start-test-vis.sh`

---

## T6.5 — ENV_DISABLED (비용 zero 검증)

### 준비
1. `.disabled` 마커 생성: `touch ~/.claude/state/vis-backlink/.disabled`
2. vis daemon 요청 카운터 기준값 기록 (또는 logs 스냅샷):
   `cat ~/.claude/logs/vis-backlink-*.log | wc -l`

### 실행
사용자 프롬프트:
> "`/tmp/vault-test/001-INBOX/test-disabled.md` 파일에 태그 붙이고 정리해줘.
> vis daemon 은 localhost:8742 사용. vis-backlink-trigger 의 사전 가드 0 테스트."

### 검증
- [ ] 명령어 실행 후 인라인 메시지에 `backward 비활성화` 포함 (`재활성화: /vis-backlink-toggle on` 안내 포함)
- [ ] vis `/search` 호출이 **0회** 발생 (logs 카운터 변화 없음 — 비용 zero)
- [ ] state active/ 에 새 job JSON 없음
- [ ] forward 는 정상 실행됨 (test-disabled.md 에 ## Related Notes 삽입됨)

### 복구
`rm ~/.claude/state/vis-backlink/.disabled`

---

## T6.6 — ENV_VIS_DOWN (daemon 응답 없음)

### 준비
1. test vis daemon 중단 (또는 존재하지 않는 포트 사용)
2. `.disabled` 마커 없음 확인: `ls ~/.claude/state/vis-backlink/.disabled` → 없어야 함

### 실행
사용자 프롬프트:
> "`/tmp/vault-test/001-INBOX/test-vis-down.md` 에 태그 붙이고 정리해줘.
> vis daemon 은 localhost:8743 (존재하지 않는 포트) 사용."

### 검증
- [ ] 5초 이내에 timeout 발생 후 `vis daemon 응답 없음` 포함 메시지 출력
- [ ] `visd start 후 재시도` 안내 포함
- [ ] state active/ 에 새 job JSON 없음
- [ ] forward 는 정상 실행됨 (test-vis-down.md 에 ## Related Notes 삽입됨)
- [ ] 전체 blocking 7초 이내

---

## T6.7 — 동시성 (직전 backward job active)

### 준비
1. active/ 에 dummy job JSON 생성:
   ```bash
   mkdir -p ~/.claude/state/vis-backlink/active
   cat > ~/.claude/state/vis-backlink/active/dummy-job.json << 'EOF'
   {"job_id": "dummy", "phase": "processing", "started_at": "2026-04-26T00:00:00Z"}
   EOF
   ```

### 실행
사용자 프롬프트:
> "`/tmp/vault-test/001-INBOX/concurrent-test.md` 태그 붙이고 정리해줘."

### 검증
- [ ] SKILL.md 가 active/ 에 job 있음을 감지
- [ ] 2초 polling 시작
- [ ] `⏳ 선행 backward job 대기 중 (5초 max)` 알림 1회 출력 (5초 후)
- [ ] phase 를 `completed` 로 수동 변경 후 polling 해제 확인:
  ```bash
  python3 -c "
  import json, glob
  f = glob.glob(os.path.expanduser('~/.claude/state/vis-backlink/active/*.json'))[0]
  d = json.load(open(f)); d['phase'] = 'completed'
  json.dump(d, open(f, 'w'))
  "
  ```
- [ ] polling 해제 후 정상 휴리스틱 평가 → dispatch 진행

### 복구
```bash
rm -f ~/.claude/state/vis-backlink/active/dummy-job.json
```

---

## 수동 시뮬레이션 결과

(Task 3 SKILL.md 구현 후 재실행)
```

- [ ] **Step 2.2: commit**

```bash
git add tests/scenarios/12-trigger-guard.md
git commit -m "test(scenario): T6.5/T6.6 사전 가드 시나리오 작성"
```

---

## Task 3 — `vis-backlink-trigger` SKILL.md 신설 (사전 가드 0·1·2)

**Why:** 스킬의 골격 + 세 개의 사전 가드를 구현. 이후 Task 에서 기능을 추가하는 방식으로 점진적 확장.

**Files:**
- Create: `~/.claude/skills/vis-backlink-trigger/SKILL.md`

- [ ] **Step 3.1: 디렉토리 생성**

```bash
mkdir -p ~/.claude/skills/vis-backlink-trigger
```

- [ ] **Step 3.2: SKILL.md 생성 (사전 가드 0·1·2 포함)**

`~/.claude/skills/vis-backlink-trigger/SKILL.md` 내용:

````markdown
---
name: vis-backlink-trigger
description: |
  Use when invoked from /obsidian:add-tag or /obsidian:add-tag-and-move-file as the
  final step. Evaluates heuristic signals on the just-classified document A, recommends
  proceed/skip for backward Related Notes refresh, then dispatches async subagent.
  Honors .disabled marker. Per-file dirty check.
argument-hint: "<A_path>"
model: sonnet
---

# vis-backlink Backward Trigger

이 스킬은 `/obsidian:add-tag` 또는 `/obsidian:add-tag-and-move-file` 의 마지막 step 에서
호출됩니다. 인자로 전달된 `A_path` 를 기준으로 backward Related Notes 갱신을 결정합니다.

`$ARGUMENTS` = A 의 경로 (vault root 기준 상대 또는 절대 경로).

## Step 1: 사전 가드 0 — .disabled 마커 확인

```bash
[ -f ~/.claude/state/vis-backlink/.disabled ] && echo "DISABLED" || echo "OK"
```

결과가 `DISABLED` 이면:
- 인라인 고지 출력:
  `ℹ️ backward 비활성화 (재활성화: /vis-backlink-toggle on)`
- **즉시 종료** (아래 모든 단계 skip, vis /search 호출 금지)

결과가 `OK` 이면 Step 2 진행.

## Step 2: 사전 가드 1 — vis daemon health 확인

```bash
curl -s --max-time 5 http://localhost:8741/health
```

응답이 없거나 오류이면 (`ENV_VIS_DOWN`):
- 인라인 알림:
  `⚠️ vis daemon 응답 없음 — backward 생략 (visd start 후 재시도)`
- **즉시 종료**

응답 정상이면 Step 3 진행.

## Step 3: 사전 가드 2 — 동시성 체크

```bash
ls ~/.claude/state/vis-backlink/active/*.json 2>/dev/null
```

결과가 있으면 (`CONCURRENT_DISPATCH`):
- 2초 대기 후 재확인 (최대 5초 polling)
- 5초 경과 후에도 active 이면: `⏳ 선행 backward job 대기 중 (5초 max)` 1회 알림 후 계속 polling
- phase 가 `completed`, `partial_failure`, `user_skipped`, `crashed` 중 하나가 되면 해제
- `phase=crashed` 감지 시: `mv ~/.claude/state/vis-backlink/active/<id>.json ~/.claude/state/vis-backlink/history/<id>.json` 후 `🧹 crashed job 자동 정리: <job_id>` 알림

state_dir 부트스트랩 (없으면 생성):
```bash
mkdir -p ~/.claude/state/vis-backlink/active
mkdir -p ~/.claude/state/vis-backlink/history
```

## Step 4 이후: 휴리스틱 평가 (Task 5 에서 추가)

(placeholder — Task 5 에서 구현)
````

- [ ] **Step 3.3: 시나리오 12 수동 검증 (T6.5)**

```bash
touch ~/.claude/state/vis-backlink/.disabled
```

사용자 프롬프트:
> "`/tmp/vault-test/001-INBOX/test-disabled.md` 파일에 태그 붙이고 정리해줘."

검증: 인라인 고지 `ℹ️ backward 비활성화` 출력, vis /search 호출 없음.

```bash
rm ~/.claude/state/vis-backlink/.disabled
```

- [ ] **Step 3.4: 시나리오 12 수동 검증 (T6.6)**

test vis daemon 을 중지하거나 다른 포트로 변경 후:

> "`/tmp/vault-test/001-INBOX/test-vis-down.md` 파일에 태그 붙이고 정리해줘."

검증: `⚠️ vis daemon 응답 없음` 출력 (5~7초 이내).

- [ ] **Step 3.5: 시나리오 12 체크리스트에 수동 결과 기록**

`tests/scenarios/12-trigger-guard.md` 의 "수동 시뮬레이션 결과" 섹션에 날짜·결과 추가:

```markdown
## 수동 시뮬레이션 결과

### 2026-04-26
- T6.5: ✅ 사전 가드 0 정상 (vis /search 0회, forward 유지)
- T6.6: ✅ ENV_VIS_DOWN 5초 timeout 후 알림 (forward 유지)
```

- [ ] **Step 3.6: commit**

```bash
git add tests/scenarios/12-trigger-guard.md
git commit -m "feat(skill): vis-backlink-trigger 스킬 신설 (사전 가드 0·1·2)"
```

> ⚠️ SKILL.md 는 `~/.claude/skills/` 글로벌 위치라 git 추적 대상 아님. 시나리오 결과 업데이트만 commit.

---

## Task 4 — 휴리스틱 시나리오 작성 (TDD red)

**Why:** 휴리스틱 평가기(NC2) 구현 전에 S4·S5 hard veto, soft signal 표시, uncommitted 비간주 동작을 명세화.

**Files:**
- Create: `tests/scenarios/13-heuristic.md`

- [ ] **Step 4.1: 시나리오 파일 생성**

`tests/scenarios/13-heuristic.md` 내용:

```markdown
# T6.2/T6.3/T6.9 — 휴리스틱 평가기 시나리오

## 전제

- `scripts/sync-sandbox.sh` 실행
- test vis daemon 실행 (localhost:8742)
- `.disabled` 마커 없음
- vis daemon 이 sandbox fixture 인덱싱 완료

---

## T6.2 — Hard Veto S4 (자동 제외율 ≥60%)

### 준비
A = `003-RESOURCES/short-note.md` (내용은 짧지만 S4 테스트용 — vis Top 5 를 work-log/ATTACHMENTS 위주로 나오도록 쿼리 조정)

sandbox vis daemon 에 `/search?query=로그&top_k=5` 로 Top 5 가 work-log·ATTACHMENTS 4건 이상이 되도록 시나리오 구성.

실제로는 vis daemon 의 응답을 조작하기 어려우므로:
- short-note.md 의 내용을 "로그 일지 기록 업무" 등 work-log 유사 키워드로 구성해서 work-log 문서가 Top 5 에 오도록 유도
- 또는 수동으로 "Top 5 중 4건이 work-log/ATTACHMENTS 라면 어떻게 동작해야 하는지" 를 시뮬레이션

### 실행
사용자 프롬프트:
> "`/tmp/vault-test/003-RESOURCES/short-note.md` 태그 붙이고 정리해줘."

### 검증
- [ ] SKILL.md 가 vis /search 호출 후 Top 5 분석
- [ ] 자동 제외 비율 계산 결과 ≥60% 이면 S4 hard veto 발화
- [ ] `⚠️ backward skip 추천 — 자동 제외율 XX% (Top 5 중 N건이 work-log/draft)` 메시지 출력
- [ ] `강제 진행하시겠습니까? [y/N]` prompt 표시
- [ ] N/Enter 입력 시 `ℹ️ backward skip 확정 (사용자)` 출력 후 종료
- [ ] state history/ 에 `phase: user_skipped` 로 기록됨
- [ ] soft signal (S1·S2·S3) 도 근거로 함께 표시됨

---

## T6.3 — Hard Veto S5 (frontmatter draft: true)

### 준비
A = `/tmp/vault-test/003-RESOURCES/draft-note.md` (frontmatter `status: draft`)

### 실행
사용자 프롬프트:
> "`/tmp/vault-test/003-RESOURCES/draft-note.md` 태그 붙이고 정리해줘."

### 검증
- [ ] SKILL.md 가 A 의 frontmatter 에서 `status: draft` 감지 → S5 hard veto 발화
- [ ] skip 추천 메시지 + `[y/N]` prompt 출력
- [ ] `y` 입력 시 → proceed 경로로 fallthrough, state reason: `user_override_skip`
- [ ] `🔗 backward dispatched` 메시지 (user_override 임을 알 수 있도록)
- [ ] state history/ 에 `reason: user_override_skip` 로 기록됨

---

## T6.9 — 회귀: git uncommitted ≠ draft

### 준비
A = 새로 작성된 `/tmp/vault-test/001-INBOX/uncommitted-new.md` (git add 안 함)
vault git status 는 dirty (uncommitted 파일 있음)
A 의 frontmatter 에는 `draft` 관련 필드 없음

### 실행
사용자 프롬프트:
> "`/tmp/vault-test/001-INBOX/uncommitted-new.md` 태그 붙이고 정리해줘."

### 검증
- [ ] SKILL.md 가 A 의 frontmatter 에 `status: draft` 또는 `draft: true` 없으므로 S5 발화 안 함
- [ ] uncommitted 상태 자체는 skip 사유가 아님
- [ ] vault dirty 이어도 backward 진행 (per-file dirty 체크로 처리 — S5 미발화)
- [ ] proceed 추천 (S4 미발화라는 전제) → 자동 dispatch

---

## 수동 시뮬레이션 결과

(Task 5 휴리스틱 구현 후 재실행)
```

- [ ] **Step 4.2: commit**

```bash
git add tests/scenarios/13-heuristic.md
git commit -m "test(scenario): T6.2/T6.3/T6.9 휴리스틱 평가기 시나리오 작성"
```

---

## Task 5 — 휴리스틱 평가기 구현 (NC2) + per-file dirty + dispatch (NC3)

**Why:** SKILL.md Step 4 이후를 완성. 5개 신호 평가 → 추천 → per-file dirty → Agent dispatch 전체 흐름.

**Files:**
- Modify: `~/.claude/skills/vis-backlink-trigger/SKILL.md` (Step 4 이후 전체 추가)
- Create: `tests/scenarios/14-perfile-dirty.md`

- [ ] **Step 5.1: SKILL.md Step 4 이후 추가**

`~/.claude/skills/vis-backlink-trigger/SKILL.md` 의 `## Step 4 이후: 휴리스틱 평가 (Task 5 에서 추가)` 섹션을 아래 내용으로 교체:

````markdown
## Step 4: vis /search — Top 5 조회

```bash
curl -s --get \
  --data-urlencode "query=<A_title>" \
  "http://localhost:8741/search?search_method=hybrid&rerank=true&top_k=5"
```

`<A_title>` = A 의 frontmatter `title` 필드 (없으면 첫 번째 `#` 헤딩 텍스트).

응답 JSON 의 `results` 배열을 Top 5 로 사용. 응답 실패 시 → `ENV_VIS_DOWN` 처리 (Step 2 와 동일).

## Step 5: 휴리스틱 평가 (NC2)

`exclude_patterns` = `["work-log/**", "ATTACHMENTS/**", "<A_path>"]` (A 자신은 무조건 제외).

### Hard Veto 신호 평가 (1개라도 해당 → skip 추천)

**S4: 자동 제외율**
Top 5 results 중 `exclude_patterns` 에 매칭되는 비율을 계산.
- 매칭 수 / 5 ≥ 0.6 (즉 3개 이상 제외 대상) → S4 veto 발화

**S5: frontmatter draft**
A 의 frontmatter 에서 다음 중 하나라도 있으면 S5 veto 발화:
- `status: draft`
- `draft: true`

> ⚠️ git uncommitted 상태는 draft 로 간주하지 않음. frontmatter 필드만 확인.

### Soft 신호 수집 (근거 표시용, veto 권한 없음)

**S1:** A 본문 (frontmatter 제외) 글자 수 → `<500자` 이면 `짧음`, 이상이면 `충분`
**S2:** A 경로가 `work-log/`, `daily/`, `journal/` 중 하나를 포함하면 `시간성 경로`, 아니면 `일반 경로`
**S3:** Top 5 results 의 평균 score (소수점 2자리)

### 추천 결정

veto 신호 (S4 또는 S5) 1개 이상 발화 → recommendation = `skip`
veto 없음 → recommendation = `proceed`

### 남은 targets 계산

Top 5 에서 `exclude_patterns` 매칭 제거 → 실제 backward 대상 목록 (0~5개).

## Step 6: 분기 처리

### recommendation = skip

출력:
```
⚠️ backward skip 추천 — <veto 근거>
   soft signals: <S1 결과>, <S2 결과>, Top 5 평균 <S3>
   대상 후보: <targets list> (총 N건)
   강제 진행하시겠습니까? [y/N]
```

사용자 응답:
- `y` 또는 `Y` → Step 7 (per-file dirty + dispatch) 로 진행. job state reason: `user_override_skip`
- `N`, `n`, Enter → state 기록 (`phase: "user_skipped"`) + history/ 이동 + 종료

### recommendation = proceed

출력:
```
🔗 backward dispatched — Top 5 평균 <S3>, 제외 후 <N>건 대상 (job=<job_id>)
   상태 조회: /vis-backlink-status
```

Step 7 로 진행.

## Step 7: Per-file Dirty Check + Job 초기화

`job_id` = `$(date +%Y%m%d-%H%M%S)-$(basename "$ARGUMENTS" .md)`

state JSON 초기 기록:
```bash
cat > /tmp/vis-backlink-state-tmp.json << EOF
{
  "job_id": "<job_id>",
  "source": "<A_path>",
  "started_at": "<ISO8601>",
  "updated_at": "<ISO8601>",
  "phase": "dispatched",
  "reason": "<normal|user_override_skip>",
  "progress": {"total": <N>, "done": 0, "failed": 0},
  "targets": [],
  "log_path": "~/.claude/logs/vis-backlink-$(date +%Y%m%d).log"
}
EOF
mv /tmp/vis-backlink-state-tmp.json ~/.claude/state/vis-backlink/active/<job_id>.json
```

targets 각각에 대해 per-file dirty 체크:
- A 자신은 무시 (항상 dirty 이므로)
- 각 X 에 대해: `cd <vault_root> && git status --porcelain "<X_path>"`
  - 결과 있음 → targets 에 `{"path": X, "status": "skipped_dirty"}` 기록
  - 결과 없음 → targets 에 `{"path": X, "status": "queued"}` 기록

dirty skip 이 있으면 proceed 인라인 메시지 뒤에 `(N건 dirty skip)` 추가.

## Step 8: Background Subagent Dispatch

`queued` targets 가 0건이면 → 모두 dirty skip 됨. state `phase: "all_dirty_skip"`, history/ 이동, 알림 후 종료.

`queued` targets 가 1건 이상이면:

Agent(
  subagent_type: "general-purpose",
  name: "vis-backlink-<job_id 앞 8자리>",
  run_in_background: true,
  prompt: """
    vis-backlink backward update 실행.

    <기존 spec C2 X 처리 서브루틴 전체 내용 붙여넣기>

    Config:
    - top_k: 5
    - bootstrap_mode: minimal
    - exclude_patterns: ["work-log/**", "ATTACHMENTS/**", "<A_path>"]
    - concurrency: sequential
    - state_dir: ~/.claude/state/vis-backlink/
    - log_path: ~/.claude/logs/vis-backlink-<date>.log
    - vault_root: <vault_root>

    Job state path: ~/.claude/state/vis-backlink/active/<job_id>.json
    Targets (queued 만): <queued_list>
  """
)

즉시 해제. 사용자는 다음 작업 가능.

## history/ 정리

`ls -t ~/.claude/state/vis-backlink/history/ | tail -n +31 | xargs -I{} rm ~/.claude/state/vis-backlink/history/{}` 로 30개 초과 시 삭제.
````

- [ ] **Step 5.2: per-file dirty 시나리오 생성**

`tests/scenarios/14-perfile-dirty.md` 내용:

```markdown
# T6.4 — Per-file Dirty 체크 시나리오

## 전제

- `scripts/sync-sandbox.sh` 실행
- test vis daemon 실행 (localhost:8742)
- Top 5 X 중 하나 (`bar.md`) 를 수동으로 편집해서 dirty 상태로 만들기:
  `echo "dirty" >> /tmp/vault-test/003-RESOURCES/bar.md`
- vault git status 확인: `cd /tmp/vault-test && git status --porcelain 003-RESOURCES/bar.md` → 결과 있어야 함

## 실행

사용자 프롬프트:
> "`/tmp/vault-test/001-INBOX/perfile-test.md` 파일에 태그 붙이고 정리해줘."

## 검증

- [ ] vis /search 결과 Top 5 에 `bar.md` 포함
- [ ] bar.md 에 대해 `git status --porcelain` 결과 있음 → `skipped_dirty` 로 기록
- [ ] 나머지 X (foo.md, baz.md 등) 는 clean → `queued` 로 기록
- [ ] proceed 메시지에 `(1건 dirty skip)` 포함
- [ ] subagent 는 queued targets 만 처리 (bar.md 수정 안 됨)
- [ ] state JSON active/<job>.json 에 targets 목록 확인

## 복구

`cd /tmp/vault-test && git checkout -- 003-RESOURCES/bar.md`

## 수동 시뮬레이션 결과

(구현 후 기록)
```

- [ ] **Step 5.3: 시나리오 13 수동 검증 (T6.3 — S5 veto)**

```bash
# /tmp/vault-test/003-RESOURCES/draft-note.md 에 이미 status: draft 있음
```

사용자 프롬프트:
> "`/tmp/vault-test/003-RESOURCES/draft-note.md` 태그 붙이고 정리해줘."

검증: S5 veto 발화, skip 추천 메시지 + `[y/N]` 출력.

- [ ] **Step 5.4: 시나리오 13 수동 검증 (T6.9 — uncommitted 비간주)**

```bash
# A = 새 파일, git add 안 한 상태, frontmatter draft 없음
echo "# New Note\n\n내용" > /tmp/vault-test/001-INBOX/uncommitted-new.md
cd /tmp/vault-test && git status --porcelain 001-INBOX/uncommitted-new.md
# 결과: ?? 001-INBOX/uncommitted-new.md (untracked)
```

사용자 프롬프트:
> "`/tmp/vault-test/001-INBOX/uncommitted-new.md` 태그 붙이고 정리해줘."

검증: S5 발화 안 함, proceed 추천 (S4 미발화 전제).

- [ ] **Step 5.5: 시나리오 결과 기록 + commit**

`tests/scenarios/13-heuristic.md` 와 `tests/scenarios/14-perfile-dirty.md` 의 결과 섹션 업데이트.

```bash
git add tests/scenarios/13-heuristic.md tests/scenarios/14-perfile-dirty.md
git commit -m "feat(skill): 휴리스틱 평가기 + per-file dirty + dispatch 구현 완료"
```

---

## Task 6 — UX 시나리오 + 메시지 정확성 검증

**Why:** NC4(skip prompt) · NC5(proceed inline) 의 메시지 형식이 spec §8.2 표와 1:1 일치하는지 확인.

**Files:**
- Create: `tests/scenarios/15-ux.md`
- Create: `tests/scenarios/16-recursive-skip.md`

- [ ] **Step 6.1: UX 시나리오 생성**

`tests/scenarios/15-ux.md` 내용:

```markdown
# T6.10 — UX 메시지 정확성 + skip prompt 시나리오

## 검증 대상 메시지 (spec §8.2 표)

| 상황 | 기대 메시지 |
|---|---|
| `.disabled` ON | `ℹ️ backward 비활성화 (재활성화: /vis-backlink-toggle on)` |
| vis daemon down | `⚠️ vis daemon 응답 없음 — backward 생략 (visd start 후 재시도)` |
| heuristic proceed | `🔗 backward dispatched — Top 5 평균 X.XX, N건 대상 (job=...)` |
| heuristic skip 추천 | `⚠️ backward skip 추천 — <근거>. 강제 진행? [y/N]` |
| 사용자 N/Enter | `ℹ️ backward skip 확정 (사용자)` |
| 사용자 y | `🔗 backward dispatched ...` (reason: user_override) |
| Top 5 일부 dirty | `🔗 backward dispatched — N건 대상 (M건 dirty skip)` |
| 직전 job 대기 | `⏳ 선행 backward job 대기 중 (5초 max)` |
| subagent crash 정리 | `🧹 crashed job 자동 정리: <job_id>` |

## 검증 절차

각 시나리오별로 실제 호출 후 메시지가 위 표와 일치하는지 ✅/❌ 체크.

### Skip → N 검증
- [ ] S5 veto 발화 시나리오 (T6.3) 후 N 입력 → `ℹ️ backward skip 확정 (사용자)` 정확히 포함

### Skip → y (override) 검증
- [ ] S5 veto 발화 후 y 입력 → `🔗 backward dispatched` (user_override 표시)

### Proceed (dirty 일부) 검증
- [ ] bar.md dirty 상태 (T6.4) → `(1건 dirty skip)` 포함 메시지

## 수동 시뮬레이션 결과

(Task 5~7 완료 후 기록)
```

- [ ] **Step 6.2: --recursive skip 시나리오 생성**

`tests/scenarios/16-recursive-skip.md` 내용:

```markdown
# T6.8 — --recursive 모드 trigger skip 시나리오

## 전제

- `scripts/sync-sandbox.sh` 실행

## 실행

사용자 프롬프트:
> "`/tmp/vault-test/003-RESOURCES/` 디렉토리 전체 태그 붙여줘. (`/obsidian:add-tag --recursive`)"

## 검증

- [ ] 명령어가 `--recursive` 모드로 실행됨
- [ ] vis-backlink-trigger 스킬이 **호출되지 않음** (명령어 last step skip)
- [ ] state active/ 에 새 job JSON 없음
- [ ] forward 도 skip (기존 `--recursive` 정책 그대로)

## 수동 시뮬레이션 결과

(Task 8 CHG2 완료 후 기록)
```

- [ ] **Step 6.3: commit**

```bash
git add tests/scenarios/15-ux.md tests/scenarios/16-recursive-skip.md
git commit -m "test(scenario): T6.8/T6.10 UX 메시지 + recursive skip 시나리오 작성"
```

---

## Task 7 — CHG1: CLAUDE.md backward 블록 제거

**Why:** 패치 1 의 backward 블록이 CLAUDE.md 에 남아 있으면 CHG2 이후 이중 발화 위험. 이 단계에서 완전 제거.

**Files:**
- Modify: `~/.claude/CLAUDE.md` — `<when-creating-obsidian-document>` 의 backward 부분 제거

- [ ] **Step 7.1: 현재 CLAUDE.md backward 블록 범위 파악**

```bash
grep -n "### Backward\|### Forward\|</when-creating-obsidian-document>" ~/.claude/CLAUDE.md | head -20
```

결과로 `### Backward` 시작 줄과 `</when-creating-obsidian-document>` 끝 줄 번호 확인.

- [ ] **Step 7.2: backward 블록 제거 + footer 추가**

`~/.claude/CLAUDE.md` 의 `<when-creating-obsidian-document>` 블록에서:

**제거 대상**: `### Backward (A 의 Top 5 각각에 대해 역방향 Related Notes full refresh)` 부터 `</when-creating-obsidian-document>` 직전까지.

**유지 대상**: Forward 섹션 (1~5번 항목 전체).

**추가** (`</when-creating-obsidian-document>` 직전에):

```markdown
**Backward Related Notes**: 이제 `/obsidian:add-tag` 또는 `/obsidian:add-tag-and-move-file` 의 마지막 단계에서 `vis-backlink-trigger` 스킬이 처리합니다. 자세한 동작은 `~/git/vault-intelligence/docs/superpowers/specs/2026-04-26-vis-backlink-smart-trigger-design.md` 참조.
```

- [ ] **Step 7.3: 이중 발화 없음 확인**

```bash
grep -n "vis-backlink\|backward\|\.trusted\|ENV_DIRTY_TREE" ~/.claude/CLAUDE.md
```

`forward` 관련 5단계 항목 외에 backward 로직이 남아있지 않은지 확인.

> ⚠️ `~/.claude/CLAUDE.md` 는 git 추적 대상 아님 (홈 디렉토리). 이 task 는 commit 없음.

---

## Task 8 — CHG2: 명령어 두 개에 trigger 호출 추가

**Why:** backward 의 새 진입점. 두 명령어 마지막 step 에 `Skill: vis-backlink-trigger` 호출 추가.

**Files:**
- Modify: `~/.claude/commands/obsidian/add-tag.md`
- Modify: `~/.claude/commands/obsidian/add-tag-and-move-file.md`

- [ ] **Step 8.1: add-tag.md 수정**

`~/.claude/commands/obsidian/add-tag.md` 의 `7. **관련 문서(Related Notes) 추가**` 항목 다음에 아래 항목 추가:

```markdown
8. **Backward Related Notes 트리거** (관련 문서들의 Related Notes 갱신)
   - 위 단계 완료 후 `vis-backlink-trigger` 스킬을 invoke (`Skill: vis-backlink-trigger`, args=처리한 파일의 절대 경로)
   - 휴리스틱 평가 결과에 따라 자동 진행 또는 사용자 prompt
   - `--recursive` 모드에서는 이 단계 skip (대량 처리 시 vis daemon 부하 ↑, 발화 가치 ↓)
```

- [ ] **Step 8.2: add-tag-and-move-file.md 수정**

`~/.claude/commands/obsidian/add-tag-and-move-file.md` 의 `4. **관련 문서(Related Notes) 추가**` 항목 다음에 아래 항목 추가:

```markdown
5. **Backward Related Notes 트리거** (관련 문서들의 Related Notes 갱신)
   - 위 단계 완료 후 `vis-backlink-trigger` 스킬을 invoke (`Skill: vis-backlink-trigger`, args=이동 완료된 파일의 절대 경로)
   - 휴리스틱 평가 결과에 따라 자동 진행 또는 사용자 prompt
```

> ⚠️ `~/.claude/commands/` 는 git 추적 대상 아님. 이 task 는 commit 없음.

---

## Task 9 — End-to-end 통합 시나리오 + 프로덕션 롤아웃 가이드

**Why:** 전체 파이프라인 (명령어 → trigger 스킬 → heuristic → dispatch → subagent) 이 end-to-end 로 동작하는지 확인.

**Files:**
- Create: `tests/scenarios/17-e2e.md`

- [ ] **Step 9.1: E2E 시나리오 생성**

`tests/scenarios/17-e2e.md` 내용:

```markdown
# T6.1 — End-to-End Flow A (전체 파이프라인) 시나리오

## 전제

- `scripts/sync-sandbox.sh` 실행
- test vis daemon 실행 (localhost:8742, 인덱싱 완료)
- `.disabled` 마커 없음
- active/ 비어있음
- A = `/tmp/vault-test/001-INBOX/e2e-test.md` (foo·bar·quux 를 연결하는 허브 노트)

## 실행

사용자 프롬프트:
> "다음 내용으로 `/tmp/vault-test/001-INBOX/e2e-test.md` 를 만들고, 태그 붙이고
> 003-RESOURCES/ 로 분류해줘. vis daemon 은 localhost:8742.
> 내용: 'foo, bar, quux, baz 의 교차점을 정리한 통합 노트'"

## 검증 체크리스트 (Flow A 전체)

### 명령어 실행
- [ ] `/obsidian:add-tag-and-move-file e2e-test.md` 실행됨
- [ ] 태그 부여 완료 (frontmatter tags 확인)
- [ ] `001-INBOX/ → 003-RESOURCES/` 이동 완료

### Forward
- [ ] `## Related Notes` 섹션이 e2e-test.md 에 삽입됨 (vis Top 5)

### vis-backlink-trigger 스킬 자동 호출
- [ ] 사전 가드 0 통과 (.disabled 없음)
- [ ] 사전 가드 1 통과 (vis health OK)
- [ ] 사전 가드 2 통과 (active/ 비어있음)

### 휴리스틱 평가
- [ ] vis /search 호출 → Top 5 결과 (foo.md, bar.md, baz.md, quux.md, no-section.md 예상)
- [ ] S4: 자동 제외율 ≤40% → veto 안함
- [ ] S5: e2e-test.md frontmatter draft 없음 → veto 안함
- [ ] recommendation = PROCEED
- [ ] soft signals 표시 (S1·S2·S3)

### Per-file dirty + Dispatch
- [ ] Top 5 X 모두 clean → 모두 queued
- [ ] `🔗 backward dispatched — Top 5 평균 X.XX, N건 대상 (job=...)` 출력
- [ ] 메인 Claude 4초 이내 해제
- [ ] state active/<job>.json 생성 확인

### Background Subagent
- [ ] `/vis-backlink-status` 로 진행 중 확인 (phase=dispatched 또는 processing)
- [ ] 완료 후 foo.md, bar.md 등의 `## Related Notes` 섹션 갱신 확인
- [ ] no-section.md 에 bootstrap minimal (e2e-test.md 링크 1줄) 신설 확인
- [ ] state history/<job>.json phase=completed 확인

## 성능 측정

- [ ] 메인 Claude blocking 시간: __ 초 (≤4초 목표)
- [ ] subagent 전체 완료 시간: __ 초

---

## 프로덕션 롤아웃 가이드

### 첫 1~2회 모니터링 절차

1. `/obsidian:add-tag-and-move-file <실제 vault 파일>` 실행
2. `🔗 backward dispatched` 메시지 확인
3. `/vis-backlink-status` 로 진행 상황 확인 (job 완료까지 대기)
4. `cat ~/.claude/state/vis-backlink/history/<job_id>.json` 로 state 확인
5. `cd ~/DocumentsLocal/msbaek_vault && git diff` 로 backward 변경사항 확인
6. 변경 내용 적절하면 `git add -p && git commit -m "chore(backlinks): ..."` 로 확정
7. 문제 있으면 `git checkout -- <X_path>` 로 해당 파일 롤백

### 임계값 튜닝 기준

1주 운영 후:
- skip 추천 후 사용자 `y` (강제 진행) 비율 > 10% → S4 임계값 60% 상향 검토
- backward 발화율 < 70% (proceed 비율) → S4 임계값 하향 또는 S5 조건 완화 검토

## 수동 시뮬레이션 결과

(전체 구현 완료 후 기록)
```

- [ ] **Step 9.2: 시나리오 16 (recursive skip) 검증**

수동으로 `--recursive` 호출 후 trigger 스킬이 호출되지 않는지 확인.

- [ ] **Step 9.3: 시나리오 결과 기록 + commit**

```bash
git add tests/scenarios/17-e2e.md \
        tests/scenarios/15-ux.md \
        tests/scenarios/16-recursive-skip.md
git commit -m "test(scenario): E2E Flow A + 프로덕션 롤아웃 가이드 시나리오 작성"
```

> ⚠️ SKILL.md / CLAUDE.md / 명령어 .md 변경은 글로벌 위치라 git 미포함. 시나리오 결과 파일만 commit.

---

## 완료 기준

- [ ] `~/.claude/skills/vis-backlink-trigger/SKILL.md` 생성 완료 (사전 가드 0·1·2 + 휴리스틱 + per-file dirty + dispatch + UX)
- [ ] `~/.claude/CLAUDE.md` backward 블록 완전 제거 (forward only 확인)
- [ ] `~/.claude/commands/obsidian/add-tag.md` + `add-tag-and-move-file.md` trigger 호출 추가
- [ ] 시나리오 12~17 수동 검증 완료 + 결과 기록
- [ ] T6.9 회귀 (uncommitted ≠ draft) 명시적 통과
- [ ] 이중 발화 없음 확인 (`grep backward ~/.claude/CLAUDE.md` 에서 backward 로직 없음)
