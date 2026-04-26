---
title: vis-backlink Reverse Update (Related Notes Compounding)
date: 2026-04-15
status: approved
scope: 패치 1 — 새 Obsidian 문서 생성 시 역방향 Related Notes 자동 업데이트
---

# vis-backlink Reverse Update Design

> **작업 home**: `~/git/vault-intelligence` repo. 본 스펙과 후속 plan · 구현 참고자료를 여기에 보관한다.
> 최종 산출물 설치 위치:
> - `~/.claude/CLAUDE.md` 의 `<when-creating-obsidian-document>` 블록 (글로벌 훅)
> - `~/.claude/skills/vis-backlink-status/SKILL.md` (글로벌 스킬)
> - 샌드박스 · 테스트 픽스처 · 운영 스크립트는 vault-intelligence 하위 디렉토리

## 1. Context & Motivation

현재 `~/.claude/CLAUDE.md` 의 `<when-creating-obsidian-document>` 훅은 **새 Obsidian 문서 A를 만들 때만** Related Notes 섹션을 삽입한다 (vis daemon `/search` 호출 후 Top 5를 `## Related Notes` 로 추가). 이는 **일방향**이다: 새 A가 들어와도 기존 관련 문서 B·C·D의 Related Notes 는 갱신되지 않아 **stale 상태**로 남는다.

Karpathy 의 "compounding wiki" 원칙을 차용하면, 새 문서 추가가 기존 연결을 **강화**해야 한다. 구조적으로 저비용인 변형이 **"새 문서 생성 시 vis Top 5 각각의 Related Notes 도 역방향 업데이트"** 이다.

### 현 vault 통계 (2026-04-15)

- 전체 `.md` 파일: 3,490개
- `## Related Notes` 섹션 보유: 107개 (3.1%)
- 역방향 대상의 **96.9%** 는 섹션 부재 → 섹션 신설 정책 필수

## 2. Goal

새 문서 A 를 Claude 가 생성할 때, A 의 vis Top 5 기존 문서 각각에 대해 **그들의 현재 Top 5** 로 Related Notes 섹션을 **full refresh** 한다. 이로써 vault 의 연결 compounding 이 양방향으로 축적된다.

**성공 기준**: 새 문서 1건 생성 시 최대 5개 기존 문서의 Related Notes 섹션이 최신 상태로 유지·생성되며, 메인 Claude 세션 blocking 은 2초 이내.

## 3. Non-Goals

- vault 전체 backfill (이미 존재하는 섹션 일괄 재계산) — v2 후보
- Obsidian 에서 직접 작성된 문서의 역방향 커버리지 — v2 catch-up 스크립트 후보
- 모순 감지 (contradiction flagging) — 별도 패치
- vis daemon 자체의 파일 쓰기 엔드포인트 — 이 설계는 daemon 을 read-only 로 유지

## 4. Design Decisions

| ID | 결정 | 선택값 | 근거 |
|---|---|---|---|
| Q1 | 역방향 대상 수 | **Top 5** | forward 대칭성, compounding 가속 |
| Q2 | 상한 처리 | **(c) Full refresh** | 항상 최신 상태 보장 |
| Q3 | 설명 생성 | **(b) 기존 보존 + 신규만 LLM** | 수동 편집 보호 + 비용 절감 |
| Q4 | 섹션 부재 시 | **(c) A 링크만 (minimal)** | 점진적, `bootstrap_mode=full` 로 전환 가능 |
| P1 | 동시성 | **(a) 순차 실행** | 단순·안전, v1 scope 적합 |
| P2 | 첫 실행 정책 | **(x) 영구 1회 sync dry-run** | `.trusted` 마커로 신뢰 획득 |
| — | 실행 주체 | **접근 B (CLAUDE.md 훅 확장 + Background Subagent)** | LLM 무료, 초기 비용 최소 |

## 5. Architecture

```
새 문서 A 생성
      │
      ▼
Main Claude
  ├─ forward (기존): vis /search(A) → A에 Related Notes 섹션 삽입
  │
  ├─ backward:
  │   ├─ .trusted 부재?    → 동기 dry-run → 사용자 승인 → 적용
  │   └─ .trusted 있음?     → Agent(run_in_background=true) dispatch
  │                          └→ 독립 컨텍스트 subagent 가 C2 서브루틴 수행
  │
  └─ 즉시 해제, 사용자는 다음 forward 작업 가능
                         │
                         ▼
Notification + state JSON (active/ → history/)
```

**책임 경계**

