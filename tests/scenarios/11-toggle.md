# T2.8 토글 시나리오 (ENV_DISABLED)

## 검증 목표
- `.disabled` 마커가 있을 때 backward 가 스킵되고 forward 만 동작
- `/vis-backlink-toggle on/off` 가 마커를 정확히 생성/제거
- 토글 상태 변경이 다음 문서 생성부터 즉시 반영

## 사전 조건
- sandbox_vault clean tree
- `.trusted` 존재 (Flow 2 진입 가능 상태)
- `.disabled` 부재 (초기 ON 상태)

## 시나리오
1. `/vis-backlink-toggle off` → 마커 생성 확인
   - 기대: `~/.claude/state/vis-backlink/.disabled` 파일 생성
   - 기대: 출력 "⏸️  backward Related Notes 비활성화"
2. 새 Obsidian 문서 X 생성 (forward 트리거)
   - 기대: forward 정상 (X 에 Related Notes 추가됨)
   - 기대: backward 스킵, 인라인 안내 출력 ("ℹ️ backward Related Notes 비활성화 (재활성화: /vis-backlink-toggle on)")
   - 기대: `~/.claude/state/vis-backlink/active/` 에 신규 job 없음
3. `/vis-backlink-toggle on` → 마커 제거 확인
   - 기대: `~/.claude/state/vis-backlink/.disabled` 파일 부재
   - 기대: 출력 "✅ backward Related Notes 활성화"
4. 새 Obsidian 문서 Y 생성
   - 기대: forward + backward 모두 정상 동작
   - 기대: `active/` 에 신규 job 생성 확인 (비동기 dispatch)
5. 정리: 마커, sandbox 상태 초기화

## 통과 기준
- 단계 2: forward Related Notes 5개 추가, backward job 0개
- 단계 4: forward + backward 모두 dispatch 성공
- 모든 단계의 인라인 안내 문구가 CLAUDE.md 명세와 1:1 일치

## 검증 포인트 (CLAUDE.md 라인 매핑)
| 항목 | CLAUDE.md 라인 |
|---|---|
| 사전 가드 0번 (ENV_DISABLED) | 163 (사전 가드 블록) |
| 에러 카탈로그 행 | 244 (표 최상단) |

## 관련 파일
- `~/.claude/CLAUDE.md` — `<when-creating-obsidian-document>` 사전 가드 0번 + 에러 카탈로그
- `~/.claude/commands/vis-backlink-toggle.md` — 슬래시 커맨드 정의
- `~/.claude/skills/vis-backlink-status/SKILL.md` — ON/OFF 헤더 표시
- spec §6.C1.steps.0, §8.E1, §11.v2h
