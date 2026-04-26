---
title: vis-backlink Smart Trigger (Heuristic-Driven Backward Refresh)
date: 2026-04-26
status: approved
scope: 패치 2 — backward 진입점을 분류·이동 명령어로 이전 + 휴리스틱 기반 자동/수동 분기
predecessor: 2026-04-15-vis-backlink-reverse-update-design.md
---

# vis-backlink Smart Trigger Design

> **작업 home**: `~/git/vault-intelligence` repo. 본 스펙과 후속 plan · 구현 참고자료를 여기에 보관한다.
> 최종 산출물 설치 위치:
> - `~/.claude/CLAUDE.md` 의 `<when-creating-obsidian-document>` 블록 (forward only 로 축소)
> - `~/.claude/skills/vis-backlink-trigger/SKILL.md` (신설)
> - `~/.claude/commands/obsidian/add-tag.md` (마지막 step 수정)
> - `~/.claude/commands/obsidian/add-tag-and-move-file.md` (마지막 step 수정)
> - 기존 `vis-backlink-status` 스킬 + `vis-backlink-toggle` 명령어는 변경 없음

## 1. Context & Motivation

### 1.1 기존 패치 1 (2026-04-15) 의 동작과 한계

패치 1 은 `<when-creating-obsidian-document>` 훅이 **새 Obsidian 문서가 생성될 때마다** backward (vis Top 5 X 각각의 Related Notes 섹션을 full refresh) 를 실행하도록 설계됐다. 두 개의 게이트로 제어:

- **사전 가드 1 (`ENV_DIRTY_TREE`)**: vault 에 uncommitted 변경 있으면 backward 자체 차단
- **첫 실행 게이트 (`.trusted` 마커)**: 부재 시 동기 dry-run → 사용자 승인 → `touch .trusted` → 이후 비동기 자동

운영 결과 두 가지 마찰 발생:

1. **트리거 시점이 너무 광범위**: INBOX 단계의 draft 문서 생성에도 backward 가 발화 → vis Top 5 신뢰도 낮음 (문서 안정화 전), 추후 분류·이동 시 다시 backward 가 필요 → 중복 작업
2. **`ENV_DIRTY_TREE` 가 너무 보수적**: vault 작업 중엔 항상 dirty 인 게 일반적이라 backward 가 거의 발화 안 됨. 사용자가 다음 로그를 자주 봄:
   ```
   ⚠️ Backward Related Notes 생략: vault dirty tree (ENV_DIRTY_TREE)
       (commit 후 다음 문서 정리 시 backward 재시도됩니다)
   ```
   `commit` 되지 않은 문서를 사실상 draft 로 간주하는 효과 → 사용자 의도와 불일치

### 1.2 핵심 통찰

- **분류·이동 시점이 안정화 시점**: `/obsidian:add-tag` 또는 `/obsidian:add-tag-and-move-file` 호출은 사용자가 명시적으로 "이 문서를 정리한다" 는 의도를 표현. 이 시점의 vis Top 5 가 가장 신뢰도 높음.
- **휴리스틱이 dry-run 보다 정교한 신호**: 5개 신호 (자동 제외율, frontmatter draft, 본문 길이, 경로 종류, Top 5 평균 score) 가 매번 평가되면 `.trusted` 1회 검증보다 풍부한 정보 제공.
- **dirty 가드는 X 단위로 충분**: A 자신은 어차피 dirty (방금 변경됨), Top 5 X 들 중 사용자가 동시 편집 중인 파일만 충돌 위험 → narrow 한 가드로 발화율 큰 폭 향상.

## 2. Goal

backward (Related Notes 역방향 갱신) 의 트리거 시점·게이트 정책을 재설계한다:

- 트리거 시점: "새 문서 생성" → "분류·이동 명령어 실행"
- 사전 가드: vault 전체 dirty → per-file dirty (X 단위)
- 첫 실행 게이트: `.trusted` + dry-run → 휴리스틱 + 추천 (매 호출 시)
- 진입점: CLAUDE.md 훅 → 명령어 → 헬퍼 스킬 (3-tier)

**성공 기준**:
- 분류·이동 명령어 1회당 backward 발화율 **≥ 70%** (현재 패치 1: 측정 시 약 10~20%로 추정)
- 메인 Claude blocking ≤ 4초 (vis /search + heuristic + per-file dirty + state 작성)
- skip 추천 정확도: hard veto 발화 시 사용자 강제 진행 (`y`) 비율 ≤ 10% (= 추천이 합리적이라는 신호)

