# T2.1 — C3 파서 샌드박스 시나리오

## 전제

- `scripts/sync-sandbox.sh` 실행으로 `/tmp/vault-test/` 재생성
- test vis daemon 실행 (`scripts/start-test-vis.sh`)
- `~/.claude/state/vis-backlink/.trusted` **삭제** (dry-run 유도)
- `~/.claude/state/vis-backlink/active/` 비움

## 실행

사용자 프롬프트 시뮬레이션:
> "다음 내용으로 `/tmp/vault-test/001-INBOX/parser-probe.md` 를 만들어줘 —
> 본문은 'foo, bar, quux 를 연결하는 허브'. vis daemon 은 localhost:8742 사용."

훅이 forward + backward 를 순차 수행. `.trusted` 부재라 dry-run 진입.

## 검증 체크리스트

- [ ] forward: `001-INBOX/parser-probe.md` 에 `## Related Notes` 섹션이 Top 5 로 삽입됨
- [ ] backward: vis Top 5 로 `foo.md`, `bar.md`, `baz.md`, `quux.md`, `no-section.md` 중 상위 5개가 candidate
- [ ] `work-log/2026-04-14.md` 는 `exclude_patterns` 에 의해 자동 제외
- [ ] `ATTACHMENTS/dummy-image.md` 는 자동 제외
- [ ] `deviant-multiline.md` 는 파서 skip 대상으로 보고 (수정 없음)
- [ ] `deviant-image.md` 는 섹션 내부에 `![[...]]` 존재 → 파서 skip
- [ ] `no-section.md` 는 bootstrap minimal 로 `## Related Notes\n\n- [[parser-probe]] — ...` 1줄만 신설
- [ ] 정상 케이스(`foo.md`, `bar.md`, `baz.md`, `quux.md`): 기존 desc 보존, 신규 링크만 LLM desc 생성
- [ ] C6 dry-run diff 출력이 대화 내에 보임
- [ ] 사용자 거부 테스트: 거부 시 어떤 md 도 수정되지 않음
- [ ] 사용자 승인 테스트: 승인 후 `~/.claude/state/vis-backlink/.trusted` 생성됨

## 실패 시 조치

- 파서가 일탈 라인을 수정하면 → Task 2 에서 C3 파서 규칙 재작성
- bootstrap minimal 이 전체 Top 5 를 넣으면 → 훅 Backward 서브섹션 재작성

## 수동 시뮬레이션 결과 (2026-04-26)

### exclude_patterns 체크

- `work-log/2026-04-14.md`: **제외** — `work-log/*.md` 패턴에 일치, backward candidate 목록에 진입하지 않음
- `ATTACHMENTS/dummy-image.md`: **제외** — `ATTACHMENTS/**` 패턴에 일치, backward candidate 목록에 진입하지 않음

### C3 파서 적용 결과

| 파일 | 섹션 유무 | 일탈 여부 | 판정 | 상세 |
|------|---------|---------|------|------|
| `003-RESOURCES/foo.md` | 있음 | 없음 | **parse-ok** | `[[003-RESOURCES/bar]]`, `[[003-RESOURCES/baz]]` 두 링크 모두 정규식 통과. 기존 desc 보존 대상. |
| `003-RESOURCES/bar.md` | 있음 | 없음 | **parse-ok** | `[[003-RESOURCES/foo]]`, `[[003-RESOURCES/baz]]`, `[[997-BOOKS/quux]]` 세 링크 정규식 통과. 기존 desc 보존 대상. |
| `003-RESOURCES/baz.md` | 있음 | 없음 | **parse-ok** | `[[003-RESOURCES/foo]]` 한 링크 정규식 통과. 기존 desc 보존 대상. |
| `997-BOOKS/quux.md` | 없음 | — | **bootstrap** | `## Related Notes` 섹션 자체 부재. `bootstrap_mode=minimal` → A 링크 1줄만 신설. |
| `003-RESOURCES/no-section.md` | 없음 | — | **bootstrap** | `## Related Notes` 섹션 자체 부재. `bootstrap_mode=minimal` → A 링크 1줄만 신설. |
| `003-RESOURCES/deviant-multiline.md` | 있음 | 멀티라인 desc | **SKIP** | 라인 12 `  추가 설명 두 번째 줄이 들여쓰기로 이어짐` — C3 규칙 "멀티라인 desc (들여쓰기로 이어지는 줄)" 해당. 파일 전체 skip. |
| `003-RESOURCES/deviant-image.md` | 있음 | `![[...]]` 이미지 링크 | **SKIP** | 라인 12 `- ![[diagram.png]]` — C3 규칙 "`![[...]]` 이미지 링크 줄" 해당. 파일 전체 skip. |
| `work-log/2026-04-14.md` | — | — | **제외** | `exclude_patterns: work-log/*.md` 에 의해 파서 도달 전 제외. |
| `ATTACHMENTS/dummy-image.md` | — | — | **제외** | `exclude_patterns: ATTACHMENTS/**` 에 의해 파서 도달 전 제외. |

