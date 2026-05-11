# Claude Code 사내 강연 Outline (8시간) — Design Spec

**Status:** design approved, ready for writing-plans
**Created:** 2026-05-11
**Owner:** msbaek
**Related:** `.claude/plans/2026-05-08-claude-code-talk/plan.md` (선행 외부-청중 outline)

---

## 1. Context

### Goal

외부 발주처(중견 IT 기업)의 사내 개발자 50–100명(중급~고급)을 대상으로 한 **반-1일(8시간) 단발 집체 강연**의 콘텐츠 outline을 확정한다. 강연 종료 시점에 청중이 본인 PC에서 즉시 시도할 5가지 항목과 30일 진입 로드맵을 가지고 돌아가게 만든다.

**Why:** 발주처는 AI 코딩 어시스턴트(Claude Code) 도입 2개월 차로, 적극 활용자와 미사용자의 격차가 벌어지는 시점. 발주처가 명시한 목적은 *"의식 전환과 활용 레벨업의 계기"* 이며 단순 기능 소개 수준은 명시적으로 배제됨. 발주처 요구 프레임은 **"프롬프트 → 컨텍스트 → 하네스 엔지니어링"** 3단계.

**연사의 차별점 4가지** (발주처 신뢰성 자산):
1. 30년 경력 + ktown4u CTO
2. 매일 AI 페어 프로그래밍 — Pro부터 Code Max까지 도구 진화 경험
3. 자작 skill 30+ / msbaek-tdd plugin v1.6.1 marketplace publish
4. TDD/Refactoring 평생 추구 → "AI가 짜는 코드"가 아닌 **"30년 개발자가 4.7과 함께 짜는 코드"**

### Acceptance Criteria

다음이 모두 충족되면 outline 완성:

- [ ] 8시간(점심·휴식 75분 제외하면 실강 405분) 시간표가 ±15분 오차 내로 합산
- [ ] 발주처 요구 3단계(프롬프트 / 컨텍스트 / 하네스) 각각 명시적 슬롯 보유
- [ ] 연사 차별점 4가지 자산이 모두 강연 중 등장
- [ ] Dave Farley 인용 3회 등장: Open(3요소) + Act 3 Phase 3(Modern Software Engineering) + Close(3요소 수미상관)
- [ ] msbaek-tdd plugin 라이브 시연 슬롯 포함 (TDD를 *가르치는* 게 아니라 *agent 사례*로)
- [ ] vault `나의 AI 활용 사례.md`의 16개 사례 중 12개 이상이 강연 어딘가에 등장
- [ ] 청중 take-home: "5개 즉시 시도 거리" + "30일 로드맵" 명시
- [ ] 라이브 데모 6개 모두 recorded fallback 준비 가능한 구조
- [ ] Q&A 45분 이상 확보

---

## 2. Constraints (Non-negotiable)

| 제약 | 내용 |
|---|---|
| **시간** | 9:00–18:00 (실강 405분 + 점심 60분 + 휴식 2×15분) |
| **TDD 별도 세션 제외** | Part II 분리 안 함. TDD는 *agent 제작 사례*로만 등장 (Act 2 후반) |
| **청중 규모** | 50–100명, 중~고급. 페어 워크숍은 운영적 어려움으로 미채택 (실습 비중 5%) |
| **포맷** | 라이브 데모 + 강의 + Q&A. 페어 실습 없음 |
| **언어** | 한국어. 기술 용어 영어 first. 발표자료 한글 |
| **라이브 실패 대비** | 핵심 데모 6개 recorded fallback 필수 |
| **사내 격차 대응** | "envy-driven adoption"을 유지하되 좌절 방지 메시지 동봉 |

---

## 3. Final Structure — 8시간 시간표

```
09:00 – 09:25  [Open] 25m
09:25 – 09:55  [미니강의] 3단계 프레임 30m
09:55 – 10:35  [Act 1] 아침 루틴 40m
10:35 – 10:50  ☕ 휴식 15m
10:50 – 12:30  [Act 2 전반] ISMS 자동화 100m
12:30 – 13:30  🍱 점심 60m
13:30 – 14:20  [Act 2 후반] msbaek-tdd plugin 사례 50m
14:20 – 16:20  [Act 3] 지식 활용 + cc-orchestra + 30일 로드맵 120m
16:20 – 16:35  ☕ 휴식 15m
16:35 – 17:15  [Close] 5개 시도 + Farley 수미상관 40m
17:15 – 18:00  [Q&A] 45m
─────────────────────────────────────
실강 405m + 휴식 75m = 480m (8h)
```