## 3. Non-Goals

- vault 전체 backfill (이미 존재하는 섹션 일괄 재계산) — v2 후보 (패치 1 §11.v2a 와 동일)
- Obsidian 에서 직접 작성된 문서 (Claude 외부) 의 backward 커버리지 — v2 catch-up 스크립트
- 휴리스틱 신호 가중치 학습 — v2 ML/통계 분석
- 자동 rollback (실패 시 backward 변경 일괄 되돌리기) — git 워크플로우 침해 위험
- forward 로직 변경 — 기존 동작 그대로 유지

## 4. Design Decisions

| ID | 질문 | 결정 | 근거 |
|---|---|---|---|
| Q1 | backward 트리거 진입점 | **(b) 두 명령어 (`add-tag`, `add-tag-and-move-file`) 모두** | 양쪽 모두 forward 보유, 대칭성 |
| Q2 | 휴리스틱 결합 방식 | **(c) Hard veto + soft signal** | 결정 추적성, 직관, 임계값 명시 |
| Q2-fix | 휴리스틱 5번 (draft) 정의 | frontmatter `status: draft` OR `draft: true` 만. git uncommitted 는 draft 아님 | 사용자 지적 — uncommitted 는 정상 작업 상태 |
| Q3 | dirty 가드 정책 | **(b) Per-file dirty** — A 자신 무시, Top 5 X 중 dirty 만 skip | 발화율 ↑ + 안전망 유지 |
| Q4 | 추천 UX 와 `.trusted` 관계 | **(c) `.trusted` 폐기 + 휴리스틱 자동/수동 분기** | proceed = 자동, skip = `[y/N]` prompt |
| Q5 | 두 진입점 공통화 | **(b2) `vis-backlink-trigger` 헬퍼 스킬 신설** | SSOT, vis-backlink 패밀리 일관성 |
| Q6-D1 | `.disabled` 우선순위 | 휴리스틱 평가 자체 skip, 인라인 고지 1줄 | 메모리 Q3.a, 비용 zero |
| Q6-D2 | proceed 추천 시 알림 | 자동 dispatch + 짧은 근거 + 알림 1줄 | 사용자 인지 + 마찰 최소 |
| Q6-D3 | skip 추천 시 prompt | `[y/N]` (default = skip, Enter = skip) | 보수적 default |
| Q6-D4 | dry-run preview 옵션 | v1 추가 안 함, v2 후보 | 휴리스틱 + state JSON 으로 충분 |

## 5. Architecture

### 5.1 호출 흐름

```
사용자: /obsidian:add-tag-and-move-file <file>
         (또는 /obsidian:add-tag <file>)
  │
  ▼
명령어 실행 (Claude)
  ├─ Step 1~N: 태그 부여, 파일 이동 (해당 명령어 본연 작업)
  ├─ Step (마지막-1): forward (자기 문서에 Related Notes 추가)
  └─ Step (마지막):  Skill: vis-backlink-trigger 호출 ← NEW
                          │
                          ▼
                vis-backlink-trigger SKILL.md 실행
                  ├─ 사전 가드 0: .disabled 마커 → ENV_DISABLED, 인라인 고지, exit
                  ├─ 사전 가드 1: vis daemon /health → ENV_VIS_DOWN, exit
                  │  (ENV_DIRTY_TREE 가드 폐기 — per-file 로 대체)
                  │
                  ├─ 휴리스틱 평가기
                  │   ├─ vis /search(A) → Top 5 X
                  │   ├─ Hard veto 신호: S4 (자동 제외율 ≥60%), S5 (A draft)
                  │   ├─ Soft 신호 (S1·S2·S3) 점수화 → 근거 표시용
                  │   └─ 추천: proceed | skip
                  │
                  ├─ 분기:
                  │   ├─ skip → [y/N] prompt
                  │   │    ├─ y → proceed 경로로 fallthrough (user_override)
                  │   │    └─ N/Enter → exit (state phase=user_skipped)
                  │   └─ proceed → 인라인 알림 1줄 + 즉시 비동기 dispatch
                  │
                  └─ 비동기 dispatch:
                      ├─ Per-file dirty 체크 (Top 5 X 각각, A 제외)
                      ├─ Agent(general-purpose, run_in_background=true)
                      └─ 메인 Claude 즉시 해제 (≤ 4초)
```

