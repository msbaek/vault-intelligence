# T6.8 — --recursive 모드에서 trigger skip 시나리오

## 목적

`/obsidian:add-tag <dir> --recursive` 실행 시 `vis-backlink-trigger` 스킬이 호출되지 않음을 확인.

## 전제

- `scripts/sync-sandbox.sh` 실행
- Task 8 (CHG2) 완료 후 실행 (명령어에 trigger 호출 추가된 상태)

## 실행

사용자 프롬프트:
> "`/tmp/vault-test/003-RESOURCES/` 디렉토리 전체 태그 붙여줘.
> `/obsidian:add-tag /tmp/vault-test/003-RESOURCES/ --recursive`"

## 검증

- [ ] 명령어가 `--recursive` 모드로 실행됨
- [ ] 각 파일에 태그 부여 작업 완료
- [ ] `vis-backlink-trigger` 스킬이 호출되지 않음 (명령어 마지막 step skip)
- [ ] `backward` 관련 메시지 없음
- [ ] `~/.claude/state/vis-backlink/active/` 에 새 job JSON 없음
- [ ] `~/.claude/state/vis-backlink/history/` 에도 새 항목 없음

## 비교: --recursive 없이 단일 파일 처리 시

```bash
# 단일 파일이면 trigger 가 호출됨
# /obsidian:add-tag /tmp/vault-test/003-RESOURCES/foo.md
# → vis-backlink-trigger 호출 → 휴리스틱 평가 → dispatch
```

- [ ] `--recursive` 없는 단일 파일 처리 시 trigger 정상 호출됨 (대조)

## 수동 시뮬레이션 결과

(Task 8 CHG2 완료 후 기록)