| 블록 | 시간 | 3단계 라벨 | 핵심 메시지 |
|---|---|---|---|
| Open | 25m | — | 30년 경력 + 매일 페어 + Farley + 사내 격차 |
| 미니강의 | 30m | **3단계 전체** | 프롬프트→컨텍스트→하네스 개념 |
| Act 1 | 40m | **컨텍스트** | "어제 컨텍스트 30초 복원" |
| Act 2 전반 | 100m | **하네스 (skill)** | ISMS 5단계 + /skillify 메타 |
| Act 2 후반 | 50m | **하네스 (plugin)** | 30년 경험 → msbaek-tdd marketplace |
| Act 3 | 120m | **컨텍스트 + 종합** | vault 시연 + 30일 로드맵 |
| Close | 40m | — | 5개 시도 + Farley 수미상관 |
| Q&A | 45m | — | 자주 나올 5개 질문 사전 준비 |

---

## 4. 블록별 세부 설계

### 4.1 Open (25m)

**Output Format:** 25분 narrative + 슬라이드 8장 + 청중 호흡 측정 1회

**스토리 흐름:**
1. (5m) "1995년부터 코드를 짰습니다. TDD 만난 게 2002년, 페어 프로그래밍 만난 게 2005년. 평생 더 좋은 페어를 찾아왔습니다."
2. (5m) "매일 같이 일합니다. 처음엔 Claude Pro로, 지금은 Code Max로. 좌절한 시기도 있었습니다." — 외부 참고 자료: vault `After 180 Days of Daily AI Pair Programming.md` (영문, 다른 개발자 경험)
3. (5m) **Dave Farley 인용 (1차)**: 프로그래밍 본질 3요소 — "AI 시대에도 변하지 않습니다."
   > "어려운 부분은 코드 작성이 아니라, 컴퓨터가 수행할 수 있을 만큼 충분히 상세하고 정확한 *설명*을 제시하는 것이다."
4. (5m) **사내 격차 직격탄**: "여러분 회사는 2개월 전 Claude Code 도입. 적극 활용자 vs 미사용자 격차가 벌어지고 있을 겁니다. 이건 도구 문제가 아니라 **의식 전환** 문제입니다."
5. (5m) **명시적 메시지**: "AI가 짭니다. ← 틀린 명제. 30년 개발자가 4.7과 함께 짭니다. ← 정답."

**인용 자료:**
- vault `003-RESOURCES/AI/AI-DEVELOPER-GROWTH/After 180 Days of Daily AI Pair Programming.md`
- vault `003-RESOURCES/TDD/Acceptance Testing Is the FUTURE of Programming - Dave-Farely.md`
- vault `나의 AI 활용 사례.md` "커피타임의 변화" 47개 회의록 언급

**Failure Conditions:**
- 청중이 "또 자랑하는 강연이구나" 첫 5분에 판단하면 실패 → 좌절 경험(30일) 명시적 공개로 방어
- 사내 격차 메시지가 비난조로 들리면 실패 → "도구 문제 아니라 의식 문제" 톤으로

### 4.2 미니강의 — 3단계 프레임 (30m)

**Output Format:** 슬라이드 12장 + 라이브 시연 1회 (Slow Think 비교)

| 단계 | 시간 | 내용 | 라이브 |
|---|---|---|---|
| **프롬프트** | 10m | Slow Think(+4–10%) + Prompt Contracts(4요소) + 안티패턴 (바이브 코딩) | 같은 질문 일반 vs Slow Think 비교 |
| **컨텍스트** | 10m | CLAUDE.md 5계층 + 200줄 한도 + 핸드셰이크 | 본인 CLAUDE.md 일부 공개 |
| **하네스** | 10m | hook / skill / plugin 차이 + Claude Code 하네스 = 4계층 (hooks/skills/plugins/settings) | 본인 settings.json 일부 |

**핵심 메시지:** "프롬프트는 1%, 나머지 99%가 컨텍스트와 하네스. 오늘 그 99%를 보여드립니다."

**인용 자료:**
- vault `Prompt-Contracts-From-Vibe-Coding-to-Shipping-with-Claude-Code.md` (롤백 33%→10%)
- vault `Slow Think의 놀라운 효과.md` (정확도 +4–10%)
- vault `Context Engineering: AI 코딩의 새로운 패러다임.md`
- vault `AI 활용 기법 완전 가이드 - Prompt / Context / Harness Engineering.md`
- vault `Claude XML 프롬프팅 고급 기법.md` (예비)

**Failure Conditions:**
- 30분에 3단계 다 다루려고 깊이 잃으면 실패 → 각 단계 1개 핵심 패턴만
- "이거 우리도 알아요" 반응 나오면 실패 → Slow Think 라이브 시연으로 임팩트 회복

### 4.3 Act 1 — 아침 루틴 (40m) [컨텍스트]