### 5.2 책임 경계

| 컴포넌트 | 기존 (패치 1) | 패치 2 |
|---|---|---|
| `<when-creating-obsidian-document>` 훅 | forward + backward 오케스트레이터 | **forward only** — backward 블록 완전 제거 |
| `vis-backlink-trigger` SKILL.md | (없음) | **신설** — backward 진입점 + 휴리스틱 + dispatch |
| `/obsidian:add-tag` 명령어 | 태그 부여 + Related Notes (forward) | step 마지막에 `Skill: vis-backlink-trigger` 호출 추가 |
| `/obsidian:add-tag-and-move-file` 명령어 | 위 + 파일 이동 | 동일 |
| `vis-backlink-status` SKILL.md | 상태 조회 | 변경 없음 |
| `vis-backlink-toggle` 명령어 | `.disabled` on/off | 변경 없음 |
| 기존 spec C2~C10 (서브루틴, 파서, 에러, state) | backward 실제 작업 | **변경 없음** — vis-backlink-trigger 가 그대로 위임 |

### 5.3 핵심 변화 요약

1. 트리거 시점: "아무 새 문서" → "분류·이동 명령어" (안정화 시점)
2. 차단 범위: vault 전체 dirty → 해당 X 파일 dirty 만 (per-file)
3. 첫 실행 게이트: dry-run 1회 → 매번 휴리스틱 추천
4. 진입점: 훅 (CLAUDE.md) → 명령어 → 헬퍼 스킬 (3-tier 위임)

## 6. Components

### NC1. `vis-backlink-trigger` SKILL.md (신설)

**위치**: `~/.claude/skills/vis-backlink-trigger/SKILL.md`

**Frontmatter**:
```yaml
---
name: vis-backlink-trigger
description: |
  Use when invoked from /obsidian:add-tag or /obsidian:add-tag-and-move-file as the
  final step. Evaluates heuristic signals on the just-classified document A, recommends
  proceed/skip for backward Related Notes refresh, then dispatches async subagent.
  Honors .disabled marker. Per-file dirty check.
allowed-tools: [Bash, Read, Skill, Task]
---
```

**스킬 본문 흐름**:

1. **입력 파싱**: `<A_path>` (호출 명령어가 인자로 전달, 절대 경로 또는 vault root 기준 상대)
2. **사전 가드 0**: `[ -f ~/.claude/state/vis-backlink/.disabled ]` 참 → `ENV_DISABLED` 인라인 고지 + exit
3. **사전 가드 1**: `curl -s --max-time 5 http://localhost:8741/health` 실패 → `ENV_VIS_DOWN` 알림 + exit
4. **사전 가드 2 (동시성)**: `ls ~/.claude/state/vis-backlink/active/*.json` 존재 → 2초 polling, max 5초. crashed job 자동 정리.
5. **NC2 호출** (Heuristic Evaluator) → recommendation 받음
6. **분기**: skip 추천 → NC4 prompt | proceed 추천 → NC3 dispatch
7. dispatch 완료 → 메인 Claude 즉시 해제

### NC2. Heuristic Evaluator (스킬 내부 함수)

**입력**: `A_path`, vis Top 5 결과
**출력**: `{recommendation: "proceed"|"skip", veto_signals: [...], soft_signals: [...], targets: [X1..X5], excluded: [...]}`

#### Hard veto 신호 (1개라도 발화 → skip 추천)

| ID | 정의 | 임계값 |
|---|---|---|
| S4 | Top 5 중 `exclude_patterns` 매칭 비율 | **≥60%** (5건 중 3건 이상 work-log/draft/ATTACHMENTS 등) |
| S5 | A 의 frontmatter `status: draft` 또는 `draft: true` | true 시 발화 |

**S5 명시**: git uncommitted 상태는 draft 로 간주하지 않음. frontmatter 의 명시적 필드만 평가.

#### Soft 신호 (근거 표시용, veto 권한 없음)

