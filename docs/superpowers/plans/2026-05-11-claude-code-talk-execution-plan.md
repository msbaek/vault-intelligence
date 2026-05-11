# Claude Code 사내 강연 실행 Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** spec(`docs/superpowers/specs/2026-05-11-claude-code-talk-outline-design.md`)에 정의된 사내 100명 / 8시간 강연을 실제로 진행 가능한 상태로 만든다 — fallback 영상 6개 + 슬라이드 + take-home PDF + 리허설 2회 완료.

**Architecture:** D-day 역산 일정(D-30 / D-14 / D-7 / D-1 / Day / D+14) + 9개 Task. 위험 큰 항목(발주처 협의 + 리허설 + fallback 영상) 우선. 각 task는 산출물 단위로 분해되며, 산출물별 verification 기준 명시.

**Tech Stack:** Markdown + Keynote/Google Slides + macOS QuickTime/OBS (화면 녹화) + Canva/Figma(PDF 디자인) + GitHub(README) + visd HTTP API + tmux + Claude Code skills/plugins

**Spec 참조:** `docs/superpowers/specs/2026-05-11-claude-code-talk-outline-design.md`

---

## File Structure (강연 산출물)

준비 단계에서 생성/수정될 파일:

```
docs/superpowers/specs/2026-05-11-claude-code-talk-outline-design.md   (spec, 이미 존재)
.claude/plans/2026-05-08-claude-code-talk/plan.md                       (선행 outline, 이미 존재)

신규 산출물 (각 Task에서 생성):
~/git/claude-code-talk-assets/                                          ★ 새 작업 디렉토리
├── slides/
│   ├── 01-open.key                                                     (8장)
│   ├── 02-mini-lecture.key                                             (12장)
│   ├── 03-act1.key                                                     (8장)
│   ├── 04-act2-front-isms.key                                          (10장)
│   ├── 05-act2-back-tdd-plugin.key                                     (8장)
│   ├── 06-act3-vault.key                                               (10장)
│   ├── 07-act3-roadmap.key                                             (5장)
│   ├── 08-act3-cc-orchestra.key                                        (8장)
│   ├── 09-close.key                                                    (5장)
│   └── 10-qa-backup.key                                                (5장)
├── fallback-videos/
│   ├── demo-01-recall.mov                                              (~2 min)
│   ├── demo-02-skillify-isms.mov                                       (~5 min)
│   ├── demo-03-vis-search-moc.mov                                      (~4 min)
│   ├── demo-04-weekly-newsletter.mov                                   (~3 min)
│   ├── demo-05-tdd-rgb.mov                                             (~6 min)
│   └── demo-06-cc-orchestra.mov                                        (~5 min)
├── handouts/
│   ├── audience-handout.pdf                                            (1장 양면)
│   └── audience-handout.fig                                            (Figma 원본)
├── checklists/
│   ├── d-minus-1-checklist.md
│   └── day-of-checklist.md
└── README.md                                                            (자료 색인)

~/git/msbaek-claude-plugins/README.md                                    (영문판 점검)
~/git/msbaek-claude-plugins/README-ko.md                                 (한글판 분리, 선택)
```

---

## Task 1: 발주처 협의 + Open Questions 해결

**의도:** spec의 Open Questions 5개를 발주처와 협의하여 해소. 이게 안 되면 D-14 이후 작업이 막힐 수 있으므로 D-30 시점에 최우선.

**Files:**
- Create: `~/git/claude-code-talk-assets/sponsor-briefing.md`

- [ ] **Step 1: 작업 디렉토리 생성**

```bash
mkdir -p ~/git/claude-code-talk-assets/{slides,fallback-videos,handouts,checklists}
cd ~/git/claude-code-talk-assets
git init
```

- [ ] **Step 2: 발주처 협의 문서 작성**

Create `~/git/claude-code-talk-assets/sponsor-briefing.md`:

```markdown
# 발주처 협의 항목

## 강연 일정·장소
- [ ] 강연 일자: YYYY-MM-DD
- [ ] 시작/종료 시각: 09:00–18:00 (점심 12:30–13:30 / 휴식 2회 15분)
- [ ] 장소: (오프라인 회의실 / 온라인 / 하이브리드)
- [ ] 청중 수 확정: 50–100명 중 정확한 인원

## 기술 환경
- [ ] 인터넷 환경: Wi-Fi 속도 / 사외망 접근 가능 여부
- [ ] 보안 정책: GitHub 접근 가능? marketplace install 허용?
- [ ] 발표용 장비: 본인 노트북 사용 가능? 외부 모니터/HDMI/USB-C 어댑터?
- [ ] 녹화 가능 여부: 강연 녹화 + 사후 vault 보존 권한
- [ ] 마이크/스피커 환경: 100명 대상 — 무선 마이크 가능?

## 청중 정보
- [ ] 발주처 회사명 + 도메인 (Act 2 ISMS 사례 매핑 점검)
- [ ] 청중 페르소나: 도구 사용 경험치 분포 추정 (Claude Code 사용자 vs 미사용자 비율)
- [ ] 보안·컴플라이언스 환경: ISMS-P 같은 인증 필요한 회사인가?

## 발주처 요구사항 재확인
- [ ] "실습 비중 5%"가 발주처 기대치와 부합하는지 확인 — 아니면 Act 3 Phase 2에 자기 평가 워크시트 추가
- [ ] 사후 자료 제공 범위 (슬라이드 PDF? 영상?)
- [ ] 사후 follow-up 권한 (2주 후 시도 사례 수집 메일 발송 OK?)

## 약속한 결과물
- [ ] Take-home 1장 PDF: 5개 즉시 시도 + 30일 로드맵 + QR
- [ ] msbaek-claude-plugins 무료 사용 가이드
- [ ] 강연 후 설문 (QR)
```

- [ ] **Step 3: 발주처 미팅 또는 이메일 송부**

발주처 담당자에게 위 문서 송부 + 회신 일정 명시 (D-21 까지).

- [ ] **Step 4: 회신 반영**

```bash
cd ~/git/claude-code-talk-assets
# sponsor-briefing.md 에 회신 내용 반영
git add sponsor-briefing.md
git commit -m "docs: 발주처 협의 결과 반영"
```

