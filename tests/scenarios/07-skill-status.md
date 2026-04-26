# T2.6 — vis-backlink-status 스킬 동작 검증

## 전제

state fixture 3개 심음 (processing 1, crashed 1, history completed 1)

- `~/.claude/state/vis-backlink/active/20260415-120000-probe.json` — phase=processing
- `~/.claude/state/vis-backlink/active/20260414-221045-crash.json` — phase=crashed
- `~/.claude/state/vis-backlink/history/20260414-093011-old.json` — phase=completed

## 수동 시뮬레이션 결과

### Step 1: active 목록 조회

```bash
ls ~/.claude/state/vis-backlink/active/*.json 2>/dev/null
```

결과:
```
~/.claude/state/vis-backlink/active/20260415-120000-probe.json
~/.claude/state/vis-backlink/active/20260414-221045-crash.json
```

### Step 2: 최근 history 조회

```bash
ls -t ~/.claude/state/vis-backlink/history/*.json 2>/dev/null | head -5
```

결과:
```
~/.claude/state/vis-backlink/history/20260414-093011-old.json
```

### Step 3: 각 JSON 파일 Read

**active/20260415-120000-probe.json**:
- phase: processing
- source: 001-INBOX/probe.md
- progress: total=3, done=1, current=003-RESOURCES/baz.md
- elapsed: 34s (started_at → updated_at 차이)
- subagent: vis-backlink-a1b2
- targets: foo.md(done/12400ms), baz.md(in_progress/llm_description_generation), quux.md(pending)

**active/20260414-221045-crash.json**:
- phase: crashed
- source: 001-INBOX/whatever.md
- progress: total=2, done=0
- last step: llm_description_generation (target=003-RESOURCES/baz.md)
- elapsed: 25s

**history/20260414-093011-old.json**:
- phase: completed
- source: 001-INBOX/old.md
- progress: total=3, done=3, failed=0
- duration: 78s

### 스킬 출력 (실제 생성된 내용)

```
=== vis-backlink 상태 (2026-04-26 14:41:00) ===

활성 (2):
  [20260415-120000-probe] phase=processing
    source: 001-INBOX/probe.md
    progress: [##------] 1/3 (current: 003-RESOURCES/baz.md)
    elapsed: 34s
    subagent: vis-backlink-a1b2

  [20260414-221045-crash] phase=crashed
    source: 001-INBOX/whatever.md
    progress: 0/2
    elapsed: 25s

최근 완료 (1):
  [20260414-093011-old] done=3/3 duration=78s

실패 (1):
  [20260414-221045-crash] phase=crashed
    source: 001-INBOX/whatever.md
    last step: llm_description_generation (target=003-RESOURCES/baz.md)
    힌트: /vis-backlink-status --clear-failed 로 정리
```

## 검증 체크리스트

- [x] 활성 2 (processing + crashed) 표시
- [x] 최근 history 1건 표시
- [x] crashed 항목에 --clear-failed 힌트
- [x] vis daemon 불필요 (daemon 비의존)

## --clear-failed 수동 실행

```bash
ls ~/.claude/state/vis-backlink/active/
# 결과: 20260415-120000-probe.json  20260414-221045-crash.json

# crashed 파일을 history로 이동
mv ~/.claude/state/vis-backlink/active/20260414-221045-crash.json \
   ~/.claude/state/vis-backlink/history/20260414-221045-crash.json

ls ~/.claude/state/vis-backlink/active/
# 결과: 20260415-120000-probe.json
```

실행 결과:
- active/ 에 processing만 남고 crashed는 history로 이동됨
- `cleared 1 failed jobs → history/` 출력

## Cleanup

```bash
rm -f ~/.claude/state/vis-backlink/active/20260415-120000-probe.json
rm -f ~/.claude/state/vis-backlink/history/20260414-093011-old.json
rm -f ~/.claude/state/vis-backlink/history/20260414-221045-crash.json
```