**Output Format:** 30분 라이브 데모 + 10분 take-home

**라이브 시퀀스:**
1. `/recall yesterday` — 어제 세션·파일·결정 30초 복원
2. `/agf list` — Claude Code 세션 인덱스에서 어제 작업 5건
3. `morning-auto.sh` — daily-work-logger + claude-code-release-tracker 자동 실행
4. Obsidian Daily Note 공개 — 오늘 컨텍스트가 한 화면에
5. 첫 메시지 시작 (cold start 비교)

**자작 자산 등장:**
- `recall` skill
- `agf` skill / find-session
- `daily-work-logger` skill
- `claude-code-release-tracker` skill
- `session-handoff` skill
- (vault `나의 AI 활용 사례.md` "매일 아침의 루틴" 섹션 인용)

**핵심 메시지:** "맥락 손실이 가장 큰 비용. 매일 자동으로 복원합니다."

**Take-home (10m):**
- 가장 단순한 버전: `~/.claude/CLAUDE.md`에 어제 작업 1줄 + `git log --since=yesterday` alias

**Failure Conditions:**
- 5개 skill을 빠르게 휘두르다 청중이 따라오지 못하면 실패 → 첫 1개는 일부러 천천히

### 4.4 Act 2 전반 — ISMS 자동화 (100m) [하네스: skill]

**Output Format:** 80m narrative + 20m 메타 모먼트

**5단계 (각 20m):**

1. **고통 식별 (15m)** — ktown4u ISMS 컴플라이언스 사례
   - `~/git/kt4u/enc-mask/` 워크스페이스 (thomas / ktown4u-masking / pacman / plan-docs/isms-p)
   - vault `work-log/2026-ISMS/ISMS_Aurora_DB_감사로그_분석_지침서.md` 입증
   - **자작 사례**: vault `나의 AI 활용 사례.md`의 **ktown4u-masking** (Spring Profile + Jackson MaskingModule + CodeArtifact 배포) + **DB 스크럽 자동화** (21테이블, 91% 감축)

2. **1회성 자동화 (20m)** — "이번 주 SQL 모음 들고 와서 그냥 채팅"
   - extract → 포맷 → 마스킹 룰 위반 검출까지
   - **대본대로 안 될 때 대응**도 보여줌 — 라이브의 진정성

3. **/skillify 메타 모먼트 (25m)** ★ 클라이맥스
   - 방금 한 대화에서 SKILL.md 자동 추출
   - `extract-sql-log` skill로 등록
   - **재귀**: Claude Code로 Claude Code skill 만들기

4. **운영화 (20m)**
   - 다음 날 `/extract-sql-log` 한 줄로 끝
   - `capture-research`로 vault 저장
   - 일주일 뒤 `/weekly-newsletter`가 자동 정리
   - **자작 사례**: vault "Claude Code Skills/Commands 개발" 섹션 (daily-work-logger, weekly-newsletter, batch-summarize-urls 등 5종)

5. **Take-home (10m)**
   - "skill 만드는 게 어렵지 않다 — Claude Code가 만들어 준다"
   - 청중에게 본인 회사의 *반복되는 검증·정리·보고* 3개 즉시 적게 (1분)
   - `msbaek-claude-plugins` repo 공개 → "fork 해서 시작"

**자작 자산 등장:** `extract-sql-log`, `skillify`, `capture-research`, `weekly-newsletter`, `commit`, `humanize-korean` (보너스), ktown4u-masking 라이브러리, DB 스크럽 스크립트

**Failure Conditions:**
- /skillify가 라이브에서 실패하면 → recorded fallback 즉시 전환
- ISMS가 청중 도메인과 동떨어지면 → "여러분 회사의 컴플라이언스/감사/리포팅에 그대로 적용"으로 일반화

### 4.5 Act 2 후반 — msbaek-tdd plugin 사례 (50m) [하네스: plugin]

**Output Format:** 30m narrative + 라이브 + 20m marketplace install 가이드

**Narrative:** "skill 하나가 발전하면 plugin이 됩니다. 30년 TDD 경험을 plugin으로 패키징한 사례를 보여드립니다."

**시연 흐름:**
1. (10m) **왜 plugin인가** — skill 22개를 묶어 marketplace 배포
   - `/Users/msbaek/git/msbaek-claude-plugins/msbaek-tdd` v1.6.1
   - vault `나의 AI 활용 사례.md` "TDD-AGENT" 섹션
   - vault `TDD and Generative AI – A Perfect Pairing.md` 인용
   - **메시지 전환**: "TDD를 가르치지 않습니다. agent에게 TDD를 시킵니다."