### 정규식 검증 세부 내역

C3 파서 줄 문법: `^-\s+\[\[(?P<link>[^\]]+)\]\](\s+—\s+(?P<desc>.+))?$`

**통과 예시:**
- `- [[003-RESOURCES/bar]] — bar 와 상호 연결된 샌드박스 기준 문서` → link=`003-RESOURCES/bar`, desc=`bar 와 상호 연결된 샌드박스 기준 문서`
- `- [[997-BOOKS/quux]] — 책 레퍼런스` → link=`997-BOOKS/quux`, desc=`책 레퍼런스`

**실패 예시 (SKIP 유발):**
- `  추가 설명 두 번째 줄이 들여쓰기로 이어짐` → `^-\s+` 미매칭, 멀티라인 일탈
- `- ![[diagram.png]]` → `^-\s+\[\[` 미매칭 (`![[` 형태), 이미지 링크 일탈

**확장자 있는 링크 패턴 주의:**
- `- [[foo.md]] — 설명` → link에 `.md` 포함 → C3 규칙 "확장자 있는 링크" 해당 → **SKIP**
- fixture 파일들은 `[[003-RESOURCES/bar]]` 형태 (확장자 없음) → 정상

### bootstrap 예상 결과 (quux.md, no-section.md)

`bootstrap_mode=minimal` 적용 시 삽입될 내용:
```markdown
## Related Notes

- [[001-INBOX/parser-probe]] — <A 요약 1-2문장 LLM 생성>
```

기존 섹션이 없으므로 EOF 앞에 추가.

### 체크리스트 결과

- [x] `deviant-multiline.md` → SKIP (멀티라인 desc 일탈)
- [x] `deviant-image.md` → SKIP (`![[...]]` 이미지 링크 일탈)
- [x] `work-log/2026-04-14.md` → 제외 (`work-log/*.md` 패턴)
- [x] `ATTACHMENTS/dummy-image.md` → 제외 (`ATTACHMENTS/**` 패턴)
- [x] `no-section.md` → bootstrap (섹션 없음, minimal 1줄 신설)
- [x] `997-BOOKS/quux.md` → bootstrap (섹션 없음, minimal 1줄 신설)
- [x] `foo.md`, `bar.md`, `baz.md` → parse-ok (기존 desc 보존 대상)

### 결론

**모든 C3 파서 케이스 통과.**

- exclude_patterns 분기: work-log, ATTACHMENTS 모두 정상 제외
- 일탈 감지: 멀티라인 desc, 이미지 링크 두 케이스 모두 SKIP 판정
- bootstrap: 섹션 없는 quux.md, no-section.md 모두 bootstrap 경로 진입
- parse-ok: foo.md, bar.md, baz.md 세 파일 모두 기존 desc 보존 가능 상태

Task 2 루프백 불필요. C3 파서 규칙 현행 유지.