| 컴포넌트 | 역할 | 이 패치로 변경? |
|---|---|---|
| vis daemon | 검색만 (`/search`, `/health`, `/reindex`) | 아니오 (read-only 유지) |
| CLAUDE.md 훅 | 오케스트레이터 | **예** (backward 블록 추가) |
| Claude Code | 훅 수행자, subagent 디스패처 | 아니오 (도구는 동일) |
| Obsidian | 읽기·편집 | 아니오 |
| git | 안전망 | **예** (dirty tree 가드 신설) |

## 6. Components

### C1. 확장된 훅 구조 (`<when-creating-obsidian-document>`)

```yaml
forward:          # 기존
  - vis /search(A) → Top 5
  - A에 Related Notes 섹션 삽입

backward:         # 신규
  config:
    top_k: 5
    bootstrap_mode: "minimal"     # "minimal" | "full"
    exclude_patterns:
      - "work-log/*.md"
      - "ATTACHMENTS/**"
      - "<A-path>"                # self-exclude
      - frontmatter.draft == true
    first_run_policy: "sync_dryrun_once"   # .trusted 없으면 강제 sync
    concurrency: "sequential"     # P1.a
  steps:
    0: .disabled 마커 체크 → ENV_DISABLED 시 backward 스킵, forward 유지, 인라인 안내
    1: git dirty-tree guard
    2: active/*.json 있으면 polling (P1.a)
    3: .trusted 없으면 → sync dry-run 모드 (C6)
    4: .trusted 있으면 → Background Subagent dispatch (C7)
```

### C2. X 처리 서브루틴 (subagent 또는 메인이 수행)

```
입력: X_path
출력: X_path 변경 또는 skip 이유

1. Read(X_path) → 원본
2. parse_related_notes_section (C3)
   → (before_section, related_lines, after_section)
3. vis /search(X, top_k=5, rerank=true) → X 의 최신 Top 5
   자동 제외 필터 적용 (C4)
4. 각 링크 L 에 대해:
   - L in related_lines  → 기존 설명 재사용
   - else                → 설명 LLM 생성 (Q3.b)
5. bootstrap_mode=minimal AND 기존 섹션 없음
   → new_related_lines = [A 만]
6. assembled = before_section + "## Related Notes\n\n" + lines + after_section
7. MultiEdit(X_path, 원본 → assembled)
8. state JSON 업데이트: targets[X].status = "done"
```

### C3. `## Related Notes` 섹션 파서

- **섹션 시작**: `^## Related Notes\s*$`
- **섹션 종료**: 다음 `^## ` 또는 EOF
- **줄 문법**: `^-\s+\[\[(?P<link>[^\]]+)\]\](\s+—\s+(?P<desc>.+))?$`
- **일탈 줄**: 원본 보존 (주석/메모 가능성)
- **다중 줄 설명**: v1 범위 밖 → 파싱 실패 시 해당 파일 skip
- **image 링크** (`![[pic.png]]` 또는 확장자 있는 링크): Related Notes 대상 아님 → skip

### C4. 자동 제외 필터

| 대상 | 이유 |
|---|---|
| A 자신 | self-link 방지 |
| `work-log/**` | daily notes |
| `ATTACHMENTS/**` | 바이너리 asset |
| frontmatter `draft: true` | 초안 |

설정 가능. 기본값으로 4개 포함.

### C5. Rollback Buffer

별도 구조 없음. Claude 의 Read 결과가 대화 컨텍스트에 보존되어 수동 복원 가능. 궁극 안전망은 git.

### C6. Dry-run 보고 포맷 (첫 실행 전용)

```
역방향 Related Notes 업데이트 미리보기
새 문서: A = 001-INBOX/new-doc.md

역방향 대상 (vis Top 5, 자동 제외 적용 후):
  [1] B = 003-RESOURCES/foo.md     (섹션 있음)
  [2] C = 997-BOOKS/bar.md          (섹션 없음 → bootstrap minimal)
  [3] D = work-log/2026-04-14.md   (제외: work-log/**)
  [4] E = 003-RESOURCES/baz.md     (섹션 있음)
  [5] F = ATTACHMENTS/img.png      (제외: ATTACHMENTS/**)

실제 수정 대상: B, C, E

B 변경안 diff:
  - [[old]] — 설명 X  (제거)
  + [[A]]   — 새 설명 Y  (추가)
  = [[common]] — 설명 Z  (유지)

[계속 적용 / 취소 / 선택 적용]
```

### C7. Background Dispatch Wrapper

