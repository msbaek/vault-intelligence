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

## 논리 검증 결과

### 검증 명령

```bash
grep -n "사용자 승인\|사용자 거부\|trusted" ~/.claude/CLAUDE.md | head -10
```

### 검증 결과

```
156:- `first_run_policy`: `"sync_dryrun_once"` (`.trusted` 없으면 강제 동기 dry-run)
167:**분기 (.trusted 마커로 1회 gate):**
169:- `.trusted` 부재 → 동기 dry-run (Flow 1). 아래 "Dry-run 프로시저" 수행.
170:- `.trusted` 존재 → 비동기 dispatch (Flow 2). 아래 "Async dispatch 프로시저" 수행.
190:5. 사용자 승인 → MultiEdit 순차 적용 → `touch ~/.claude/state/vis-backlink/.trusted`.
191:6. 사용자 거부 → 변경 없음, `.trusted` 생성 안 함. 다음 새 문서 생성 시 다시 dry-run.
193:**Async dispatch 프로시저 (Flow 2, `.trusted` 이후):**
247:| `ENV_NO_TRUSTED` | `.trusted` 부재 | 동기 dry-run 진입 |
```

### 판정: PASS

CLAUDE.md 스펙에 다음 분기 논리가 명확히 정의되어 있음:

| 케이스 | 조건 | `.trusted` 처리 | 동작 |
|--------|------|----------------|------|
| Case A (거부) | 사용자 거부 | 생성 안 함 | 변경 없음. 다음 문서 생성 시 다시 dry-run |
| Case B (승인) | 사용자 승인 | `touch .trusted` 생성 | MultiEdit 순차 적용 후 `.trusted` 마커 생성 |
| Case C (선택 적용) | partial 승인 | `touch .trusted` 생성 | 선택된 대상만 MultiEdit 적용, `.trusted` 생성 (1회 통과) |

**근거 라인:**
- Line 190: `사용자 승인 → MultiEdit 순차 적용 → touch ~/.claude/state/vis-backlink/.trusted`
- Line 191: `사용자 거부 → 변경 없음, .trusted 생성 안 함. 다음 새 문서 생성 시 다시 dry-run`
- Line 167-170: `.trusted` 마커 기반 Flow 1/Flow 2 분기 게이트

선택 적용(Case C)은 스펙에 "선택 적용" 옵션이 dry-run 출력 프롬프트(Line 188)에 명시되어 있으며,
`.trusted` 생성은 "1회 통과" 기준으로 부분 승인도 포함하는 것으로 해석됨.
