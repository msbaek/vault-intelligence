# T6.4 — Per-file Dirty 체크 시나리오

## 전제

- `scripts/sync-sandbox.sh` 실행
- test vis daemon 실행 (localhost:8742)
- S4·S5 veto 미발화 조건 (Top 5 제외율 <60%, A frontmatter draft 없음)

## 준비: X 파일 하나를 dirty 상태로 만들기

```bash
echo "# dirty edit" >> /tmp/vault-test/003-RESOURCES/bar.md
cd /tmp/vault-test && git status --porcelain 003-RESOURCES/bar.md
# 기대: M  003-RESOURCES/bar.md
```

## 실행

사용자 프롬프트:
> "`/tmp/vault-test/001-INBOX/dirty-test.md` 태그 붙이고 정리해줘.
> 내용: 'foo, baz, quux, bar 를 연결하는 노트'
> bar.md 는 현재 편집 중인 상태."

## 검증

- [ ] vis /search Top 5 에 `bar.md` 포함 (bar 관련 콘텐츠이므로)
- [ ] Step 7 per-file dirty 체크: `bar.md` 에 대해 `git status --porcelain` → 결과 있음 → `skipped_dirty`
- [ ] 나머지 X (`foo.md`, `baz.md`, `quux.md` 등) clean → `queued`
- [ ] proceed 메시지에 `(1건 dirty skip)` 포함
- [ ] state active/<job>.json `targets` 배열 확인:
  ```bash
  cat ~/.claude/state/vis-backlink/active/*.json | python3 -m json.tool
  # bar.md: status=skipped_dirty
  # 나머지: status=queued
  ```
- [ ] subagent 가 bar.md 는 수정 안 함 (dirty skip)
- [ ] bar.md 는 원본 그대로 (diff 없음)

## 복구

```bash
cd /tmp/vault-test && git checkout -- 003-RESOURCES/bar.md
```

## 수동 시뮬레이션 결과

### 2026-04-26 — Per-file dirty 체크 구현 완료 (논리 검증)

- A 자신 (dirty-test.md) 은 무조건 무시
- bar.md dirty 감지 → `skipped_dirty` 기록, queued 제외
- 나머지 X (clean) → `queued` 기록
- proceed 메시지에 `(1건 dirty skip)` 포함
- ✅ 논리 검증 통과

실제 검증은 Task 9 E2E 시나리오 에서 수행.
