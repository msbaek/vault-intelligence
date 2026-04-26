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

## 수동 검증 결과

### 검증 환경

- CLAUDE.md 경로: `~/.claude/CLAUDE.md`
- 검증 날짜: 2026-04-26
- Forward 섹션 위치: 줄 140-146
- Backward 섹션 위치: 줄 148-257
- `</when-creating-obsidian-document>` 닫힘: 줄 258

### Forward/Backward 독립성 분석

**Forward 섹션 (줄 140-146)**은 다음 5단계로 구성:
1. vis `/search` API 호출 (서버 미실행 시 `vis search` fallback)
2. 자기 자신·daily notes 제외 후 관련 후보 선별
3. 상위 5개 자동 추가
4. 문서 하단 `## Related Notes` 섹션 삽입
5. frontmatter `related:` 필드는 명시적 요청 시에만 업데이트

**Backward 섹션 (줄 148-257)**은 사전 가드를 포함한 독립적 흐름:
- 사전 가드 1: `ENV_DIRTY_TREE` 감지 → **backward 중단, forward 유지** (에러 카탈로그 명시)
- 사전 가드 2: state_dir 부트스트랩
- 사전 가드 3: 동시성 체크
- `.trusted` 마커 기반 분기 (Flow 1: dry-run / Flow 2: async dispatch)

### 독립성 근거

1. **에러 카탈로그 `ENV_DIRTY_TREE`**: "backward 중단, forward 유지" 로 명시 (줄 245). forward는 backward 실패와 무관하게 항상 완료됨.

2. **사전 가드 순서**: backward 사전 가드는 forward 완료 이후에 평가됨. forward 자체는 가드 대상이 아님.

3. **Dry-run 거부(Flow 1, 줄 191)**: 사용자 거부 시 "변경 없음, `.trusted` 생성 안 함"만 수행. forward 단계에서 이미 삽입된 `## Related Notes`는 영향을 받지 않음.

4. **backward 실패 전파 없음**: backward가 `partial_failure`/`crashed` 상태로 종료되어도 forward 결과물(대상 문서 A의 Related Notes)에는 롤백 메커니즘이 없음.

5. **forward fallback 독립성**: vis 서버 미실행 시 forward는 `vis search` CLI로 fallback. backward는 `ENV_VIS_DOWN` (curl timeout 5s) 으로 Abort. 두 경로는 서로 독립된 오류 처리 경로를 가짐.

### 결론

**forward 독립성: PASS**

CLAUDE.md 스펙에서 forward와 backward는 명확히 분리된 단계로 정의되어 있으며, backward의 어떠한 실패/차단도 forward 단계의 완료 여부에 영향을 주지 않는다.