```yaml
Agent:
  type: "general-purpose"
  name: "vis-backlink-<hash>"
  run_in_background: true
  prompt: |
    새 문서 A = {A_path} 역방향 Related Notes 업데이트.
    대상 후보: {top5_candidates}
    자동 제외: {exclude_patterns}
    bootstrap_mode: {bootstrap_mode}
    state_json: {state_path}
    
    C2 서브루틴 엄격 수행. 단계마다 state JSON atomic rewrite.
    실패 시 C3~C5 정책 적용. 완료 시 {log_path} 에 [DONE] append.
```

### C8. 동시성 제어 (P1.a 순차)

```
새 문서 생성 시:
  1. ls ~/.claude/state/vis-backlink/active/*.json
  2. 있으면 polling 루프 (2초 주기)
  3. .phase in {completed, failed, partial_failure} 시 break
  4. 5초 경과 후에도 대기 중이면 사용자에게 1회 알림
  5. 완료 확인 후 새 dispatch
```

v2 대안: file-level mutex (현재 불필요).

### C9. 결과 표시 정책

| 경로 | 수단 |
|---|---|
| 동기 dry-run | 대화 내 diff 출력 + 대화형 승인 |
| 비동기 완료 | Claude Code notification + log + git diff |
| 실패 | notification + `/vis-backlink-status` 힌트 |

### C10. 상태 JSON 스키마

**저장**: `~/.claude/state/vis-backlink/` 하위 per-job 파일

```
active/<job_id>.json      # 진행 중 또는 실패 유지
history/<job_id>.json     # 성공 완료 (최근 30개)
.trusted                  # 동기 dry-run 1회 통과 마커
```

**스키마**:

```json
{
  "job_id": "20260415-104523-new-doc",
  "source": "001-INBOX/new-doc.md",
  "started_at": "2026-04-15T10:45:23+09:00",
  "updated_at": "2026-04-15T10:45:38+09:00",
  "phase": "processing",
  "subagent_name": "vis-backlink-a1b2",
  "progress": {
    "total": 3,
    "done": 1,
    "failed": 0,
    "current": "003-RESOURCES/baz.md"
  },
  "targets": [
    {
      "path": "003-RESOURCES/foo.md",
      "status": "done",
      "duration_ms": 12400,
      "changes": {"added": 2, "preserved": 3, "removed": 1}
    },
    {"path": "003-RESOURCES/baz.md", "status": "in_progress", "step": "llm_description_generation"},
    {"path": "997-BOOKS/bar.md", "status": "pending"}
  ],
  "log_path": ".claude/logs/vis-backlink-20260415.log"
}
```

**Write 권한**: 훅 메인 (dispatch 시), Subagent (처리 중), 스킬 (`--clear-failed` 만).
**Read 권한**: 스킬 (전부), 훅 메인 (동시성 체크).

### C11. Skill `/vis-backlink-status`

**위치**: `~/.claude/skills/vis-backlink-status/SKILL.md`

**Frontmatter**:

```yaml
---
name: vis-backlink-status
description: Use when user asks about background vis-backlink (reverse Related Notes update) progress. Reads ~/.claude/state/vis-backlink/ and reports active/recent/failed jobs with progress bars.
---
```

**트리거**: 슬래시 커맨드 `/vis-backlink-status [options]`, 자연어 ("vis-backlink 상태", "역방향 진행 어디까지", "백링크 작업 현황").

**동작**:

```
1. ls ~/.claude/state/vis-backlink/active/*.json
2. ls ~/.claude/state/vis-backlink/history/*.json | sort -r | head -5
3. 각 JSON Read + 집계
4. 출력 (진행률 bar, 현재 파일, 실패 강조)
5. 실패 있으면 --clear-failed 힌트 표시
```

**옵션**:

| 옵션 | 동작 |
|---|---|
| (없음) | 기본 요약 |
| `--clear-failed` | 실패 job 을 history/ 로 이동 |
| `--json` | 파싱된 전체 상태 덤프 |
| `--follow` | v2 예정 (미구현) |

**의존성**: Read, Bash(ls, jq, mv) 만. **LLM 호출 없음**, vis daemon 비의존.

## 7. Data Flow

### Flow 1: 첫 실행 (동기 dry-run)

```
Main Claude
├─ Write(A), forward 완료
├─ .trusted 부재 → 동기 모드
├─ 각 대상 parse + 설명 준비
├─ C6 diff 출력 → 사용자 승인
├─ 승인 → MultiEdit 순차 적용 → touch .trusted
└─ 거부 → 변경 없음, .trusted 생성 안 함
```