| ID | 정의 | 표시 형식 |
|---|---|---|
| S1 | A 본문 (frontmatter 제외) 글자 수 | `<500자 (짧음)` 또는 `≥500자 (충분)` |
| S2 | A 경로 매칭 (`work-log/`, `daily/`, `journal/`, `997-BOOKS/`) | `시간성 경로` 또는 `일반 경로` |
| S3 | Top 5 평균 score | `평균 0.XX` |

#### 평가 로직 (의사 코드)

```python
def evaluate(A_path, vis_top5):
    veto = []
    soft = []

    # S4: 자동 제외율
    excluded_count = sum(1 for x in vis_top5 if matches_exclude(x.path))
    excluded_ratio = excluded_count / len(vis_top5)
    if excluded_ratio >= 0.6:
        veto.append(("S4", f"자동 제외율 {int(excluded_ratio*100)}%"))

    # S5: frontmatter draft
    fm = read_frontmatter(A_path)
    if fm.get("status") == "draft" or fm.get("draft") is True:
        veto.append(("S5", "frontmatter draft"))

    # S1·S2·S3: 근거 표시용
    body_len = len(read_body(A_path))
    soft.append(("S1", f"본문 {body_len}자 ({'짧음' if body_len < 500 else '충분'})"))
    soft.append(("S2", f"{'시간성' if matches_temporal(A_path) else '일반'} 경로"))
    soft.append(("S3", f"Top 5 평균 score {avg_score(vis_top5):.2f}"))

    recommendation = "skip" if veto else "proceed"
    return {
        "recommendation": recommendation,
        "veto_signals": veto,
        "soft_signals": soft,
        "targets": [x for x in vis_top5 if not matches_exclude(x.path)],
        "excluded": [x for x in vis_top5 if matches_exclude(x.path)],
    }
```

### NC3. Per-file Dirty Check + Async Dispatch

```bash
# A 자신은 무조건 dirty 이므로 무시
# Top 5 X 중 S4 자동 제외 적용 후 실제 대상에 대해
queued=()
skipped_dirty=()
for X in "${targets[@]}"; do
  if [ -n "$(cd <vault_root> && git status --porcelain "$X")" ]; then
    skipped_dirty+=("$X")
    state.targets[X]={status: "skipped_dirty"}
  else
    queued+=("$X")
    state.targets[X]={status: "queued"}
  fi
done
```

dispatch 직전 state JSON 에 dirty skip 기록 → subagent 는 `queued` 만 처리.

기존 spec C7 의 Agent dispatch 그대로 사용:
- `subagent_type`: `general-purpose`
- `name`: `vis-backlink-<short-hash>`
- `run_in_background`: `true`
- `prompt`: 기존 spec C2 서브루틴 + config + state JSON 경로 + queued 리스트

### NC4. Skip-Prompt UX

```
⚠️ backward skip 추천 — <근거 1>; <근거 2>
   대상 후보 (자동 제외 적용 후): X1, X2, ... (총 N건)
   강제 진행하시겠습니까? [y/N]
```

응답 처리:
- `y` 또는 `Y` → NC3 fallthrough (state reason: `user_override_skip`)
- `N`, `n`, Enter → exit (state phase=`user_skipped`, history/ 직행)
- 명령어 환경에서 stdin 응답 timeout 없음 (Claude 대화 응답 기다림 — Claude Code 표준)

### NC5. Proceed-Inline UX

```
🔗 backward dispatched — <근거 요약>, N건 대상 (job=<job_id>)
   상태 조회: /vis-backlink-status
```

근거 요약 예시:
- `Top 5 평균 0.71, 제외 후 4건 대상` (정상)
- `Top 5 평균 0.71, 제외 후 4건 대상 (1건 dirty skip)` (per-file dirty 일부)

### CHG1. CLAUDE.md `<when-creating-obsidian-document>` 변경

**제거 대상**:
- 사전 가드 전체 (0번 ENV_DISABLED, 1번 ENV_DIRTY_TREE, 2번 state_dir 부트스트랩, 3번 동시성)
- 분기 (`.trusted` 마커 gate)
- Dry-run 프로시저 (Flow 1)
- Async dispatch 프로시저 (Flow 2)
- X 처리 서브루틴 (C2)
- 완료 · 정리 섹션
- 에러 카탈로그

**유지 대상**:
- Forward 부분 (자기 문서에 Related Notes 추가)