2. (15m) **/tdd-rgb 라이브** — 작은 Java/Spring Boot 기능
   - `/tdd-plan` → SRS · 테스트 목록
   - `/tdd-red` → 실패 테스트 (sub-agent)
   - `/tdd-green` → 최소 구현 (sub-agent)
   - `/tdd-blue` → Composed Method 리팩토링 (sub-agent)
   - **각 단계가 별도 sub-agent → main context 오염 없음**이 차별점

3. (10m) **Farley 원칙이 어떻게 코드화됐는가**
   - Farley 3요소 ↔ /tdd-plan / /tdd-rgb / 인수 테스트
   - 사용자 CLAUDE.md 6단계 ↔ msbaek-tdd 22 skill catalog
   - "원칙은 변하지 않습니다. 구현 메커니즘이 발전합니다."

4. (15m) **marketplace install 가이드 + 청중 take-home**
   - QR 코드: GitHub repo URL
   - 라이브 설치 시도 1대 (1-2명 자원 청중)
   - 100명 동시 설치는 점심 후 자가 진행 (보안·네트워크 정책 변수 회피)
   - **메시지**: "여러분도 본인 도메인 경험을 plugin으로 만들어 동료에게 배포하세요."

**자작 자산 등장:** msbaek-tdd plugin v1.6.1 (22 skill: tdd / tdd-plan / tdd-red / tdd-green / tdd-blue / tdd-tidy / tdd-rgb / decompose-conditional / extract-method-object / replace-conditional-with-poly 등)

**Failure Conditions:**
- 라이브 install 실패하면 → QR로 우회, 점심 후 자가 진행
- TDD 자체를 모르는 청중이 다수면 → "Farley 3요소 + agent" 비유로 추상화

### 4.6 Act 3 — 지식 활용 + 30일 로드맵 (120m) [컨텍스트 종합]

**Output Format:** Phase 1 (60m 라이브 시연) + Phase 2 (30m 로드맵) + Phase 3 (30m 자작 자산 시연)

#### Phase 1: vault 시연 (60m)

- (10m) `vis search "TDD"` — vault 3,354 문서를 0.3초 의미 검색
- (10m) `/recall TDD 리팩토링` — 의미 기반 회상
- (10m) `vis generate-moc "TDD"` — MOC 자동 생성 라이브
- (10m) Obsidian Graph view + backlink 자동화 (`vis-backlink-trigger`)
- (10m) `/weekly-newsletter` — 이번 주 글 자동 뉴스레터
- (10m) **자작 사례**: `vault-intelligence` 4개월 9 Phase BGE-M3 (검색 <1초, 캐시 99%+, 7,000+ 문서)
  - vault `나의 AI 활용 사례.md` "vault-intelligence" 섹션

#### Phase 2: 30일 진입 로드맵 (30m)

| 일차 | 단계 | 도구 | 결과 |
|---|---|---|---|
| Day 1–3 | CLAUDE.md 1개 + memory ON | Claude Code 기본 | 컨텍스트 한 번 작성 → 평생 활용 |
| Day 4–7 | 첫 skill 1개 (`/commit` 같은 사소한 것) | skillify | "skill이 무엇인지" 체득 |
| Day 8–14 | hook 1개 (커밋 시 자동 리뷰 등) | hook-development | "자동화" 첫 맛 |
| Day 15–21 | Obsidian 설치 + Daily Note | Obsidian (vis 없이) | vault 가치 체감 |
| Day 22–30 | vis-intelligence + MCP 서버 1개 | vis + MCP | full setup 80% |

**메시지:** "오늘 setup은 18개월 누적입니다. 여러분은 그 위에서 시작 — 한 달이면 80%."

#### Phase 3: cc-orchestra 클라이맥스 — "AI 페어의 다음 단계" (30m)

**의도:** Act 3의 클라이맥스. 단순 사례 나열이 아니라 "AI 페어 프로그래밍의 다음 단계" narrative를 통째로 전달. 발표자의 가장 최근(2026-05) 발견 + 사상적 깊이.

**5단계 narrative** (vault `cc-orchestra-brunch.md` 기반):

1. **(5m) 문제: 단일 페어의 천장**
   - ISMS-P 작업 시 6개 프로젝트(thomas / ktown4u-masking / pacman / plan-docs/isms-p / enc-mask / capybara) 동시 운영
   - "AI를 많이 시키는 게 아니라, 내가 많이 움직이는 것이었다" — 사람이 병목

2. **(5m) 실패한 시도: symlink는 통신을 만들지 않는다**
   - enc-mask aggregator + symlink 6개 → Claude Code가 하위 CLAUDE.md를 로딩하지 않음
   - **Conway's Law 인용**: "조직이 시스템을 설계하면, 그 구조는 그 조직의 의사소통 구조를 닮는다"
   - 깨달음: "파일 경로를 연결했을 뿐, 의사소통 경로를 만들지 않았다"

