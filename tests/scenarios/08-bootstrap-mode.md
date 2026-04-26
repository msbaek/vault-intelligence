# T2.7 — bootstrap_mode minimal ↔ full

## Case A: minimal (default)

- `no-section.md` → `## Related Notes\n\n- [[<A>]] — ...` 1 줄
- [ ] 정확히 1 줄 신설 확인

## Case B: full

1. `~/.claude/CLAUDE.md` 의 backward config 에서 `bootstrap_mode: "minimal"` → `"full"` 변경 (임시).
2. 샌드박스 새로 초기화 + `no-section.md` 복구.
3. 새 문서 생성 → `no-section.md` 의 Related Notes 가 Top 5 전체로 신설.
4. [ ] 5개 링크 삽입 확인
5. 테스트 후 config 되돌림 (`minimal`).

## 수동 검증 결과

- CLAUDE.md bootstrap_mode 설정 위치: `grep -n "bootstrap_mode" ~/.claude/CLAUDE.md`
- minimal/full 분기 처리: CLAUDE.md X 처리 서브루틴 step 5
- config 한 줄 변경으로 전환 가능: ✅ (코드 변경 0)