### Flow 2: 정상 비동기

```
Main Claude
├─ Write(A), forward 완료
├─ .trusted 있음, active/ 비어있음
├─ active/<id>.json 초기 기록 (phase=dispatched)
├─ Agent(run_in_background=true) dispatch
└─ 즉시 해제 ← 사용자 forward 계속

[Subagent]
├─ state phase=processing
├─ 각 X 순회: vis → parse → desc → MultiEdit → state update
├─ phase=completed → mv active/→history/
└─ notification + log [DONE]
```

### Flow 3: 연속 생성 (순차 대기)

```
t=0: A 생성 → #1 dispatch
t=5: B 생성 → active/*.json 1건 발견
     → polling (2s 주기, 5s 시 사용자 알림)
     → #1 완료 → #2 dispatch
```

**특징**: forward 자체는 블록 없음. backward 큐만 순차.

### Flow 4: 실패 시나리오

| 서브 | 상황 | 처리 |
|---|---|---|
| 4a | 개별 파일 parse 실패 | 해당 X skip, 다른 대상 계속, phase=partial_failure |
| 4b | dirty git tree | backward 스킵, forward는 진행 |
| 4c | subagent crash | phase=crashed 강제 기록, active/ 유지 |
| 4d | vis down | phase=vis_unavailable, abort |

### Flow 5: 상태 조회 (스킬 호출)

```
User: /vis-backlink-status
├─ 스킬이 active/, history/ JSON 읽음
├─ 집계 후 포맷 출력 (진행률 bar, 경과 시간, 실패 강조)
└─ 즉시 반환 (LLM 없음)
```

### 상태 전이

```
dispatched → processing → completed      (→ history/)
                       → partial_failure (→ active/ 유지)
                       → failed          (→ active/ 유지)
                       → crashed         (→ active/ 유지)
                       → skipped_*       (→ active/ 유지)
```

`completed` 만 자동 이동. 나머지는 사용자 검토 대기.

## 8. Error Handling

### E1. 에러 카탈로그

| 코드 | 발생 | 감지 | 복구 | 사용자 |
|---|---|---|---|---|
| `ENV_DISABLED` | 메인 가드 | `.disabled` 마커 | Abort (backward만), forward 유지 | 인라인 안내 |
| `ENV_DIRTY_TREE` | 메인 가드 | `git status` | Abort | 안내 |
| `ENV_VIS_DOWN` | Subagent curl | timeout 5s | Abort | Notification |
| `ENV_NO_TRUSTED` | 메인 체크 | `.trusted` 부재 | 동기 dry-run | 대화형 |
| `DATA_PARSE_FAIL` | Subagent | 포맷 일탈 | 해당 X skip | 로그 |
| `DATA_FILE_MISSING` | Subagent | 경로 없음 | skip | 로그 |
| `DATA_SELF_REFERENCE` | 필터 | vis 응답에 A | 조용히 제외 | 없음 |
| `LLM_CONTEXT_FULL` | Subagent | 내부 오류 | Abort | Notification |
| `LLM_DESC_GEN_FAIL` | Subagent | 응답 파싱 실패 | snippet fallback | 경고 |
| `IO_WRITE_FAIL` | MultiEdit | 권한/디스크 | skip | Notification |
| `CONCURRENT_DISPATCH` | 메인 | active/ 존재 | Polling | "대기 중" |
| `SUBAGENT_CRASH` | Claude Code | notification | phase=crashed | 수동 정리 |

### E2. 복구 전략

- **A. Abort with preservation**: 전체 중단, 이미 수정된 파일 롤백 없음 (각 수정은 독립적 valid)
- **B. Skip and continue**: 실패 X 한 개만 skip, 나머지 계속 → partial_failure
- **C. Silent handle**: 정상 동작의 일부 (SELF_REFERENCE, CONCURRENT_DISPATCH)
- **D. Fallback**: LLM 실패 → Q3.c snippet 사용으로 강등

### E3. 원자성

| 단계 | 수단 |
|---|---|
| state JSON | tmp → rename (atomic POSIX) |
| MultiEdit | Claude Code 자체 all-or-nothing |
| git | 사전 가드 + git diff 사후 확인 |
| 로그 | append-only |

### E4. Notification 수준

| 수준 | 예 | 형태 |
|---|---|---|
| Critical | vis down, subagent crash | 즉시 notification |
| Warning | parse 실패, partial_failure | 완료 시 집계 |
| Info | dirty tree | 메인 실행 중 인라인 메시지 |
| Debug | self-reference, concurrent dispatch | 로그만 |