**Verification:**
- [ ] sponsor-briefing.md의 모든 [ ] 항목이 [x]로 변경됨
- [ ] 강연 일자 확정 → D-30 카운트 시작 가능

**Failure mode 대응:**
- 발주처 응답 지연 시: 가정값으로 진행하고, 회신 도착 시 plan 재조정 (보안·녹화는 보수적으로 가정)

---

## Task 2: 워크스페이스 + visd 사전 점검

**의도:** 라이브 데모의 3개 워크스페이스(enc-mask / msbaek-tdd / vault-intelligence) + visd HTTP API가 강연 시점에 확실히 동작하도록 사전 점검. D-30 시점에 한 번, D-7에 한 번, D-1에 한 번 — 총 3회.

**Files:**
- Create: `~/git/claude-code-talk-assets/checklists/workspace-precheck.md`

- [ ] **Step 1: 점검 체크리스트 작성**

Create `~/git/claude-code-talk-assets/checklists/workspace-precheck.md`:

```markdown
# 워크스페이스 사전 점검 체크리스트

실행 시점: D-30 / D-7 / D-1 (총 3회)

## visd HTTP API
- [ ] `visd status` → running 확인
- [ ] `visd start` (미실행 시)
- [ ] `curl http://localhost:8741/health` → `{"status":"ok","indexed":true,...}` 확인
- [ ] `curl -s --get --data-urlencode "query=TDD" "http://localhost:8741/search?top_k=5"` → 결과 5건 정상
- [ ] vault 문서 수 확인 (3,000+ 예상)

## enc-mask 워크스페이스 (Act 2 ISMS)
- [ ] `~/git/kt4u/enc-mask/` 존재
- [ ] symlink 6개 정상 (thomas / ktown4u-masking / pacman / plan-docs/isms-p / capybara / mercury)
- [ ] 각 프로젝트 디렉토리에서 `claude code` 정상 진입
- [ ] vault `work-log/2026-ISMS/ISMS_Aurora_DB_감사로그_분석_지침서.md` 존재

## msbaek-tdd plugin (Act 2 후반)
- [ ] `~/git/msbaek-claude-plugins/msbaek-tdd/plugin.json` 존재
- [ ] `~/git/msbaek-claude-plugins/msbaek-tdd/skills/` 디렉토리 — 22개 skill 확인
- [ ] marketplace 등록 상태 확인 (`gh repo view msbaek/msbaek-claude-plugins`)
- [ ] `/tdd-plan` `/tdd-red` `/tdd-green` `/tdd-blue` `/tdd-tidy` 호출 가능 여부

## vault-intelligence (Act 3 메인)
- [ ] `~/git/vault-intelligence/` 존재
- [ ] `vis info` 정상 출력
- [ ] `vis search "TDD" --rerank --top-k 5` 0.3초 이내 응답
- [ ] `vis generate-moc "TDD"` 동작 확인

## cc-orchestra (Act 3 Phase 3)
- [ ] `~/dotfiles/.claude/skills/cc-orchestra/` 존재
- [ ] `ccup` 명령어 alias 존재 (`zsh function`)
- [ ] tmux 설치 확인 (`tmux -V`)
- [ ] `ccup test-task project1 ~/git/kt4u/thomas project2 ~/git/kt4u/pacman` 2 pane 정상 기동

## 매일 아침 루틴 (Act 1)
- [ ] `morning-auto.sh` 정상 실행
- [ ] `/recall yesterday` skill 등록 확인
- [ ] `/agf list` skill 등록 확인
- [ ] `daily-work-logger` skill 등록 확인

## skill 등록 확인 (전체)
- [ ] `/extract-sql-log` skill 등록
- [ ] `/skillify` skill 등록
- [ ] `/capture-research` skill 등록
- [ ] `/weekly-newsletter` skill 등록
- [ ] `/commit` skill 등록
```

- [ ] **Step 2: D-30 시점 첫 점검 실행**

```bash
cd ~/git/claude-code-talk-assets/checklists
# workspace-precheck.md 의 모든 항목 실행 + 결과 기록
```

- [ ] **Step 3: 점검 결과 commit**

```bash
git add checklists/workspace-precheck.md
git commit -m "checklist: 워크스페이스 사전 점검 1차 (D-30) 완료"
```

**Verification:**
- [ ] 모든 [ ] 항목이 [x]로 변경됨
- [ ] 실패한 항목이 있다면 그 자리에서 fix or D-14 안으로 처리할 task로 별도 기록

**Failure mode 대응:**
- visd 미실행: `visd start` 후 재확인
- skill 누락: `~/.claude/skills/`에서 해당 skill 재설치
- msbaek-tdd plugin 실패: marketplace 재배포 또는 로컬 plugin 등록

---

## Task 3: 리허설 1차 — 전체 흐름 + 시간 측정

**의도:** spec의 405분 시간 분배가 실제로 맞는지 검증. fallback 영상 제작 *전*에 리허설을 먼저 — 어느 데모가 안 되는지 알아야 영상 우선순위 결정 가능.

**Files:**
- Create: `~/git/claude-code-talk-assets/rehearsal-1-log.md`

- [ ] **Step 1: 리허설 환경 세팅**

```bash
# 빈 회의실 또는 본인 사무실 (90분 이상 확보)
# 슬라이드 없이 spec 보면서 진행 — narrative + 라이브 데모만
# 타이머: 각 블록 시작·종료 시 기록
```

- [ ] **Step 2: spec 따라 405분 풀-런 (실제 시간 측정)**

각 블록 종료 시 `rehearsal-1-log.md`에 기록:

```markdown
# 리허설 1차 시간 측정

날짜: YYYY-MM-DD
방식: 슬라이드 없이 narrative + 라이브 데모

| 블록 | spec 시간 | 실제 시간 | 차이 | 비고 |
|---|---|---|---|---|
| Open | 25m | __m | __m | |
| 미니강의 | 30m | __m | __m | |
| Act 1 | 40m | __m | __m | |
| Act 2 전반 | 100m | __m | __m | |
| Act 2 후반 | 50m | __m | __m | |
| Act 3 Phase 1 (vault) | 60m | __m | __m | |
| Act 3 Phase 2 (로드맵) | 30m | __m | __m | |
| Act 3 Phase 3 (cc-orchestra) | 30m | __m | __m | |
| Close | 40m | __m | __m | |
| Q&A 시뮬레이션 | 45m | __m | __m | |

