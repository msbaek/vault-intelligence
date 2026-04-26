# T5 — Production 첫 실행 체크리스트

## 사전 조건

- [ ] T2 전체 통과 (01~08 시나리오)
- [ ] T3 성능 목표 달성 (09)
- [ ] CLAUDE.md backward 블록 diff 리뷰 완료 (Task 2)
- [ ] vis-backlink-status SKILL.md 리뷰 완료 (Task 3)

## Production 첫 실행

1. `.trusted` 없음 확인:
   ```bash
   test ! -f ~/.claude/state/vis-backlink/.trusted && echo "ready for first run"
   ```
2. vault clean 확인:
   ```bash
   cd ~/DocumentsLocal/msbaek_vault && git status --porcelain
   ```
3. Obsidian 문서 1건 생성 요청.
4. forward 후 dry-run 미리보기 확인.
5. diff를 섹션별로 읽고 검토.
6. 승인 → MultiEdit 적용 → `.trusted` 생성.
7. `/vis-backlink-status` 로 첫 job 확인.

> ⚠️ dry-run 반복 거부 탈출구:
> ```bash
> mkdir -p ~/.claude/state/vis-backlink
> touch ~/.claude/state/vis-backlink/.trusted
> ```
> 단, 최초 diff 검토 생략이므로 **권장하지 않음**.

## 1주 실사용 후 후속

- [ ] `~/.claude/state/vis-backlink/history/` 최근 30건 분석
  - 실패율 (failed + partial_failure / total)
  - 평균 duration
  - 자주 skip 되는 파일 패턴
- [ ] exclude_patterns 조정
- [ ] v2 후보 triage

## 구현 완료 기준

모든 Task 1~13 완료 + production 첫 실행 후 1주 실사용 결과 이상 없음.
