# T6.5/T6.6/T6.7 — vis-backlink-trigger 사전 가드 시나리오

## 전제

- `scripts/sync-sandbox.sh` 실행으로 `/tmp/vault-test/` 최신화
- test vis daemon 실행: `bash scripts/start-test-vis.sh`

---

## T6.5 — ENV_DISABLED (비용 zero 검증)

### 준비
1. `.disabled` 마커 생성: `touch ~/.claude/state/vis-backlink/.disabled`
2. vis daemon 요청 로그 스냅샷:
   `ls ~/.claude/logs/vis-backlink-*.log 2>/dev/null | head -1 | xargs wc -l 2>/dev/null || echo "0"`

### 실행
사용자 프롬프트:
> "`/tmp/vault-test/001-INBOX/test-disabled.md` 파일에 태그 붙이고 정리해줘.
> vis daemon 은 localhost:8742 사용. vis-backlink-trigger 의 사전 가드 0 테스트."

### 검증
- [ ] 명령어 실행 후 인라인 메시지에 `backward 비활성화` 포함
- [ ] 메시지에 `재활성화: /vis-backlink-toggle on` 안내 포함
- [ ] vis `/search` 호출이 **0회** 발생 (logs 카운터 변화 없음 — 비용 zero)
- [ ] `~/.claude/state/vis-backlink/active/` 에 새 job JSON 없음
- [ ] forward 는 정상 실행됨 (test-disabled.md 에 `## Related Notes` 섹션 삽입됨)

### 복구
```bash
rm ~/.claude/state/vis-backlink/.disabled
```

---

## T6.6 — ENV_VIS_DOWN (daemon 응답 없음)

### 준비
1. test vis daemon 중단: `kill $(cat /tmp/vis-test-daemon.pid 2>/dev/null) 2>/dev/null || true`
2. `.disabled` 마커 없음 확인: `[ ! -f ~/.claude/state/vis-backlink/.disabled ] && echo "OK"`

### 실행
사용자 프롬프트:
> "`/tmp/vault-test/001-INBOX/test-vis-down.md` 에 태그 붙이고 정리해줘.
> vis daemon 은 localhost:8743 (존재하지 않는 포트) 사용."

### 검증
- [ ] 5초 이내에 timeout 발생
- [ ] 인라인 메시지에 `vis daemon 응답 없음` 포함
- [ ] `visd start 후 재시도` 안내 포함
- [ ] `~/.claude/state/vis-backlink/active/` 에 새 job JSON 없음
- [ ] forward 는 정상 실행됨
- [ ] 전체 blocking 7초 이내

---

## T6.7 — 동시성 (직전 backward job active)

### 준비
1. active/ 에 dummy job JSON 생성:
   ```bash
   mkdir -p ~/.claude/state/vis-backlink/active
   cat > ~/.claude/state/vis-backlink/active/dummy-20260426-000000-test.json << 'EOF'
   {"job_id": "dummy-20260426-000000-test", "phase": "processing", "started_at": "2026-04-26T00:00:00Z", "updated_at": "2026-04-26T00:00:00Z", "source": "test", "progress": {"total": 5, "done": 0, "failed": 0}, "targets": []}
   EOF
   ```

### 실행
사용자 프롬프트:
> "`/tmp/vault-test/001-INBOX/concurrent-test.md` 태그 붙이고 정리해줘."

### 검증
- [ ] SKILL.md 가 active/ 에 job 있음을 감지
- [ ] 2초 polling 시작 (즉시 dispatch 안 함)
- [ ] 5초 후 `⏳ 선행 backward job 대기 중 (5초 max)` 알림 1회 출력
- [ ] dummy job 의 phase 를 `completed` 로 변경 후 polling 해제됨:
  ```bash
  python3 -c "
  import json
  f = '$HOME/.claude/state/vis-backlink/active/dummy-20260426-000000-test.json'
  d = json.load(open(f)); d['phase'] = 'completed'
  json.dump(d, open(f, 'w'))
  "
  ```
- [ ] polling 해제 후 정상 휴리스틱 평가 → dispatch 진행
- [ ] phase=completed 된 dummy job 이 history/ 로 이동됨

### 복구
```bash
rm -f ~/.claude/state/vis-backlink/active/dummy-20260426-000000-test.json
rm -f ~/.claude/state/vis-backlink/history/dummy-20260426-000000-test.json
```

---

## 수동 시뮬레이션 결과

### 2026-04-26 — SKILL.md 사전 가드 구현 완료 (논리 검증)

- **T6.5 (ENV_DISABLED)**: Step 1 에서 `.disabled` 마커 확인 → `DISABLED` 출력 → 즉시 종료. vis /search 미호출 (비용 zero). forward 는 스킬 호출 전 명령어에서 완료됨 → 영향 없음. ✅ 논리 검증 통과
- **T6.6 (ENV_VIS_DOWN)**: Step 2 에서 `curl --max-time 5` → 5초 timeout → 알림 + 종료. ✅ 논리 검증 통과
- **T6.7 (동시성)**: Step 3 에서 active/*.json 감지 → 2초 polling × max 5초 → completed/crashed 시 해제. ✅ 논리 검증 통과

실제 Claude 세션에서 end-to-end 검증은 Task 9 E2E 시나리오에서 수행.