총합: spec 450m vs 실제 ___m (차이 ___m)

## 라이브 데모 실패 지점 기록 (★ 중요)
- `/recall yesterday`: 동작 OK / 지연 X초 / 실패 원인
- `/skillify`: ...
- `vis search`: ...
- `vis generate-moc`: ...
- `/weekly-newsletter`: ...
- `/tdd-rgb`: ...
- `cc-orchestra ccup`: ...
- `/extract-sql-log`: ...

## 발견된 문제점
- (예) Act 2 전반이 100m 초과 → 20m 압축 필요
- (예) cc-orchestra pane 가독성 — 폰트 크기 조정 필요

## D-14 시점 조정 사항
- (리허설 결과 기반 spec 수정 사항)
```

- [ ] **Step 3: spec 시간 분배 조정 (필요 시)**

리허설 결과 ±15분 벗어나는 블록이 있으면 `docs/superpowers/specs/2026-05-11-claude-code-talk-outline-design.md` 의 Section 3 시간표 수정.

```bash
# spec 수정 → commit
cd ~/git/vault-intelligence
git add docs/superpowers/specs/2026-05-11-claude-code-talk-outline-design.md
git commit -m "docs(spec): 리허설 1차 결과 반영 — 시간 분배 조정"
```

- [ ] **Step 4: fallback 영상 제작 우선순위 확정**

리허설에서 실패하거나 지연된 데모는 **반드시** fallback 영상 제작. 안정적인 데모도 영상 만들되, 실패 위험 큰 것 먼저.

- [ ] **Step 5: 리허설 로그 commit**

```bash
cd ~/git/claude-code-talk-assets
git add rehearsal-1-log.md
git commit -m "log: 리허설 1차 완료 + 실패 지점 6개 식별"
```

**Verification:**
- [ ] 총 강의 시간 405m ± 15m 안에 들어옴
- [ ] 6개 핵심 데모의 라이브 동작 상태가 모두 기록됨
- [ ] fallback 영상 제작 우선순위 6개 확정

**Failure mode 대응:**
- 시간 초과 30분+: spec의 Act 2 전반 또는 Act 3 Phase 3에서 컨텐츠 압축
- 데모 3개 이상 실패: D-14 까지 환경 디버깅 task 추가

---

## Task 4: Fallback 영상 6개 제작

**의도:** spec Failure Conditions의 핵심 대응. 라이브 데모 실패 시 5초 안에 전환 가능한 recorded 영상 6개 제작.

**Files:**
- Create: `~/git/claude-code-talk-assets/fallback-videos/*.mov` (6개)

각 영상은 2-6분, 화면 녹화 + 자막 (선택). QuickTime Player 또는 OBS 사용.

- [ ] **Step 1: 영상 1 — `/recall yesterday` 데모 (Act 1)**

```bash
# 1. 터미널 + Obsidian 화면 분할 세팅
# 2. QuickTime > 새 화면 기록 시작
# 3. 시연 시나리오:
#    - `/recall yesterday` 입력 → 어제 세션 30초 복원
#    - `/agf list` 입력 → 5건 표시
#    - `morning-auto.sh` 실행 → Daily Note 자동 반영
#    - Obsidian Daily Note 한 화면 보여주기
# 4. 녹화 정지 → 파일명: demo-01-recall.mov
# 5. 길이: 2분 내외
```

저장: `~/git/claude-code-talk-assets/fallback-videos/demo-01-recall.mov`

- [ ] **Step 2: 영상 2 — `/skillify` ISMS 메타 모먼트 (Act 2 전반)**

```bash
# 시나리오:
# 1. 채팅으로 "이번 주 ISMS SQL 추출·포맷·마스킹 검출 해줘"
# 2. Claude 응답 후 `/skillify` 호출
# 3. SKILL.md 자동 추출 → extract-sql-log skill 등록
# 4. 다음 turn에서 `/extract-sql-log` 한 줄로 동작
# 5. 길이: 5분 내외
```

저장: `~/git/claude-code-talk-assets/fallback-videos/demo-02-skillify-isms.mov`

- [ ] **Step 3: 영상 3 — `vis search` + `vis generate-moc` (Act 3 Phase 1)**

```bash
# 시나리오:
# 1. `vis search "TDD" --rerank --top-k 10` → 0.3초 응답
# 2. `vis generate-moc "TDD"` → MOC 자동 생성
# 3. Obsidian에서 생성된 MOC 열어보기
# 4. Graph view 보여주기
# 5. 길이: 4분 내외
```

저장: `~/git/claude-code-talk-assets/fallback-videos/demo-03-vis-search-moc.mov`

- [ ] **Step 4: 영상 4 — `/weekly-newsletter` (Act 2 운영화)**

```bash
# 시나리오:
# 1. `/weekly-newsletter` 호출
# 2. 이번 주 작성·수정 글 자동 수집 + 뉴스레터 1편 생성
# 3. 결과 마크다운 보여주기
# 4. 길이: 3분 내외
```

저장: `~/git/claude-code-talk-assets/fallback-videos/demo-04-weekly-newsletter.mov`

- [ ] **Step 5: 영상 5 — `/tdd-rgb` 사이클 (Act 2 후반)**

```bash
# 시나리오 (Java/Spring Boot 작은 기능, 예: Calculator):
# 1. `/tdd-plan` → SRS + 테스트 목록 (1분)
# 2. `/tdd-red` → 실패 테스트 (sub-agent) (1.5분)
# 3. `/tdd-green` → 최소 구현 (sub-agent) (1.5분)
# 4. `/tdd-blue` → Composed Method refactor (sub-agent) (2분)
# 5. 각 단계 commit 보여주기
# 6. 길이: 6분 내외
```

저장: `~/git/claude-code-talk-assets/fallback-videos/demo-05-tdd-rgb.mov`

- [ ] **Step 6: 영상 6 — cc-orchestra `ccup` (Act 3 Phase 3) ★ 가장 중요**

```bash
# 시나리오:
# 1. 터미널 큰 화면 + 폰트 14pt+
# 2. `ccup isms184 thomas ~/git/kt4u/thomas pacman ~/git/kt4u/pacman` 한 줄
# 3. 6 pane (또는 3 pane) 자동 기동
# 4. 메인 pane(orchestrator)에 한국어: "pacman에서 ISMS-184 Task 1 시작"
# 5. 자동 dispatch 판단 + 확인 게이트 → 사용자 승인 → pacman pane 동작
# 6. 길이: 5분 내외
```

저장: `~/git/claude-code-talk-assets/fallback-videos/demo-06-cc-orchestra.mov`

- [ ] **Step 7: 영상 6개 commit**

```bash
cd ~/git/claude-code-talk-assets
# .gitignore에 *.mov 추가 (용량 큼) 또는 git-lfs 사용
echo "fallback-videos/*.mov" >> .gitignore
# 영상은 별도 클라우드 저장 (Google Drive / Dropbox)
# README.md 에 영상 위치 링크 기록
git add .gitignore
git commit -m "feat: fallback 영상 6개 제작 완료 (별도 클라우드 저장)"
```

**Verification:**
- [ ] 영상 6개 모두 존재 + 재생 가능
- [ ] 각 영상 화질 1080p + 폰트 가독 (회의실 50m 거리에서도 보임)
- [ ] 클라우드에 백업 (오프라인 USB도 1개 권장)

**Failure mode 대응:**
- 영상 화질 부족: OBS Studio로 재녹화 (1080p 60fps)
- 음성 없음 → 자막 권장 (간단한 한글 자막 .srt)

---

## Task 5: 슬라이드 작성 (10개 deck, 총 79장)

**의도:** spec의 블록별 설계를 시각 자료로 변환. 라이브 데모 보조 + 청중 시각 가이드.

**Files:**
- Create: `~/git/claude-code-talk-assets/slides/01-open.key` ~ `10-qa-backup.key`

도구: Keynote (또는 Google Slides). 다크 테마 + JetBrains Mono 폰트 권장.

- [ ] **Step 1: Deck 01 — Open (8장)**

슬라이드 구성:
1. 표지: "30년 + 매일 페어 — Claude Code Day in the Life" + 발표자명·소속
2. 발표자 소개: 1995년부터의 타임라인 (TDD 2002 / 페어 2005 / Claude Pro 2024-07 / Code Max 2025-07)
3. Dave Farley 인용 (1차) — 프로그래밍 본질 3요소
4. "AI 시대에도 변하지 않는 것" 메시지
5. 사내 격차 직격탄: "도구 문제가 아니라 의식 전환 문제"
6. 명시적 메시지: "AI가 짠다" ✕ → "30년 개발자가 4.7과 함께 짠다" ✓
7. 오늘의 학습 목표 (프롬프트 / 컨텍스트 / 하네스 + 5개 take-home)
8. 시간표 한 장 (블록·휴식·점심)

저장: `~/git/claude-code-talk-assets/slides/01-open.key`

- [ ] **Step 2: Deck 02 — 미니강의 3단계 프레임 (12장)**

슬라이드 구성:
1. 표지: "프롬프트 → 컨텍스트 → 하네스 30분"
2-5. 프롬프트 10m: Slow Think(+4-10%) + Prompt Contracts 4요소 + 안티패턴(바이브 코딩) + 라이브 비교
6-9. 컨텍스트 10m: CLAUDE.md 5계층 + 200줄 한도 + 핸드셰이크 + 본인 CLAUDE.md 일부
10-12. 하네스 10m: hook/skill/plugin 차이 + Claude Code 4계층 + 본인 settings.json 일부

저장: `~/git/claude-code-talk-assets/slides/02-mini-lecture.key`

- [ ] **Step 3: Deck 03 — Act 1 아침 루틴 (8장)**

슬라이드 구성:
1. 표지: "[컨텍스트] 아침 루틴 40분"
2. 메시지: "맥락 손실이 가장 큰 비용"
3-4. `/recall yesterday` + `/agf list` 데모 캡처
5-6. `morning-auto.sh` + Obsidian Daily Note 캡처
7. 활용 skill 5종 정리
8. Take-home: 가장 단순한 버전 (CLAUDE.md 1줄 + git log alias)

저장: `~/git/claude-code-talk-assets/slides/03-act1.key`

- [ ] **Step 4: Deck 04 — Act 2 전반 ISMS (10장)**

슬라이드 구성:
1. 표지: "[하네스: skill] ISMS 자동화 100분"
2. 5단계 narrative 한 장
3. 1단계 — 고통 식별 (ktown4u-masking + DB 스크럽 사례)
4. 2단계 — 1회성 자동화
5-6. 3단계 — /skillify 메타 모먼트 (★ 클라이맥스)
7. 4단계 — 운영화 (skill 5종)
8. 5단계 — Take-home
9. 활용 skill·plugin 정리
10. "여러분 회사의 반복 작업 3개 적어보기" (1분 워크시트)

저장: `~/git/claude-code-talk-assets/slides/04-act2-front-isms.key`

- [ ] **Step 5: Deck 05 — Act 2 후반 msbaek-tdd plugin (8장)**

슬라이드 구성:
1. 표지: "[하네스: plugin] 30년 경험의 패키징 50분"
2. 메시지 전환: "TDD를 가르치지 않습니다. agent에게 TDD를 시킵니다."
3-4. /tdd-rgb 사이클 흐름도 (sub-agent 분리)
5. Farley 원칙 ↔ msbaek-tdd 매핑
6. CLAUDE.md 6단계 ↔ 22 skill catalog
7. marketplace install 가이드 (QR 코드)
8. Take-home: "본인 도메인 경험을 plugin으로 만들어 동료에게 배포"

저장: `~/git/claude-code-talk-assets/slides/05-act2-back-tdd-plugin.key`

- [ ] **Step 6: Deck 06 — Act 3 Phase 1 vault 시연 (10장)**

슬라이드 구성:
1. 표지: "[컨텍스트] 지식 활용 60분"
2-3. vis search 0.3초 응답 + 검색 방법 4종
4. vis generate-moc 결과 캡처
5. Obsidian Graph view + backlink 자동화
6-7. /weekly-newsletter 결과 + AI-Practice-Master.md (306KB)
8. vault-intelligence 4개월 9 Phase BGE-M3 자작 사례
9. "Second Brain × Claude Code" 메시지
10. 활용 자료 정리

저장: `~/git/claude-code-talk-assets/slides/06-act3-vault.key`

- [ ] **Step 7: Deck 07 — Act 3 Phase 2 30일 로드맵 (5장)**

슬라이드 구성:
1. 표지: "[종합] 30일 진입 로드맵 30분"
2. "오늘 setup은 18개월 누적. 여러분은 그 위에서 시작."
3. 5단계 표 (Day 1-3 / Day 4-7 / Day 8-14 / Day 15-21 / Day 22-30)
4. Day 1 — 오늘 저녁 30분으로 시작
5. "한 달이면 80%" 메시지

저장: `~/git/claude-code-talk-assets/slides/07-act3-roadmap.key`

- [ ] **Step 8: Deck 08 — Act 3 Phase 3 cc-orchestra (8장)** ★ 클라이맥스

슬라이드 구성:
1. 표지: "[클라이맥스] AI 페어 프로그래밍의 다음 단계 30분"
2. 문제: 6개 프로젝트 동시 운영의 한계
3. 실패한 시도: symlink + Conway's Law 인용
4. 돌파: 오케스트라 메타포 + Anthropic orchestrator-workers 인용
5. `ccup` 한 줄 데모 캡처
6. 1:1 vs 1:N 표 (역할 / 산출물 / 관심사)
7. Dave Farley *Modern Software Engineering* 인용 (2차)
8. 최종 메시지: "도구의 진화가 아니라 일하는 사람의 진화"

저장: `~/git/claude-code-talk-assets/slides/08-act3-cc-orchestra.key`

- [ ] **Step 9: Deck 09 — Close (5장)**

슬라이드 구성:
1. 표지: "5개 시도 + 마무리 40분"
2. 5개 즉시 시도 거리 (체크리스트 + 시점: 오늘 저녁 / 내일 점심 / 이번 주말)
3. coffee-time 사례 (47개 회의록 + 명언 3개)
4. Farley 인용 (3차 수미상관) — Open 슬라이드 재인용
5. 최종 한 줄 메시지 (cc-orchestra-brunch.md 인용)

저장: `~/git/claude-code-talk-assets/slides/09-close.key`

- [ ] **Step 10: Deck 10 — Q&A 백업 (5장)**

슬라이드 구성:
1. 표지: "Q&A 45분"
2. 자주 묻는 질문 5개 (보안 / 주니어 / Cursor 비교 / 토큰 비용 / skill 제작 시간)
3-5. 각 질문에 대한 vault 인용 + 답변 요약

저장: `~/git/claude-code-talk-assets/slides/10-qa-backup.key`

- [ ] **Step 11: 슬라이드 PDF 일괄 export**

```bash
# Keynote 각 deck > File > Export To > PDF
# 또는 일괄 스크립트 (선택)
mkdir -p ~/git/claude-code-talk-assets/slides/pdf
# 모든 .key → .pdf export 후 폴더에 저장
```

- [ ] **Step 12: 슬라이드 commit (Keynote 파일은 git LFS 또는 클라우드)**

```bash
cd ~/git/claude-code-talk-assets
echo "slides/*.key" >> .gitignore
git add .gitignore slides/pdf/
git commit -m "feat: 슬라이드 10 deck 79장 작성 완료"
```

**Verification:**
- [ ] 10 deck 모두 존재 + 79장 ±5장
- [ ] 다크 테마 + 가독성 있는 폰트 (회의실 50m 거리)
- [ ] Farley 인용이 Deck 01·08·09 3곳에 등장
- [ ] PDF export 완료 (백업용)

**Failure mode 대응:**
- 시간 부족: Deck 02 미니강의 + Deck 08 cc-orchestra 우선 (가장 차별점)
- 디자인 부담: 기본 템플릿 + 검정 배경 + 흰 글씨 + 코드 블록만으로 충분

---

## Task 6: Take-home PDF + msbaek-claude-plugins README 영문판

**의도:** 청중이 가져갈 1장 PDF 디자인 + 외부 청중 대비 README 정비.

**Files:**
- Create: `~/git/claude-code-talk-assets/handouts/audience-handout.pdf`
- Modify: `~/git/msbaek-claude-plugins/README.md` (영문판 점검)

- [ ] **Step 1: Take-home PDF 컨텐츠 작성**

Create `~/git/claude-code-talk-assets/handouts/handout-content.md`:

```markdown
# Claude Code 30일 진입 가이드

## 오늘부터 시도할 5가지

| # | 항목 | 소요 시간 | 시점 |
|---|---|---|---|
| 1 | `~/.claude/CLAUDE.md`에 본인 역할·도메인·말투 5줄 작성 | 10분 | 오늘 저녁 |
| 2 | `/commit` skill 설치 (한글 안전 커밋) | 5분 | 내일 출근 후 |
| 3 | MCP 서버 1개 연결 (Context7 또는 GitHub) | 20분 | 이번 주말 |
| 4 | brainstorming → writing-plans → executing-plans 1회 | 60분 | 다음 주 |
| 5 | msbaek-claude-plugins install — TDD 도구 무료 | 10분 | 이번 주 안 |

## 30일 로드맵

(spec Section 4.6 Phase 2 표 그대로 1장 압축)

## 참고 자료 (QR 코드)

- [QR] msbaek-claude-plugins repo
- [QR] vault-intelligence repo
- [QR] cc-orchestra-brunch 글 (브런치)
- [QR] 발표 슬라이드 PDF (강연 후 공유)

## 강연 후 follow-up

- 2주 후 짧은 설문 메일 → 시도 사례 1건 회신해주시면 다음 강연·블로그 소재로 활용
- 질문은 (발표자 메일/슬랙) 으로 환영
```

- [ ] **Step 2: PDF 디자인 (Canva/Figma)**

```bash
# A4 1장 양면 또는 단면
# 좌측 50%: 5개 시도 표
# 우측 50%: 30일 로드맵
# 하단: QR 코드 4개 + 발표자 연락처
# 색상: spec과 통일 (다크 또는 화이트)
```

저장: `~/git/claude-code-talk-assets/handouts/audience-handout.pdf`
저장: `~/git/claude-code-talk-assets/handouts/audience-handout.fig` (원본)

- [ ] **Step 3: msbaek-claude-plugins README 영문판 점검**

```bash
cd ~/git/msbaek-claude-plugins
# README.md 영문판 점검 항목:
# - 1줄 소개 (영문)
# - install 가이드 (코드 블록)
# - 22개 skill 목록 + 1줄 설명
# - 외부 청중이 fork 후 시작할 수 있는 가이드
# - License 명시
```

- [ ] **Step 4: README 한글판 분리 (선택)**

기존 한글 README가 있으면 `README-ko.md`로 분리. `README.md`는 영문 메인.

- [ ] **Step 5: README commit + push**

```bash
cd ~/git/msbaek-claude-plugins
git add README.md README-ko.md
git commit -m "docs: 외부 청중 대비 영문판 README 정비"
git push
```

- [ ] **Step 6: handouts commit**

```bash
cd ~/git/claude-code-talk-assets
git add handouts/handout-content.md handouts/audience-handout.pdf
git commit -m "feat: take-home PDF + README 영문판 완료"
```

**Verification:**
- [ ] PDF 1장에 5개 시도 + 30일 로드맵 + QR 4개 모두 포함
- [ ] msbaek-claude-plugins README 영문판이 외부 청중에게 충분히 명확
- [ ] QR 코드 4개 모두 실제로 스캔 가능 (사전 테스트)

**Failure mode 대응:**
- 디자인 부담: 간단한 Markdown → Pandoc PDF 변환도 충분 (디자인 < 명확성)

---

## Task 7: 리허설 2차 — 슬라이드 포함 풀-런

**의도:** Task 5 슬라이드 + Task 4 fallback 영상 포함 풀-런. 시간 ±15분 안에 들어오는지 최종 검증.

**Files:**
- Create: `~/git/claude-code-talk-assets/rehearsal-2-log.md`

- [ ] **Step 1: 풀-런 환경 세팅**

```bash
# 발주처와 동일한 장비 환경 시뮬레이션 (가능한 경우)
# - 슬라이드 deck 10개 순서대로 열어두기
# - fallback 영상 6개 즉시 접근 가능 위치
# - 라이브 데모 워크스페이스 사전 준비 (Task 2 체크리스트 한 번 더)
# - 시간 측정 타이머 준비
```

- [ ] **Step 2: 슬라이드 + 라이브 데모 동시 진행 풀-런**

`rehearsal-2-log.md` 작성 + 시간 측정:

```markdown
# 리허설 2차 (슬라이드 + 영상 포함)

날짜: YYYY-MM-DD

| 블록 | 시간 | 슬라이드 전환 OK | 라이브 OK / fallback 사용 |
|---|---|---|---|
| Open (Deck 01) | __m | ✓ / ✗ | — |
| 미니강의 (Deck 02) | __m | ✓ / ✗ | Slow Think 비교 |
| Act 1 (Deck 03) | __m | ✓ / ✗ | recall / fallback |
| Act 2 전반 (Deck 04) | __m | ✓ / ✗ | skillify / fallback |
| Act 2 후반 (Deck 05) | __m | ✓ / ✗ | tdd-rgb / fallback |
| Act 3 Phase 1 (Deck 06) | __m | ✓ / ✗ | vis search / fallback |
| Act 3 Phase 2 (Deck 07) | __m | ✓ / ✗ | — |
| Act 3 Phase 3 (Deck 08) | __m | ✓ / ✗ | ccup / fallback |
| Close (Deck 09) | __m | ✓ / ✗ | — |

## 발견된 보정 필요 항목
- (예) Deck 04 슬라이드 3장 → 5장으로 늘림
- (예) Act 3 Phase 1 60m → 55m 압축

## 발주처 안내 사항 (강연 당일)
- (예) Wi-Fi 패스워드 미리 요청
- (예) HDMI/USB-C 어댑터 본인 지참 안내
```

- [ ] **Step 3: 보정 사항 슬라이드/spec에 반영**

```bash
# 슬라이드 수정
cd ~/git/claude-code-talk-assets
# 필요 시 Keynote 열어서 수정
git add slides/
git commit -m "fix: 리허설 2차 결과 슬라이드 보정"

# spec 수정 (시간 분배 등)
cd ~/git/vault-intelligence
git add docs/superpowers/specs/2026-05-11-claude-code-talk-outline-design.md
git commit -m "docs(spec): 리허설 2차 시간 분배 최종 확정"
```

- [ ] **Step 4: 리허설 로그 commit**

```bash
cd ~/git/claude-code-talk-assets
git add rehearsal-2-log.md
git commit -m "log: 리허설 2차 완료 + 최종 보정"
```

**Verification:**
- [ ] 총 405m ±15m 안에 들어옴
- [ ] 슬라이드 전환 + 라이브 데모 동시 진행 자연스러움
- [ ] fallback 영상 5초 안에 전환 가능 (실제 측정)

**Failure mode 대응:**
- 시간 또 초과: Deck 06 Act 3 Phase 1 압축 (vis 데모 종류 줄임)
- 라이브 + 슬라이드 동시 진행 부담: 핵심 데모 화면에 미리 라이브 시연 픽 박힌 상태로 시작

---

## Task 8: D-1 최종 점검 + 당일 운영

**의도:** 강연 전날 최종 점검 + 당일 무사 진행.

**Files:**
- Create: `~/git/claude-code-talk-assets/checklists/d-minus-1-checklist.md`
- Create: `~/git/claude-code-talk-assets/checklists/day-of-checklist.md`

- [ ] **Step 1: D-1 체크리스트 작성**

Create `~/git/claude-code-talk-assets/checklists/d-minus-1-checklist.md`:

```markdown
# D-1 (강연 전날) 체크리스트

## 기술 환경
- [ ] Task 2 workspace-precheck.md 전체 재실행
- [ ] visd 데몬 동작 확인 (`visd status`)
- [ ] 노트북 배터리 100% + 충전 어댑터 챙김
- [ ] HDMI/USB-C 어댑터 챙김
- [ ] 외부 마우스/키보드 (선택)

## 발표 자료
- [ ] 슬라이드 10 deck 노트북 + 클라우드 백업 + USB 백업
- [ ] fallback 영상 6개 노트북 + 클라우드 + USB
- [ ] take-home PDF 100부 + 디지털 (QR로 배포 가능)
- [ ] sponsor-briefing.md 회신 항목 최종 확인

## 콘텐츠 리허설
- [ ] Open 25m 한 번 더 (거울 또는 셀프 녹화)
- [ ] Farley 인용 3개 위치 (Open / Act 3 / Close) 외움
- [ ] cc-orchestra `ccup` 한 줄 외움
- [ ] 5개 take-home 항목 외움

## 발주처 측 환경
- [ ] 도착 시간 + 장소 + 담당자 연락처 최종 확인
- [ ] 인터넷 환경 사전 점검 약속
- [ ] 마이크/스피커 테스트 30분 일찍 도착해서 진행

## 멘탈/체력
- [ ] 일찍 잠 (강연 직전 새벽 작업 금지)
- [ ] 아침 식사 가볍게
- [ ] 강연 1시간 전 도착 (장비 세팅 시간 확보)
```

- [ ] **Step 2: Day-of 체크리스트 작성**

Create `~/git/claude-code-talk-assets/checklists/day-of-checklist.md`:

```markdown
# 강연 당일 운영 체크리스트

## 도착 직후 (강연 1시간 전)
- [ ] 노트북 + HDMI 연결 + 화면 미러링 확인
- [ ] 슬라이드 화면 출력 OK (회의실 뒤에서 가독성 확인)
- [ ] 마이크 음량 + 노이즈 점검
- [ ] 인터넷 연결 확인 (visd HTTP API + GitHub access)
- [ ] visd 데몬 시작 (`visd start && visd status`)
- [ ] 라이브 데모 3개만 빠른 사전 동작 (recall / vis search / ccup)

## 강연 중
- [ ] 휴대폰 무음 + 노트북 알림 OFF
- [ ] 각 블록 시작 시 타이머 시작
- [ ] 라이브 데모 30초 안에 응답 없으면 즉시 fallback 영상
- [ ] Q&A 진행 시 사전 준비 5개 질문 활용
- [ ] 청중 반응 보면서 Q&A 5분 +/- 조정

## 강연 직후
- [ ] 설문 QR 코드 공지 + 청중이 그 자리에서 응답하도록 유도
- [ ] 발주처 담당자에게 인사 + 사후 자료 제공 약속 재확인
- [ ] 슬라이드 PDF + take-home PDF 발주처에 전송 (메일/슬랙)

## 귀가 후 (당일 저녁)
- [ ] 강연 자료 클라우드 백업 최종 확인
- [ ] D+14 follow-up 일정 캘린더 등록
- [ ] 본인 vault에 강연 후기 작성 (cc-logs 또는 daily note)
```

- [ ] **Step 3: 체크리스트 commit**

```bash
cd ~/git/claude-code-talk-assets
git add checklists/d-minus-1-checklist.md checklists/day-of-checklist.md
git commit -m "checklist: D-1 + 당일 운영 체크리스트 완료"
```

- [ ] **Step 4: D-1 체크리스트 실행**

체크리스트 모든 항목 [ ] → [x]

- [ ] **Step 5: 강연 당일 운영**

day-of-checklist.md 따라 진행. 강연 본편은 spec + 슬라이드대로.

**Verification:**
- [ ] D-1 체크리스트 모든 항목 완료
- [ ] 당일 405m ± 15m 안에 강연 종료
- [ ] 청중 설문 응답률 50%+ + 시도 의향 60%+ (spec Section 5.2 검증 항목)

**Failure mode 대응:**
- 장비 실패: 사전 점검 30분 일찍 도착 + 백업 USB 사용
- 시간 초과: Q&A를 30m로 단축 + 미답 질문은 메일/슬랙 follow-up

---

## Task 9: D+14 Follow-up + 강연 회고

**의도:** 청중 시도 사례 수집 + 본인 회고 + 다음 강연 소재 축적.

**Files:**
- Create: `~/DocumentsLocal/msbaek_vault/work-log/2026-talks/<강연일자>-claude-code-talk-retrospective.md`

- [ ] **Step 1: 청중 follow-up 메일 송부**

```bash
# 강연 후 2주 시점 메일/슬랙
# - 짧은 설문 (5분 이내)
# - 시도 사례 1건 회신 요청
# - 다음 강연·블로그 소재 활용 동의 받기
```

설문 내용:
1. 강연에서 가장 인상 깊었던 데모/메시지는?
2. 강연 후 시도한 항목 (CLAUDE.md / skill / hook / 다른 것)
3. 시도 후 결과 (성공 / 부분 성공 / 실패 — 자유 기술)
4. 다음 강연에서 다뤄줬으면 하는 주제
5. 발표자에게 한 마디 (선택)

- [ ] **Step 2: 청중 회신 수집 + 분석**

회신 사례 3건 이상 수집 (spec Section 5.2 검증 항목).

- [ ] **Step 3: 본인 회고 작성**

vault에 회고 노트 작성:

Create `~/DocumentsLocal/msbaek_vault/work-log/2026-talks/<강연일자>-claude-code-talk-retrospective.md`:

```markdown
---
date: YYYY-MM-DD
type: retrospective
tags: [talk, claude-code, retrospective]
---

# Claude Code 사내 강연 회고

## 강연 정보
- 일자: YYYY-MM-DD
- 발주처: ___
- 청중: ___명
- 형태: 8시간 / 온라인 or 오프라인

## 잘 된 것 (Keep)
- (예) cc-orchestra 30분 클라이맥스 — 청중 5명 즉시 질문
- (예) Farley 3회 인용 수미상관 — 메시지 일관성

## 안 됐던 것 (Problem)
- (예) Act 2 전반 100m 중 110m 소비 — 압축 필요
- (예) /skillify 라이브 1회 실패 — fallback 영상 전환

## 다음에 바꿀 것 (Try)
- (예) Slow Think 라이브 비교를 2회로 늘림
- (예) cc-orchestra 슬라이드 7장 → 5장으로 압축

## 청중 시도 사례 (수집)
- (사례 1) ___
- (사례 2) ___
- (사례 3) ___

## 메시지가 잘 닿았는가
- "AI가 짠다" → "30년 개발자가 4.7과 함께 짠다" — 청중 반응?
- "도구 진화가 아니라 일하는 사람의 진화" — 청중 반응?
- envy → 30일 로드맵 좌절 방지 → 청중 반응?

## 다음 강연 소재 후보
- (예) "주니어 개발자를 위한 Claude Code 1년 가이드"
- (예) "TDD agent 만들기 워크숍 — 2시간 실습"
```

- [ ] **Step 4: 회고 commit + share**

```bash
# vault commit (vault에 git이 있는 경우)
cd ~/DocumentsLocal/msbaek_vault
git add work-log/2026-talks/
git commit -m "retro: 사내 Claude Code 강연 회고"

# 또는 강연 자료 디렉토리에도 백업
cp ~/DocumentsLocal/msbaek_vault/work-log/2026-talks/*.md ~/git/claude-code-talk-assets/
cd ~/git/claude-code-talk-assets
git add *.md
git commit -m "retro: 강연 회고 백업"
```

**Verification:**
- [ ] 청중 회신 3건 이상 수집
- [ ] 회고 노트 vault에 저장됨
- [ ] 다음 강연 소재 후보 2개 이상 발굴

**Failure mode 대응:**
- 회신 부족: 발주처 담당자 통해 사내 채널 재공지
- 회고 작성 부담: 위 4가지 섹션만이라도 10줄씩 작성

---

## 의존성 그래프

```
Task 1 (발주처 협의) ──> Task 2 (워크스페이스 점검)
                     └─> Task 5 (슬라이드 작성)
                     └─> Task 6 (take-home PDF)

Task 2 ──> Task 3 (리허설 1차) ──> Task 4 (fallback 영상 제작)
                                └─> Task 5 시간 보정

Task 4 + Task 5 + Task 6 ──> Task 7 (리허설 2차)

Task 7 ──> Task 8 (D-1 점검 + 당일 운영)

Task 8 ──> Task 9 (D+14 follow-up + 회고)
```

## D-day 역산 일정 (예시)

| 시점 | 실행 Task |
|---|---|
| D-30 | Task 1 (발주처 협의 송부) + Task 2 (점검 1차) |
| D-21 | Task 1 회신 반영 |
| D-21 ~ D-14 | Task 3 (리허설 1차) |
| D-14 ~ D-7 | Task 4 (fallback 영상) + Task 5 (슬라이드) + Task 6 (handout) 병렬 |
| D-7 | Task 2 (점검 2차) + Task 7 (리허설 2차) |
| D-3 ~ D-1 | 슬라이드 미세 보정 |
| D-1 | Task 8 (체크리스트 실행) |
| Day 0 | 강연 |
| D+14 | Task 9 (follow-up + 회고) |

## 시간 배분 (총 작업 시간 추정)

| Task | 추정 시간 |
|---|---|
| Task 1 | 2-4 시간 (발주처 응답 대기 제외) |
| Task 2 | 1-2 시간 (3회 반복) |
| Task 3 | 6-8 시간 (리허설 풀-런 + 로그) |
| Task 4 | 12-18 시간 (영상 6개 × 2-3 시간) |
| Task 5 | 20-30 시간 (슬라이드 10 deck) |
| Task 6 | 4-6 시간 (PDF + README) |
| Task 7 | 6-8 시간 (리허설 2차) |
| Task 8 | 2 시간 (D-1) + 8 시간 (당일) |
| Task 9 | 4-6 시간 (follow-up + 회고) |

**총 작업 시간: 약 65-90 시간** (D-30 ~ D+14 약 6주에 분산)

## 위험 평가

| 위험 | 영향 | 대응 |
|---|---|---|
| 발주처 응답 지연 | 일정 전반 지연 | D-30 보다 빨리 시작 + 가정값으로 진행 |
| 라이브 데모 실패 | 강연 중 신뢰도 손상 | fallback 영상 6개 필수 |
| 슬라이드 작성 시간 부족 | D-7 압박 | Deck 02 + 08 우선 + 다른 deck은 미니멀 디자인 |
| cc-orchestra 라이브 실패 | 클라이맥스 임팩트 손상 | 영상 가장 잘 만들고 + 사전 워밍업 필수 |
| 인터넷 환경 미흡 | visd / GitHub access 불가 | 로컬 동작 강조 + 오프라인 vault 시연 백업 |
| 보안 정책으로 marketplace install 불가 | take-home 5번 항목 사용 불가 | QR + 점심 후 자가 진행으로 회피 |

---

## Self-Review

**Spec coverage:** spec Section 8.1 (사전 준비) + 8.2 (라이브 회복) + 8.3 (사후 측정) 모든 항목이 Task 1-9에 매핑됨. spec Section 9 (Open Questions 5개)는 Task 1에서 해소.

**Placeholder scan:** "TBD" 없음. 모든 step에 구체적 명령어/내용 명시. 발주처 회사명·일자 등 spec의 의도적 TBD는 Task 1에서 채워지므로 plan 자체엔 placeholder 없음.

**Type/이름 일관성:** spec에서 사용한 워크스페이스 경로(`~/git/kt4u/enc-mask/`, `~/git/msbaek-claude-plugins/msbaek-tdd`, `~/git/vault-intelligence`)와 plan에서 사용한 경로 일치. spec의 데모 6개(`/recall`, `/skillify`, `vis search`, `/weekly-newsletter`, `/tdd-rgb`, `/extract-sql-log`)와 fallback 영상 6개 매핑 일치. 단, plan에서 `cc-orchestra`도 영상 6개에 포함됨 — spec Section 8.1과 비교 시 `/extract-sql-log` 대신 `cc-orchestra`로 교체된 사항이므로 spec Section 8.1을 보정할 필요 있음 (이건 Task 3 리허설 결과 반영 단계에서 처리).

---

## Decision Log

- **2026-05-11**: spec 기반 D-30 ~ D+14 9-task 실행 plan 작성. 위험 큰 항목(발주처 협의 + fallback 영상 + cc-orchestra 클라이맥스) 우선. 총 작업 시간 65-90 시간 추정.