3. **(10m) 돌파: 오케스트라 메타포 + 라이브 시연**
   - 지휘자 + 연주자 메타포
   - **Anthropic *Building effective agents* 인용**: orchestrator-workers 패턴
   - 라이브: `ccup isms184 thomas ~/git/kt4u/thomas pacman ~/git/kt4u/pacman ...` 한 줄로 6 pane 환경 구성
   - 메인 pane orchestrator에게 한국어: "pacman에서 ISMS-184 Task 1 시작해줘"
   - 자동 dispatch 판단 + **확인 게이트** (1:N의 통제권 보존)
   - 자작 skill: `/Users/msbaek/dotfiles/.claude/skills/cc-orchestra`

4. **(5m) 사상: 도구가 아니라 일하는 방식이 바뀐다**
   - 표 (vault 원문 인용):
     | | 1:1 페어 | 1:N 오케스트레이션 |
     |---|---|---|
     | 역할 | 동료 프로그래머 | 팀 리더 + 실행 팀 |
     | 산출물 | 코드 라인 | 의도 + 위임 + 검증 |
     | 관심사 | 지금 이 함수 | 프로젝트 간 일관성 |
   - **Dave Farley 인용 (2차 — 본문 첫 등장)**: *Modern Software Engineering* — "Software engineering is the application of an empirical, scientific approach..."
   - 핵심 메시지: "도구의 진화가 아니라 일하는 사람의 진화"
   - **CTO 관점 연결**: "이건 CTO 역할과 닮아있다" (연사의 직책 자산 활용)

5. **(5m) 보너스 자작 자산 plot list** (시간 여유 시 1–2개 선택)
   - **CS-RAG 시스템** (Teams API + FAISS + Bedrock, 5 Phase)
   - **Tmux Orchestrator** (286→1,403 추출, 24/7) ← cc-orchestra의 영감 출처로 자연 연결
   - **AI-Practice-Master.md** (306KB / 52 노트)
   - **Approvaltests IntelliJ plugin** (vibe coding 무지식 정복)
   - **Bedrock Agent 데모** (2일·33 Task·38 commit)

**자작 자산 등장:** `cc-orchestra` (메인), `vault-intelligence`, `vis-intelligence`, `Tmux-Orchestrator`, `cs-rag`, `AI-Practice-Master`, (보너스: `Approvaltests plugin`, `bedrock-agent-demo`)

**라이브 실패 대비:**
- ccup 한 줄 시연 실패 → cc-orchestra recorded 영상 즉시 전환
- 6 pane이 모두 떠야 임팩트 큼 → 사전 워밍업 필수

**Failure Conditions:**
- 라이브 6 pane이 청중 화면 가독성에서 깨지면 → "큰 글꼴 + 1 pane만 확대" 백업 시나리오
- "이건 너무 고급이다" 반응이면 → "오늘 도착 안 해도 OK. 1:1 페어부터 충분" 메시지로 회복

**Failure Conditions:**
- Phase 1이 화려함에 매몰돼 envy → 좌절로 가면 → Phase 2 로드맵으로 즉시 회복
- 30일 로드맵이 현실감 떨어지면 → "Day 1 오늘 저녁 30분으로 시작" 단언

### 4.7 Close (40m)

**Output Format:** 10m 청중 노트 작성 + 10m 5개 정리 + 10m Farley 수미상관 + 10m Q&A 워밍업

**5개 즉시 시도 거리 (10m)** — 청중이 그 자리에서 적어가는 것:
1. `~/.claude/CLAUDE.md`에 본인 역할·도메인·말투 5줄
2. `/commit` skill 설치 (한글 안전 커밋)
3. MCP 서버 1개 연결 (Context7 또는 GitHub)
4. brainstorming → writing-plans → executing-plans 워크플로우 1회
5. `msbaek-claude-plugins` install — TDD 도구 무료

**Farley 수미상관 (10m)** — Open에서 인용한 3요소 재인용:
> "프로그래밍의 본질은 3가지입니다. 문제 이해 / Executable form 변환 / 검증.
> AI 시대에도 변하지 않습니다. 다만 ②번의 메커니즘이 달라질 뿐.
> 오늘 보여드린 모든 것이 그 ②번의 진화입니다."

**Q&A 워밍업 (10m)** — 사전 준비된 5개 질문 노출:
1. "보안·사외 반출 정책은?" → 로컬 동작 / `humanize-korean` 같은 PII 처리 / 회사 정책 우회 X
2. "주니어가 쓰면 안 되지 않나?" → vault `AI is Making Junior Developers Extinct.md` / Amazon Senior Review 정책
3. "이미 Cursor/Copilot 쓰는데?" → 보완재 (각자 강점 다름)
4. "토큰 비용은?" → vault `Claude-Opus-4.7-토큰-비용-최적화-종합-가이드.md`
5. "skill 만드는 데 얼마나 걸리나?" → /skillify 사용 시 10–30분 (앞서 라이브로 입증)

