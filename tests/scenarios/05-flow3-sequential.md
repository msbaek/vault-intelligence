# T2.4 — Flow 3 sequential polling

> **설계 제약 (Risk R5):** 5초 경과 후 "대기 중" 1회 알림 이후에는 사용자가
> `/vis-backlink-status`를 수동 호출해야 함. v2d(병렬 subagent)에서 해결 예정.
> 이 제약으로 인한 UX 이슈는 FAIL이 아닌 known limitation으로 기록.

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

## Known Limitation (UX)

5초 polling 알림 이후 상태 확인은 수동:
```bash
/vis-backlink-status  # 또는
ls ~/.claude/state/vis-backlink/active/
```
이는 v2d에서 병렬 subagent로 해결 예정. 현재 sequential 방식은 안전성 우선 설계.

## 수동 검증 결과 (2026-04-26)

### Sequential Polling 로직 확인
- active/ 감지: ✅ (라인 165 — `ls ~/.claude/state/vis-backlink/active/*.json 2>/dev/null`)
- 2초 주기: ✅ (라인 165 — "2초 주기 polling")
- 5초 후 1회 알림: ✅ (라인 165 — "5초 경과 후에도 대기 중이면 '선행 backward job 대기 중' 1회 알림")
- phase 해제 조건: ✅ (라인 165 — `phase in {completed, failed, partial_failure}` 가 되면 해제)
- crashed 자동 해제: ✅ (라인 165 — `phase=crashed` 감지 시 `mv active/<id>.json history/<id>.json` 후 즉시 해제)

### Known Limitation 기록
- 5초 이후 수동 조회 필요: known limitation (v2d 예정)

### 결론
sequential polling 설계 일관성: PASS