### E5. Out of scope

- 메인 Claude 프로세스 kill
- vault 심볼릭 링크 깨짐
- `.trusted` 권한 문제
- Obsidian conflict resolution

## 9. Testing

### T1. 환경

**샌드박스**: `/tmp/vault-test/` 미니 vault (5-10개 md, 포맷 일탈 케이스 포함)
**테스트 vis**: `VIS_VAULT_PATH=/tmp/vault-test vis serve --port 8742`
**테스트 state**: `VIS_BACKLINK_STATE_DIR=/tmp/vis-backlink-state`

### T2. 케이스

| ID | 대상 | 핵심 검증 |
|---|---|---|
| T2.1 | C3 파서 | 정상 100%, 일탈 케이스 파일 손상 0건 |
| T2.2 | Flow 1 | dry-run diff, exclude 적용, 거부 시 파일 무변경, 승인 시 .trusted |
| T2.3 | Flow 2 | dispatch 후 메인 즉시 해제 (< 2초), state atomic update |
| T2.4 | Flow 3 | polling 후 순차 dispatch, #1↔#2 간격 ≤ 5초 |
| T2.5 | Flow 4 | 각 에러 코드별 state 정확 기록, git diff 손상 0 |
| T2.6 | 스킬 C11 | 활성/히스토리/실패 혼합 표시, --clear-failed 동작, daemon 비의존 |
| T2.7 | bootstrap_mode | minimal 1줄, full 5줄, 코드 변경 없이 전환 |
| T2.8 | 회귀 | 기존 forward 동작 유지, backward 비활성화 시 완전 무영향 |

### T3. 성능 목표

| 지표 | 목표 |
|---|---|
| Forward blocking | < 2초 |
| Backward 5 대상 완료 | < 90초 |
| Polling 오버헤드 | < 5초 |
| vis /search 1회 | < 500ms |
| 스킬 응답 | < 1초 |

### T4. 테스트 순서

```
1. 샌드박스 + test daemon
2. T2.8 회귀 (기존 깨지지 않음)
3. T2.1 파서
4. T2.2 Flow 1
5. T2.3 Flow 2
6. T2.6 스킬
7. T2.5 에러
8. T2.4 Flow 3
9. T2.7 bootstrap_mode
10. T3 성능
11. → production vault 첫 실행 (자연스러운 dry-run)
```

### T5. 프로덕션 롤아웃

```
[ ] 샌드박스 T2 전체 통과
[ ] 성능 T3 목표 달성
[ ] 회귀 T2.8 통과
[ ] CLAUDE.md diff 리뷰
[ ] SKILL.md 리뷰
[ ] production .trusted 부재 상태로 첫 생성 → dry-run 승인
[ ] /vis-backlink-status 로 첫 job 확인
[ ] 1주 실사용 후 history 분석 (실패율, 평균 소요)
```

## 10. Implementation Path Summary

1. **CLAUDE.md 편집**: `<when-creating-obsidian-document>` 블록 확장 (C1 ~ C9)
2. **SKILL.md 신설**: `~/.claude/skills/vis-backlink-status/SKILL.md` (C11)
3. **상태 디렉토리 부트스트랩**: `~/.claude/state/vis-backlink/{active,history}/` 생성 규칙은 훅 자체에 내장 (없으면 자동 mkdir)
4. **샌드박스 구축**: `/tmp/vault-test/` + test vis daemon
5. **T2 통과 후 production 첫 실행**

구체적 tasks 분해는 **writing-plans skill** 에서 수행.

## 11. Open Questions / v2 Ideas

- **v2a**: Obsidian 직접 작성 문서 catch-up 스크립트 (접근 C 추출)
- **v2b**: `--follow` 스트리밍 (현재 미구현)
- **v2c**: file-level mutex (현재 단순 polling 대체)
- **v2d**: 병렬 subagent (현재 P1.a 순차)
- **v2e**: `bootstrap_mode = "full"` 전환 후 관찰된 compounding 속도 측정
- **v2f**: 모순 감지 pass (Karpathy 원칙의 별도 기능)
- **v2g**: 수동 편집 보존 강화 (pinned 주석 지원)
- **v2h (구현됨)**: 사용자 토글 (`.disabled` 마커 + `/vis-backlink-toggle`) — backward 만 일시 정지. 사전 가드 0번으로 통합. 시나리오: `tests/scenarios/11-toggle.md`.

---

**승인**: 2026-04-15 msbaek (대화 기반 섹션별 검토 + 최종 ok)