**추가 footer**:
> **Backward Related Notes**: 이제 `/obsidian:add-tag` 또는 `/obsidian:add-tag-and-move-file` 의 마지막 단계에서 `vis-backlink-trigger` 스킬이 처리합니다. 자세한 동작은 `~/git/vault-intelligence/docs/superpowers/specs/2026-04-26-vis-backlink-smart-trigger-design.md` 참조.

### CHG2. 명령어 두 개 변경

`~/.claude/commands/obsidian/add-tag.md` 와 `~/.claude/commands/obsidian/add-tag-and-move-file.md` 양쪽 모두에 마지막 step 추가:

```markdown
N. **Backward Related Notes 트리거** (관련 문서들의 Related Notes 갱신)
   - 위 단계 완료 후 `vis-backlink-trigger` 스킬을 invoke (`Skill: vis-backlink-trigger`, args=A_path)
   - 휴리스틱 평가 결과에 따라 자동 진행 또는 사용자 prompt
   - `--recursive` 모드에서는 이 단계 skip (대량 처리 시 vis daemon 부하 ↑, 발화 가치 ↓)
```

### REUSE. 기존 spec 컴포넌트 (변경 없음)

- C2: X 처리 서브루틴 (subagent 가 실행)
- C3: `## Related Notes` 섹션 파서
- C4: 자동 제외 필터 (NC2 의 S4 신호가 이 필터 결과 활용)
- C5: Rollback Buffer
- C7: Background Dispatch Wrapper
- C8: 동시성 제어 (active/*.json polling)
- C9: 결과 표시 정책
- C10: 상태 JSON 스키마
- C11: vis-backlink-status 스킬

### REMOVED. 기존 spec 에서 제거되는 컴포넌트

- C1: forward+backward 통합 훅 구조 → forward only 로 단순화
- C6: Dry-run 보고 포맷 → 휴리스틱 추천이 대체 (v2 후보로 보존)
- `.trusted` 마커 + 첫 실행 sync dry-run 흐름

## 7. Data Flow

### Flow A — Proceed 추천 (가장 흔함, 약 70%)

```
t=0    사용자: /obsidian:add-tag-and-move-file note.md
t=0    명령어: 태그 부여 + 파일 이동 + forward
t=2s   명령어: Skill: vis-backlink-trigger (note.md)
t=2s   trigger: .disabled 미존재 OK
t=2s   trigger: vis /health OK
t=3s   trigger: vis /search(note) → Top 5 [B,C,D,E,F]
t=3s   trigger: heuristic
         S4: 자동 제외율 20% (1/5) → veto 안함
         S5: A frontmatter draft? false → veto 안함
         결정: PROCEED (근거: S3 Top 5 평균 0.71)
t=4s   trigger: per-file dirty (B·C·E·F clean, D dirty)
         queued=[B,C,E,F], skipped_dirty=[D]
t=4s   trigger: state JSON 작성 (active/<job>.json, phase=dispatched)
t=4s   trigger: Agent dispatch (run_in_background=true)
t=4s   메인 Claude 출력:
         🔗 backward dispatched — Top 5 평균 0.71, 4건 대상 (1건 dirty skip)
            (job=20260426-153022-note)
t=4s   메인 Claude: 즉시 해제 ← 사용자는 다음 작업 가능
       (background)
t=4-30s subagent: B → C → E → F 순차 (기존 C2 서브루틴)
t=30s   subagent: state phase=completed, mv active → history
```

### Flow B — Skip 추천, 사용자 confirm (Enter)

```
t=2s   명령어 → trigger
t=3s   trigger: heuristic
         S4: 자동 제외율 80% (4/5 → work-log/draft) → VETO
         결정: SKIP (근거: S4)
t=3s   trigger 출력:
         ⚠️ backward skip 추천 — 자동 제외율 80% (Top 5 중 4건이 work-log/draft)
            대상 후보: C.md (총 1건)
            강제 진행하시겠습니까? [y/N]
       사용자: Enter (또는 N, n)
t=Δ    trigger: state 기록 (phase=user_skipped, history/ 직행), exit
t=Δ    메인 Claude: "ℹ️ backward skip 확정 (사용자)" → 즉시 해제
```

### Flow C — Skip 추천, 사용자 강제 진행 (y)

```
t=Δ    사용자: y
t=Δ    trigger: Flow A 의 t=4s 부터 그대로 fallthrough
         (per-file dirty → dispatch → 즉시 해제)
       state JSON 의 reason 필드: "user_override_skip"
```

### Flow D — `.disabled` 마커 ON

```
t=2s   trigger: .disabled 존재 → ENV_DISABLED
t=2s   메인 Claude: "ℹ️ backward 비활성화 (재활성화: /vis-backlink-toggle on)"
       (휴리스틱 평가도 안 함, vis /search 호출도 안 함 → 비용 zero)
```

### Flow E — vis daemon down

```
t=2s   trigger: .disabled 미존재 OK
t=7s   trigger: curl /health 5초 timeout → ENV_VIS_DOWN
t=7s   메인 Claude: "⚠️ vis daemon 응답 없음 — backward 생략 (visd start 후 재시도)"
```

### Flow F — 연속 호출 (이전 backward 진행 중)

```
t=0    사용자: /obsidian:add-tag-and-move-file note2.md (직전 note1 backward 가 active)
t=2s   trigger: 사전 가드 0·1 통과
t=3s   trigger: 동시성 체크 active/*.json 발견 → 2초 polling
t=5s   여전히 active → "선행 backward job 대기 중" 1회 알림 + 계속 polling
t=8s   직전 job phase ∈ {completed, partial_failure, user_skipped, crashed} 감지 → polling 해제
t=8s   trigger: 휴리스틱 평가 → dispatch (Flow A 의 t=3s 부터)
       (P1.a 순차 실행 — 기존 spec C8 정책 유지)
```

### Flow G — `--recursive` 모드 (add-tag 디렉토리 일괄)

```
t=0    사용자: /obsidian:add-tag 003-RESOURCES/ --recursive
t=0    명령어: 디렉토리 스캔, 각 파일 태그 부여 (forward 도 skip — 기존 정책)
t=N    명령어: vis-backlink-trigger 호출 자체 SKIP (CHG2 정책)
       (대량 처리 시 발화 가치 ↓, vis daemon 부하 ↑)
```

### 상태 전이 다이어그램

```
                    [.disabled?] ──yes──> ENV_DISABLED (terminal)
                         │ no
                         ▼
                    [vis health?] ──fail──> ENV_VIS_DOWN (terminal)
                         │ ok
                         ▼
                    [active job?] ──yes──> polling (max 5s, crashed 자동 정리)
                         │ no                    │
                         ▼                       │
                    [heuristic] ◄────────────────┘
                         │
                ┌────────┴────────┐
                ▼                 ▼
            PROCEED            SKIP
                │                 │
                │            [y/N prompt]
                │            ┌────┴────┐
                │            ▼         ▼
                │           y         N/Enter
                │            │         │
                ▼            ▼         ▼
        [per-file dirty]  (fallthrough) user_skipped (terminal)
                │
                ▼
        [Agent dispatch]
                │
                ▼
        dispatched → (subagent) → completed/partial_failure/crashed
```

### 핵심 SLA

| Flow | 메인 Claude blocking | 비고 |
|---|---|---|
| A (proceed) | ≤ 4초 | vis /search + heuristic + per-file dirty + state 작성 |
| B (skip → 사용자 N) | heuristic + 사용자 응답 | 사용자 의존 |
| C (skip → 사용자 y) | A 와 동일 | fallthrough |
| D (.disabled) | ≤ 1초 | 마커 체크만 |
| E (vis down) | ≤ 7초 | timeout |
| F (polling) | heuristic + max 5초 polling | 직전 job 의존 |
| G (--recursive) | 0초 | 호출 자체 skip |

## 8. Error Handling

### 8.1 에러 카탈로그 (변경 사항)

| 코드 | 패치 1 (기존) | 패치 2 (변경) |
|---|---|---|
| `ENV_DISABLED` | 사전 가드 0 | 그대로 (trigger 스킬 진입 직후 평가) |
| `ENV_DIRTY_TREE` | 사전 가드 1 (vault 전체) | **폐기** — per-file `FILE_DIRTY_SKIP` 으로 대체 |
| `ENV_VIS_DOWN` | 사전 가드 1 | 그대로 (사전 가드 1 위치) |
| `ENV_NO_TRUSTED` | dry-run 진입 트리거 | **폐기** (`.trusted` 마커 자체 폐기) |
| `FILE_DIRTY_SKIP` | (없음) | **신규** — per-file 단위, 그 X 만 skip, error 아닌 정상 skip |
| `USER_SKIPPED` | (없음) | **신규 phase** — 사용자가 prompt 에 N 응답, history/ 직행 |
| `DATA_PARSE_FAIL` | C3 일탈 | 그대로 (subagent 내부) |
| `DATA_FILE_MISSING` | Read 실패 | 그대로 |
| `DATA_SELF_REFERENCE` | filter | 그대로 |
| `LLM_CONTEXT_FULL` | 내부 | 그대로 |
| `LLM_DESC_GEN_FAIL` | 응답 파싱 | 그대로 |
| `IO_WRITE_FAIL` | MultiEdit | 그대로 |
| `CONCURRENT_DISPATCH` | active/ 존재 | 그대로 |
| `SUBAGENT_CRASH` | claude-code | 그대로 |

### 8.2 사용자 메시지 (한눈 표)

| 상황 | 메시지 형식 | tone |
|---|---|---|
| `.disabled` ON | `ℹ️ backward 비활성화 (재활성화: /vis-backlink-toggle on)` | info |
| vis daemon down | `⚠️ vis daemon 응답 없음 — backward 생략 (visd start 후 재시도)` | warning |
| heuristic proceed | `🔗 backward dispatched — Top 5 평균 0.71, 4건 대상 (job=...)` | info |
| heuristic skip 추천 | `⚠️ backward skip 추천 — <근거>. 강제 진행? [y/N]` | warning + prompt |
| 사용자 N/Enter | `ℹ️ backward skip 확정 (사용자)` | info |
| 사용자 y | (proceed 메시지로 fallthrough, reason: user_override) | info |
| Top 5 일부 dirty | `🔗 backward dispatched — 3건 대상 (1건 dirty skip)` | info |
| 직전 job 대기 | `⏳ 선행 backward job 대기 중 (5초 max)` | info |
| subagent crash 자동 정리 | `🧹 crashed job 자동 정리: <job_id>` | info |

### 8.3 복구 전략

1. **Terminal errors** (ENV_DISABLED, ENV_VIS_DOWN, USER_SKIPPED): backward 진행 안 함. forward 는 영향 없음. 재시도는 다음 명령어 호출 시 자동.
2. **Per-X errors** (FILE_DIRTY_SKIP, DATA_*, IO_WRITE_FAIL): 해당 X 만 skip, 나머지 정상 진행. state JSON 에 사유 기록. 사용자 액션 불필요.
3. **Crash recovery**: 다음 trigger 호출의 사전 가드 2 단계에서 `phase=crashed` 감지 시 자동 `mv active → history` + 인라인 알림.
4. **Job log 보존**: `history/` 30개 초과 시 가장 오래된 것부터 삭제 (기존 정책).

### 8.4 원자성 / 안전망

- state JSON 쓰기: tmp → rename (atomic, POSIX)
- MultiEdit: 단일 X 파일 단위 원자성 (Claude Code 보장)
- 부분 실패 시 `partial_failure` phase + 성공한 X 들은 commit 상태 유지 (rollback 안 함 — 사용자 git 워크플로우 침해 방지)
- 사용자가 backward 변경을 되돌리고 싶으면: `git diff` → `git checkout -- <X>` (수동, 명시적)

### 8.5 Out of scope (v2 후보)

- 자동 rollback (실패 시 backward 변경 일괄 되돌리기) — git stash 기반 wrapping 필요
- LLM 비용 sentinel — 현재는 fallback 으로 충분
- 휴리스틱 가중치 학습 — 사용자 override 패턴 분석 → 임계값 자동 조정

## 9. Testing

### 9.1 환경

- 샌드박스: `~/git/vault-intelligence/sandbox/vault-test/` (기존 패치 1 픽스처 재사용)
- 테스트 vis daemon: 별도 포트
- 가상 명령어: `add-tag-and-move-file` 호출을 시뮬레이션하는 스크립트

### 9.2 케이스

| ID | 케이스 | 기대 동작 |
|---|---|---|
| **T6.1** | 정상 proceed | Top 5 모두 일반 문서 + clean → PROCEED 자동, 4초 내 dispatch |
| **T6.2** | hard veto S4 (자동 제외율 80%) | SKIP 추천, prompt 표시, Enter → user_skipped phase |
| **T6.3** | hard veto S5 (frontmatter draft) | SKIP 추천, prompt 표시, y → user_override_skip 으로 fallthrough |
| **T6.4** | per-file dirty 일부 | Top 5 중 1건 dirty → 그 X skipped_dirty, 나머지 dispatch |
| **T6.5** | `.disabled` ON | ENV_DISABLED, vis /search 호출 안 됨 (비용 zero 검증) |
| **T6.6** | vis daemon down | ENV_VIS_DOWN, 7초 내 timeout, 인라인 알림 |
| **T6.7** | 동시성 (직전 job active) | polling 5초 max, crashed job 자동 정리 |
| **T6.8** | --recursive 모드 | trigger 호출 자체 skip, state JSON 생성 안 됨 |
| **T6.9** | 휴리스틱 신호 명세 검증 | uncommitted A 의 frontmatter draft 미명시 → S5 발화 안 함 (사용자 지적 케이스) |
| **T6.10** | 사용자 메시지 정확성 | 8.2 표의 모든 메시지가 1:1 매칭 |

### 9.3 성능 목표

| 지표 | 목표 | 측정 방법 |
|---|---|---|
| Flow A 메인 blocking | ≤ 4초 | 100회 평균 |
| 발화율 (proceed 비율) | ≥ 70% | 실 vault 1주 운영 데이터 |
| skip 추천 정확도 | 사용자 강제 진행 ≤ 10% | 1주 prompt 응답 통계 |
| 비용 zero (Flow D) | vis /search 호출 0회 | 로그 검증 |

### 9.4 테스트 순서

1. NC2 (heuristic) 단위 테스트 — 각 신호 발화 조건 검증
2. NC3 (per-file dirty) 단위 테스트 — A 무시, X dirty 검출
3. NC4·NC5 UX 시나리오 — Flow A·B·C 메시지 매칭
4. 사전 가드 시나리오 — Flow D·E·F
5. CHG1·CHG2 통합 — CLAUDE.md + 명령어 수정 후 실 호출
6. T6.9 회귀 — 사용자 지적 케이스 명시적 검증

### 9.5 프로덕션 롤아웃

1. 패치 2 spec 승인 → writing-plans 스킬로 구현 plan 작성
2. 샌드박스 T6.1~T6.10 통과
3. 프로덕션 vault 에서 첫 1~2회는 사용자가 backward 결과 (state JSON + git diff) 를 직접 확인하며 운영 (모니터링 모드 — 별도 도구 없이 수동)
4. 정상 동작 확인 → 전면 활성화
5. 1주 운영 후 발화율 + 추천 정확도 측정 → 임계값 (S4 60%) 튜닝 여부 결정

## 10. Implementation Path Summary

1. **NC1**: `~/.claude/skills/vis-backlink-trigger/SKILL.md` 신설
2. **NC2~NC5**: 스킬 본문에 휴리스틱 평가기 + per-file dirty + UX 구현
3. **CHG1**: `~/.claude/CLAUDE.md` `<when-creating-obsidian-document>` 블록 축소 (forward only)
4. **CHG2**: `~/.claude/commands/obsidian/add-tag.md` + `add-tag-and-move-file.md` 마지막 step 추가
5. **샌드박스 T6.1~T6.10 시나리오** 작성 + 수동 검증
6. **프로덕션 롤아웃** (9.5)

구체적 tasks 분해는 **writing-plans skill** 에서 수행.

## 11. Open Questions / v2 Ideas

- **v2a**: 휴리스틱 가중치 학습 — 사용자 override (`y` 강제 진행) 패턴 누적 → S4 임계값 자동 조정
- **v2b**: dry-run preview 옵션 (`--preview`) — 휴리스틱 proceed 추천 시에도 미리보기 표시 (옵트인)
- **v2c**: 더 정교한 신호 — Top 5 중 A 와 동일 디렉토리 비율, recently-modified X 비율 등
- **v2d**: backward 자동 rollback — git stash 기반 안전 wrapping
- **v2e**: vault-intelligence CLI 통합 — `vis backlink trigger <path>` 명령어로 외부 도구에서 호출 가능

---

**승인**: 2026-04-26 msbaek (대화 기반 brainstorming Q1~Q6 결정 + 섹션별 검토 + 시각화 압축본 ok)
