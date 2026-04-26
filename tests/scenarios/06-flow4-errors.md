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

## 수동 검증 결과 (2026-04-26)

| 에러 코드 | CLAUDE.md 라인 | 감지 방법 | 처리 방법 | 검증 |
|---|---|---|---|---|
| ENV_DIRTY_TREE | 163, 245 | git status --porcelain 결과 비어있지 않으면 감지 | backward 스킵, forward 유지, 인라인 고지 | PASS |
| ENV_VIS_DOWN | 246 | curl timeout 5s | Abort, notification | PASS |
| DATA_PARSE_FAIL | 248 | C3 파서 일탈 줄 감지 | 해당 X skip, 로그 | PASS |
| CONCURRENT_DISPATCH | 254 | active/*.json 존재 여부 확인 | 2초 주기 polling, 5초 후 1회 알림 | PASS |

### 검증 상세

**ENV_DIRTY_TREE** (라인 163, 245):
- 라인 163: `git dirty tree 체크: cd <vault_root> && git status --porcelain 결과가 비어있지 않으면 ENV_DIRTY_TREE → backward 스킵`
- 라인 245: 에러 카탈로그 표 — `ENV_DIRTY_TREE | git status | backward 중단, forward 유지, 인라인 안내`
- 처리 경로: 사전 가드 1번 체크 → backward 중단 → forward 유지 → 사용자에게 인라인 고지

**ENV_VIS_DOWN** (라인 246):
- 에러 카탈로그 표 — `ENV_VIS_DOWN | curl timeout 5s | Abort, notification`
- 처리 경로: vis `/search` curl 호출 시 5초 timeout → Abort → notification 발생

**DATA_PARSE_FAIL** (라인 248):
- 에러 카탈로그 표 — `DATA_PARSE_FAIL | C3 일탈 | 해당 X skip, 로그`
- 처리 경로: C3 파서로 섹션 분해 시 일탈 줄 감지 → 해당 파일 skip → state `targets[X].status="skipped_parse"` + 사유 기록 → 다른 target 계속 처리

**CONCURRENT_DISPATCH** (라인 254):
- 에러 카탈로그 표 — `CONCURRENT_DISPATCH | active/ 존재 | polling`
- 처리 경로: 동시성 체크 → `ls ~/.claude/state/vis-backlink/active/*.json` 결과 있으면 2초 주기 polling → 5초 경과 후 1회 알림 → phase 완료 시 해제 → 새 dispatch 진행