**커피타임 명언 인용 (Close 마무리):**
- 자작 사례: `coffee-time` repo (`~/git/kt4u/coffee-time`, [github.com/ktown4u/coffee-time](http://github.com/ktown4u/coffee-time)) — "AI 활용 공유를 위한 팀 의례. 47개 회의록이 쌓였다."
- 명언 3개:
  - "프롬프트가 프로그램이고, AI는 진보된 컴파일러"
  - "코딩이 차지하는 비중은 전체 공정의 6%"
  - "아는 만큼 보인다 — AI에게 좋은 질문을 하려면 많이 알아야 함"
- **사내 격차 메시지 회수**: "오늘 보여드린 도구는 가져가실 수 있습니다. 하지만 격차 해소의 진짜 도구는 — 매주 30분, 동료끼리 AI 활용 공유하는 자리입니다. 우리 팀은 이걸 47번 했습니다."

**최종 한 줄 (강연 마무리):**
> "AI 페어 프로그래밍의 다음 단계는 더 좋은 AI를 만나는 것이 아니라, 더 잘 위임하는 법을 배우는 것입니다. 도구의 진화가 아니라 일하는 사람의 진화입니다." — cc-orchestra-brunch.md

**Failure Conditions:**
- 5개가 추상적이면 → 각각 "오늘 저녁 30분 / 내일 점심 / 이번 주말" 시점 명시

### 4.8 Q&A (45m)

**Output Format:** 5–10개 질문 처리, 미답 시 메일 follow-up 약속

**라이브 회복 전략:**
- Q&A 질문이 적으면 → 사전 준비된 5개 자문자답
- 한 주제가 길어지면 → "후속 질문은 메일/Slack" 안내

---

## 5. Verification — 강연 성공 측정

### 5.1 라이브 운영 검증

- [ ] 데모 6개 모두 60초 안에 응답 도착 (visd cold start 포함)
- [ ] 405분 ±15분 안에 종료 (Q&A 45분 확보)
- [ ] fallback 영상 전환 5초 이내
- [ ] 청중 질문 5건 이상 확보 (적극성 지표)

### 5.2 청중 반응 검증

- [ ] 강연 직후 설문 (QR): 응답률 50%+ / NPS 8+ / "1주일 내 시도 의향" 60%+
- [ ] 2주 후 follow-up: 시도 사례 3건 이상 수집 (CLAUDE.md / skill / hook 중 어느 형태든)
- [ ] `msbaek-claude-plugins` repo 강연 후 1주 내 star/fork 5건 이상

### 5.3 메시지 정렬 검증

- [ ] Open에서 약속한 "30년 경력 + 매일 페어 + 도구 진화" narrative가 Close까지 일관되게 흐름
- [ ] "AI가 짠다"가 아니라 "30년 개발자가 4.7과 짠다"가 매 Act에 등장
- [ ] Farley 3요소가 Open · Close 두 지점에 등장 (수미상관)
- [ ] envy 끝에 30일 로드맵으로 실행 가능성 회복 (좌절 방지)

---

## 6. 결정 요약 — Design Trade-offs

| 결정 | 채택 | 기각된 대안 | 근거 |
|---|---|---|---|
| Day in the Life narrative 유지 | ✓ | 3단계 프레임으로 완전 재구성 | 연사 차별점(라이브 데모) 보존 |
| 3단계 라벨링 + 미니강의 30m | ✓ | 라벨만 붙이기 | 발주처 요구 표면적 충족 회피 |
| TDD agent를 Act 2 후반에 흡수 | ✓ | TDD 별도 세션 | "TDD 제외" 발주처 조건 충족 |
| Farley 인용을 Open·Act 3·Close 3회 | ✓ | 단일 인용 | 권위 + 사상적 깊이 (cc-orchestra가 Farley 인용 자체 보유) |
| Act 3 Phase 3 = cc-orchestra 클라이맥스 (30m) | ✓ | 5개 사례 균등 나열 | "AI 페어의 다음 단계" narrative + 발표자 최신 발견 |
| 실습 비중 5% (Q&A 위주) | ✓ | 페어 워크숍 33% | 100명 운영 + 라이브 임팩트 |
| envy-driven 유지 + 격차 메시지 추가 | ✓ | envy 톤 약화 | "도구 문제 아닌 의식 문제" 회복 |
| QR install + 점심 후 자가 진행 | ✓ | 라이브 100명 install | 보안·네트워크 변수 회피 |

**YAGNI (의도적 제외):**
- 멀티 Agent 병렬 orchestration 상세 (Tmux Orchestrator는 *사례 언급*만)
- BMAD / Superpowers 전체 framework 소개
- TDD 자체 교육 (agent 사례로만)
- 페어 / 그룹 워크숍 (운영 부담)

---

## 7. 활용 자료 매핑

### 7.1 자작 자산 (vault `나의 AI 활용 사례.md`에서 발췌)

| # | 사례 | 등장 위치 |
|---|---|---|
| 1 | ktown4u-masking (Spring Profile + Jackson + CodeArtifact) | Act 2 전반 (1단계 고통 식별) |
| 2 | DB 스크럽 (21테이블 · 91% 감축) | Act 2 전반 (1단계 보강) |
| 3 | CS-RAG (Teams + FAISS + Bedrock) | Act 3 Phase 3 (보너스) |
| 4 | TDD-AGENT (msbaek-claude-plugins) | **Act 2 후반 (50m 전체)** |
| 5 | **cc-orchestra (1:N orchestration)** ★ | **Act 3 Phase 3 (30m 클라이맥스)** + Close 최종 메시지 |
| 6 | Approvaltests IntelliJ plugin | Act 3 Phase 3 (보너스) |
| 7 | vault-intelligence (4개월 / 9 Phase) | **Act 3 Phase 1 (메인)** |
| 8 | Bedrock Agent 데모 (2일·33 Task) | Act 3 Phase 3 (보너스) |
| 9 | 병렬 에이전트 (286→1,403 추출) | Act 3 Phase 3 (Tmux Orchestrator와 함께) |
| 10 | Tmux Orchestrator (24/7 자율) | Act 3 Phase 3 (cc-orchestra 영감 출처) |
| 11 | Claude Code Skills 5종 | Act 1 + Act 2 운영화 |
| 12 | ISMS-P + NotebookLM | Q&A 보안 질문 |
| 13 | **coffee-time repo** (정식 GitHub) | **Close (격차 해소 회수 메시지)** |
| 14 | AI-Practice-Master.md (306KB / 52 노트) | Act 3 Phase 3 (보너스) |
| 15 | AI-문제점 종합 분석 (1,800줄) | Q&A 학습 질문 (예비) |
| 16 | 기술 문서 번역/요약 자동화 | Act 2 운영화 (`/weekly-newsletter` 흐름 내) |
| 17 | 논문 이해 (LLM 대화) | Q&A 학습 질문 (예비) |
| 18 | 매일 아침 루틴 (skill 5종) | **Act 1 (전체)** |
| 19 | 커피타임 변화 + 명언 3개 | Open + Close |

**커버리지: 19개 중 19개 = 100%** (단, Q&A 예비 사례 2개는 청중 질문에 따라 사용)

**시간 비중 (자작 자산 등장 시간):**
- Act 1 (40m) 100% — 매일 루틴 + skill 5종
- Act 2 전반 (100m) 80% — ktown4u-masking + DB 스크럽 + Claude Code Skills + 기술문서 번역
- Act 2 후반 (50m) 100% — TDD-AGENT
- Act 3 Phase 1 (60m) 100% — vault-intelligence
- **Act 3 Phase 3 (30m) 100% — cc-orchestra 메인 + 보너스 5종**
- Close (40m) 50% — coffee-time + 명언

### 7.2 Vault 인용 자료

| 위치 | 자료 |
|---|---|
| Open | `After 180 Days of Daily AI Pair Programming.md` |
| Open · Close | `Acceptance Testing Is the FUTURE of Programming - Dave-Farely.md` |
| 미니강의 (프롬프트) | `Prompt-Contracts-From-Vibe-Coding-to-Shipping-with-Claude-Code.md` / `Slow Think의 놀라운 효과.md` / `Claude XML 프롬프팅 고급 기법.md` |
| 미니강의 (컨텍스트) | `Context-Engineering-for-Coding-Agents.md` / `AI 활용 기법 완전 가이드 - Prompt / Context / Harness Engineering.md` |
| 미니강의 (하네스) | `Claude Code - Hook을 통한 자동화.md` / `AI도 혼자 일하면 망하는 이유: 앤스로픽의 하네스 시스템.md` |
| Act 2 | `work-log/2026-ISMS/ISMS_Aurora_DB_감사로그_분석_지침서.md` |
| Act 2 후반 | `TDD and Generative AI – A Perfect Pairing.md` / `Should We Revisit XP in the Age of AI.md` |
| Act 3 | `LLM-Wiki-Skill-Build-a-Second-Brain-With-Claude-Code-and-Obsidian.md` / `grep은-죽었다.md` |
| Act 3 Phase 3 ★ | `003-RESOURCES/AI/USECASES/MINE/cc-orchestra-brunch.md` (메인) + Anthropic *Building effective agents* (orchestrator-workers) + Conway's Law + Dave Farley *Modern Software Engineering* + Doug McIlroy Unix 철학 |
| Close | `003-RESOURCES/AI/USECASES/MINE/cc-orchestra-brunch.md` (최종 한 줄 인용) |
| Q&A | `Claude-Opus-4.7-토큰-비용-최적화-종합-가이드.md` / `AI is Making Junior Developers Extinct.md` |

### 7.3 라이브 시연 워크스페이스

- `~/git/kt4u/enc-mask/` — Act 2 전반 ISMS
- `~/git/msbaek-claude-plugins/msbaek-tdd` — Act 2 후반 TDD plugin
- `~/git/vault-intelligence` — Act 3 vis 본체
- `~/DocumentsLocal/msbaek_vault/` — Act 3 vault 시연

---

## 8. 프로덕션 체크리스트 (Resume Point용)

### 8.1 사전 준비 (강연 전 4주)

- [ ] 라이브 데모 전체 리허설 1회 (시간 측정 + 실패 지점 기록)
- [ ] 핵심 6개 데모 recorded fallback 영상 제작:
  - `/recall yesterday` + `morning-auto.sh` (Act 1)
  - `/skillify` ISMS 메타 모먼트 (Act 2 전반)
  - `/weekly-newsletter` (Act 2 운영화)
  - `/tdd-rgb` 사이클 (Act 2 후반)
  - `vis search` + `vis generate-moc` (Act 3 Phase 1)
  - `ccup` cc-orchestra (Act 3 Phase 3) ★
- [ ] 청중 take-home PDF 1장 — "5개 즉시 시도 거리 + 30일 로드맵 + QR(repo)"
- [ ] 슬라이드 작성 (Open 8장 / 미니강의 12장 / Act별 5–10장 / Close 5장)
- [ ] `msbaek-claude-plugins` README 영문판 점검 (외부 청중 대비)
- [ ] visd 데몬 확실히 켜둘 것 — Act 3 데모 dependency

### 8.2 라이브 시 회복 전략

- 어떤 데모든 30초 안에 응답이 오지 않으면 즉시 fallback 영상
- 청중 반응 떨어지면 즉흥 Q&A로 전환 (Open에서 청중 회사 도메인 미리 청취)
- 인터넷·API 장애 가정 — vault 검색·`extract-sql-log` 등은 모두 로컬 동작 (강조)

### 8.3 사후 측정

- 강연 직후 짧은 설문 (QR): 가장 인상 깊은 데모 / 1주일 내 시도 의향
- 2주 후 follow-up — 청중 시도 사례 수집 → 다음 강연·블로그 소재

---

## 9. Open Questions (TBD)

다음 항목은 발주처와 조율 필요:

- [ ] **발주처 회사명 / 도메인** — Act 2 ISMS 사례가 청중 도메인에 매핑되는지 점검
- [ ] **강연 일자 / 장소** — 라이브 install 가능성 (보안 정책)에 영향
- [ ] **인터넷 환경** — visd / marketplace install / GitHub access 가능 여부
- [ ] **녹화 가능 여부** — 사후 vault 보존 + 다음 강연 소재
- [ ] **발주처가 명시한 "실습 비중"이 5%로 충분한가** — 충분치 않으면 Act 3 Phase 2(30일 로드맵)에서 청중 자기 평가 워크시트 추가

---

## 10. Next Steps

1. **이 spec을 사용자가 리뷰** — 변경 사항 반영 후 commit
2. **writing-plans skill 호출** — spec 기반 30분 단위 실행 가능한 plan 작성
3. **리허설 1회 진행** — plan에 따라
4. **fallback 영상 제작 착수** — 핵심 6개 데모

---

## Decision Log

- **2026-05-11 v1**: 기존 `.claude/plans/2026-05-08-claude-code-talk/plan.md` (외부 청중 4시간) 자산을 사내 청중 8시간 강연으로 확장. TDD agent를 Act 2 후반에 흡수 (별도 세션 X). Farley 인용 수미상관 추가.
- **2026-05-11 v2**: 사용자가 `나의 AI 활용 사례.md` 수정 — cc-orchestra + coffee-time 정식 등록. Act 3 Phase 3를 cc-orchestra 클라이맥스(30m)로 전면 재구성 — "AI 페어의 다음 단계" narrative + Conway's Law + Anthropic orchestrator-workers + Farley *Modern Software Engineering* 인용. Close에 coffee-time + 최종 한 줄 인용 추가. 자산 커버리지 14→19, 100% 유지.
