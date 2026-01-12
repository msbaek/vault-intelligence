# Batch 09 - AI 활용 기법 추출 결과

**처리일**: 2026-01-03
**처리 파일 수**: 10개 (81-90)
**추출 기법 수**: 129개

---

## 처리된 문서 목록

1. Claude-Code-Skills-Deep-Dive-Part-2.md (15개 기법)
2. Claude-Code-Slash-Commands-시간을-절약하는-재사용-가능한-명령어-만들기.md (16개 기법)
3. Claude-Code-v2-0-28-Specialized-Subagents.md (10개 기법)
4. Claude-Code-LSP-사용법-버그-수정-빠르게-하기.md (9개 기법)
5. Claude-Mem-Giving-Claude-Code-a-Long-Term-Memory.md (8개 기법)
6. Claude-Sonnet-4.5-Full-Stack-App-Build-Test.md (17개 기법)
7. Code Smarter, Not Harder- AI-Powered Dev Hacks for All.md (21개 기법)
8. Code-like-a-surgeon.md (10개 기법)
9. Codex 개발자와의 대담.md (15개 기법)
10. Coding Guidelines for Your AI Agents.md (8개 기법)

---

## 문서 1: Claude-Code-Skills-Deep-Dive-Part-2.md

### Reference Files와 Lazy Loading
- **카테고리**: 도구 활용
- **설명**: 전체 문서를 미리 로드하는 대신, Skill을 경량 라우터로 설계하여 현재 작업에 필요한 특정 레퍼런스만 필요할 때 로드한다. 이 방식으로 토큰 사용량을 78-85%까지 절감할 수 있으며, 컨텍스트 오버플로우를 방지한다.
- **출처**: Claude-Code-Skills-Deep-Dive-Part-2.md

### PDA(Partial Data Automation) 아키텍처
- **카테고리**: AI 에이전트/협업
- **설명**: Skills를 "오케스트레이터(orchestrator)"로 설계하고 "백과사전(encyclopedia)"이 되지 않도록 한다. 필요한 것만 필요할 때 로드하는 지연 로딩 방식으로 가볍고 빠르고 복원력 있는 시스템을 구축한다.
- **출처**: Claude-Code-Skills-Deep-Dive-Part-2.md

### Scripts for Mechanical Work
- **카테고리**: 워크플로우
- **설명**: API 작업, 데이터 변환, 복잡한 처리를 스크립트로 분리하여 컨텍스트에서 제외한다. 스크립트는 컨텍스트에 로드되지 않아 제로 토큰 비용을 달성하며, 독립적으로 pytest로 테스트할 수 있고 여러 skill에서 재사용 가능하다.
- **출처**: Claude-Code-Skills-Deep-Dive-Part-2.md

### 3계층 아키텍처 (관심사의 분리)
- **카테고리**: 워크플로우
- **설명**: User Layer(사용자 요청) → AI Orchestrator Layer(결정 수행, 지능 제공) → Script Layer(기계적 작업 실행) → External APIs의 계층 구조를 유지한다. AI는 지능과 사용자 경험을 제공하고, 스크립트는 기계적 작업을 처리하는 프롬프트 엔지니어링에 적용된 관심사의 분리 원칙이다.
- **출처**: Claude-Code-Skills-Deep-Dive-Part-2.md

### AI Resilience Layer
- **카테고리**: AI 에이전트/협업
- **설명**: 스크립트 오류를 AI가 해석하고 사용자를 안내하는 복원력 계층을 구축한다. 오류를 "안내의 기회"로 변환하여 딱딱한 오류 메시지 대신 유용하고 적응적인 안내를 제공한다.
- **출처**: Claude-Code-Skills-Deep-Dive-Part-2.md

### Retry with Correction 패턴
- **카테고리**: AI 에이전트/협업
- **설명**: 스크립트 실패 시 (1) 특정 오류 해석 (2) 오류 수정 가능 여부 확인 (3) 수정 전략 결정 (4) 수정 적용 또는 사용자 가이드 (5) 자동 재시도 (6) 결과 보고의 순서로 처리한다.
- **출처**: Claude-Code-Skills-Deep-Dive-Part-2.md

### Graceful Degradation 패턴
- **카테고리**: AI 에이전트/협업
- **설명**: 스크립트가 사용 불가능하거나 반복 실패 시 수동 대안 워크플로우를 제공하고 단계별 수동 지침을 제공한다.
- **출처**: Claude-Code-Skills-Deep-Dive-Part-2.md

### Progressive Disclosure 패턴
- **카테고리**: AI 에이전트/협업
- **설명**: 오류 처리를 점진적으로 확대한다: 초기 시도 → 첫 번째 실패(자동 복구) → 두 번째 실패(대안 접근) → 세 번째 실패(상세 디버깅) → 지속적 실패(전문가 가이드).
- **출처**: Claude-Code-Skills-Deep-Dive-Part-2.md

### Reference File 조직 전략
- **카테고리**: 도구 활용
- **설명**: Reference 파일을 세 가지 전략으로 조직한다: By Use Case(대부분의 skill에 권장), By Complexity Level(교육용), By Feature Area(복잡한 도구). 파일당 5-15KB를 목표로 한다.
- **출처**: Claude-Code-Skills-Deep-Dive-Part-2.md

### 구조화된 오류 메시지 설계
- **카테고리**: 프롬프트 엔지니어링
- **설명**: 스크립트의 오류 메시지를 AI가 파싱하고 지능적으로 처리할 수 있도록 오류 코드, 오류 유형, 상세 정보를 포함하여 구조화한다.
- **출처**: Claude-Code-Skills-Deep-Dive-Part-2.md

### Clear Input/Output Contract
- **카테고리**: 도구 활용
- **설명**: 스크립트에 명확한 입출력 계약을 정의한다. 입력(sys.argv, 환경 변수), 출력(stdout 형식), 종료 코드를 명시적으로 문서화하여 AI가 스크립트와 정확하게 상호작용할 수 있도록 한다.
- **출처**: Claude-Code-Skills-Deep-Dive-Part-2.md

### PDA Decision Checklist
- **카테고리**: 워크플로우
- **설명**: PDA 적용 여부를 결정하는 체크리스트: 10KB 초과 문서, 복수 사용 사례, 외부 API 통합, 복잡한 처리, 시간에 따라 성장할 skill. 2개 이상 해당되면 PDA 적용.
- **출처**: Claude-Code-Skills-Deep-Dive-Part-2.md

### 3인칭 명령형 작성 스타일
- **카테고리**: 프롬프트 엔지니어링
- **설명**: Skill 프롬프트 작성 시 명령형/부정사형을 사용하고, Description은 3인칭으로 작성하여 Claude가 언제 이 skill을 사용해야 하는지 명확히 이해하도록 한다.
- **출처**: Claude-Code-Skills-Deep-Dive-Part-2.md

### Single Responsibility Script 패턴
- **카테고리**: 도구 활용
- **설명**: 각 스크립트가 단일 책임만 갖도록 분리한다. upload, download, search, create처럼 하나의 작업만 수행하는 스크립트로 분리하여 재사용성과 테스트 용이성을 높인다.
- **출처**: Claude-Code-Skills-Deep-Dive-Part-2.md

### Context Rot 방지
- **카테고리**: 생산성/마인드셋
- **설명**: LLM이 필요로 하지 않는 정보로 컨텍스트를 넘치게 하면 혼란이 발생하고 처리 시간과 토큰 비용이 증가한다. 40KB 모놀리스 파일 대신 8-10KB 파일들로 분리한다.
- **출처**: Claude-Code-Skills-Deep-Dive-Part-2.md

---

## 문서 2: Claude-Code-Slash-Commands-시간을-절약하는-재사용-가능한-명령어-만들기.md

### 슬래시 명령어로 반복 작업 자동화
- **카테고리**: 도구 활용
- **설명**: Claude Code의 `.claude/commands/` 디렉토리에 마크다운 파일로 슬래시 명령어를 정의하여 반복적인 개발 작업을 단일 명령어로 자동화한다. 토큰 사용량 20%까지 절감 가능.
- **출처**: Claude-Code-Slash-Commands.md

### 컨텍스트 주입을 위한 ! 접두사 활용
- **카테고리**: 프롬프트 엔지니어링
- **설명**: 슬래시 명령어에서 `!` 접두사를 사용하면 프롬프트 실행 전에 bash 명령을 먼저 실행하여 Claude에게 완벽한 컨텍스트를 제공할 수 있다.
- **출처**: Claude-Code-Slash-Commands.md

### $ARGUMENTS 변수로 유연한 명령어 설계
- **카테고리**: 프롬프트 엔지니어링
- **설명**: `$ARGUMENTS` 변수를 활용하여 하나의 명령어가 다양한 입력에 대응하도록 설계한다. 컴포넌트명, 이슈 번호, 파일 경로 등 다양한 인자를 받아 처리하는 유연한 명령어를 만든다.
- **출처**: Claude-Code-Slash-Commands.md

### Frontmatter를 통한 AI 행동 제어
- **카테고리**: 도구 활용
- **설명**: 마크다운 frontmatter에 `allowed-tools`, `model`, `argument-hint`, `description` 등을 정의하여 AI의 도구 사용 범위, 모델 선택, 사용법 힌트를 명시적으로 제어한다.
- **출처**: Claude-Code-Slash-Commands.md

### @ 참조로 기존 코드 패턴 전달
- **카테고리**: 프롬프트 엔지니어링
- **설명**: `@` 접두사로 기존 파일을 참조하여 AI에게 팀의 코딩 스타일, 기존 패턴, 문서 표준 등을 전달한다.
- **출처**: Claude-Code-Slash-Commands.md

### GitHub 이슈 엔드투엔드 자동 처리
- **카테고리**: 워크플로우
- **설명**: `/fix-issue` 명령어로 GitHub 이슈 조회부터 분석, 브랜치 생성, 구현, 테스트, PR 생성까지 전체 워크플로우를 자동화한다.
- **출처**: Claude-Code-Slash-Commands.md

### 스마트 커밋 메시지 자동 생성
- **카테고리**: 워크플로우
- **설명**: `/commit` 명령어로 현재 git 상태, staged 변경사항, 최근 커밋 히스토리를 자동 분석하여 Conventional Commit 형식의 적절한 커밋 메시지를 생성한다.
- **출처**: Claude-Code-Slash-Commands.md

### 보안 리뷰 체크리스트 자동화
- **카테고리**: 보안/테스트
- **설명**: `/security-review` 명령어로 인증/권한, 입력 검증(SQL 인젝션, XSS, 명령 인젝션), 데이터 보호, 의존성 취약점 등을 체계적으로 분석한다.
- **출처**: Claude-Code-Slash-Commands.md

### 성능 최적화 분석 자동화
- **카테고리**: 코드 품질
- **설명**: `/optimize` 명령어로 시간 복잡도, 메모리 사용, I/O 작업, 데이터베이스 쿼리 효율성 등을 분석하고 최적화 전략을 제안한다.
- **출처**: Claude-Code-Slash-Commands.md

### 팀 표준을 명령어에 내장
- **카테고리**: AI 에이전트/협업
- **설명**: `.eslintrc.js`, `prettier.config.js`, `CODING_STANDARDS.md` 등 팀의 규칙과 표준을 슬래시 명령어에 참조로 포함시켜 AI가 팀 표준을 자동으로 따르게 한다.
- **출처**: Claude-Code-Slash-Commands.md

### 계층적 명령어 조직 시스템
- **카테고리**: 워크플로우
- **설명**: `.claude/commands/` 아래에 git/, react/, testing/, docs/ 등 카테고리별 디렉토리를 구성하여 명령어를 체계적으로 관리한다.
- **출처**: Claude-Code-Slash-Commands.md

### 복합 명령어 워크플로우 체이닝
- **카테고리**: 워크플로우
- **설명**: 여러 슬래시 명령어를 순차적으로 실행하여 전체 기능 개발 워크플로우를 자동화한다.
- **출처**: Claude-Code-Slash-Commands.md

### 신입 온보딩 자동화 명령어
- **카테고리**: AI 에이전트/협업
- **설명**: `/onboarding` 명령어로 개발 환경 설정, 의존성 설치, 환경 파일 복사, 빌드/테스트 실행 등 신입 팀원의 온보딩 과정을 자동화한다.
- **출처**: Claude-Code-Slash-Commands.md

### 안전장치를 내장한 명령어 설계
- **카테고리**: 보안/테스트
- **설명**: 슬래시 명령어에 사전 검증 로직을 내장하여 오류를 방지한다. git 저장소 여부 확인, 커밋되지 않은 변경 확인 등 안전장치를 포함한다.
- **출처**: Claude-Code-Slash-Commands.md

### 명령어의 자체 문서화
- **카테고리**: 생산성/마인드셋
- **설명**: 슬래시 명령어 내에 사용 예시, 수행 작업 설명, 생성되는 파일 목록 등을 포함하여 별도 문서 없이 명령어 자체가 문서 역할을 한다.
- **출처**: Claude-Code-Slash-Commands.md

### 암묵지를 형식지로 변환
- **카테고리**: 생산성/마인드셋
- **설명**: 개발자의 경험과 베스트 프랙티스(TDD, 리팩토링, 클린 코드 등)를 슬래시 명령어에 명시적으로 코드화한다.
- **출처**: Claude-Code-Slash-Commands.md

---

## 문서 3: Claude-Code-v2-0-28-Specialized-Subagents.md

### 전용 Plan 서브에이전트를 통한 계획-구현 분리
- **카테고리**: AI 에이전트/협업
- **설명**: 복잡한 작업 수행 시 Plan 서브에이전트가 아키텍처 분석과 계획 수립에만 전념하고, 계획 완료 후 컨텍스트를 완전히 해제한다. 컨텍스트 오염 문제를 해결한다.
- **출처**: Claude-Code-v2-0-28-Specialized-Subagents.md

### 재개 가능한 서브에이전트를 통한 반복적 계획 정제
- **카테고리**: 워크플로우
- **설명**: 서브에이전트를 재개(resume)하여 대화 상태를 유지한다. 요구사항 변경 시 전체 컨텍스트를 재제공하지 않고 변경된 제약 조건만 전달하여 효율적으로 계획을 조정한다.
- **출처**: Claude-Code-v2-0-28-Specialized-Subagents.md

### 작업 복잡도 기반 동적 모델 선택
- **카테고리**: AI-Ops
- **설명**: 작업 복잡도에 따라 Opus(복잡한 아키텍처), Sonnet(표준 구현), Haiku(반복 작업)를 자동으로 선택한다. 비용과 품질을 최적화한다.
- **출처**: Claude-Code-v2-0-28-Specialized-Subagents.md

### 예산 제어를 통한 자율 에이전트 프로덕션 안전성 확보
- **카테고리**: AI-Ops
- **설명**: `--max-budget-usd` 플래그로 작업별 API 사용 비용 한계를 설정한다. 무인 실행 시 폭주 실행을 방지한다.
- **출처**: Claude-Code-v2-0-28-Specialized-Subagents.md

### 에이전트 전문화 패턴으로 멀티 에이전트 아키텍처 구축
- **카테고리**: AI 에이전트/협업
- **설명**: 범용 에이전트 대신 명확한 도메인과 격리된 컨텍스트를 가진 전문화된 서브에이전트를 구축한다. 보안 감사자, 성능 프로파일러 등 각각이 독립적으로 작동한다.
- **출처**: Claude-Code-v2-0-28-Specialized-Subagents.md

### 컨텍스트 오염 방지를 위한 작업 격리
- **카테고리**: 워크플로우
- **설명**: 계획, 탐색, 구현 정보가 뒤섞여 원래 요구사항을 놓치는 컨텍스트 오염 문제를 인식하고 방지한다. 각 에이전트가 특정 도메인에 집중된 컨텍스트를 유지한다.
- **출처**: Claude-Code-v2-0-28-Specialized-Subagents.md

### AI 계획을 시니어 엔지니어 PR처럼 비판적 검토
- **카테고리**: 코드 품질
- **설명**: AI 생성 계획을 검토 없이 구현하지 않고, 시니어 엔지니어의 풀 리퀘스트처럼 취급한다. 비판적으로 검토하고 가정에 도전한다.
- **출처**: Claude-Code-v2-0-28-Specialized-Subagents.md

### 예산 한계 보정을 통한 최적 설정
- **카테고리**: AI-Ops
- **설명**: 처음에는 한계 없이 작업을 실행하여 기준선을 확립한다. 실제 API 비용을 추적한 후 일반적인 비용의 1.5배 정도로 한계를 설정한다.
- **출처**: Claude-Code-v2-0-28-Specialized-Subagents.md

### 동적 모델 선택 로그 검토 및 조정
- **카테고리**: AI-Ops
- **설명**: 동적 모델 선택을 블랙박스로 취급하지 않고 주기적으로 로그를 검토한다. 경량 모델이 어려움을 겪으면 서브에이전트 모델 기본 설정을 조정한다.
- **출처**: Claude-Code-v2-0-28-Specialized-Subagents.md

### 팀 전체 공유 서브에이전트 정의 관리
- **카테고리**: AI 에이전트/협업
- **설명**: 사용자 정의 서브에이전트를 팀 공유 리소스로 관리한다. `.claude/agents/`에 팀 전체 서브에이전트, `.claude/local-agents/`에 개인 실험적 에이전트를 분리한다.
- **출처**: Claude-Code-v2-0-28-Specialized-Subagents.md

---

## 문서 4: Claude-Code-LSP-사용법-버그-수정-빠르게-하기.md

### Claude Code LSP 활성화 및 설정
- **카테고리**: 도구 활용
- **설명**: Claude Code에서 Language Server Protocol(LSP)을 활성화하여 IDE 수준의 코드 인텔리전스를 CLI에서 사용할 수 있다. `ENABLE_LSP_TOOLS=1` 환경 변수 설정이 필요하다.
- **출처**: Claude-Code-LSP-사용법-버그-수정-빠르게-하기.md

### LSP Go-to-Definition으로 코드 정의 위치 즉시 탐색
- **카테고리**: 도구 활용
- **설명**: "Where is the processRequest function defined use LSP?" 형태의 프롬프트로 함수나 심볼의 정의 위치를 즉시 찾을 수 있다.
- **출처**: Claude-Code-LSP-사용법-버그-수정-빠르게-하기.md

### LSP Find References로 코드베이스 전체 참조 추적
- **카테고리**: 도구 활용
- **설명**: "Find all references to the displayError function use LSP" 프롬프트로 함수, 변수, 클래스가 사용되는 모든 위치를 찾는다.
- **출처**: Claude-Code-LSP-사용법-버그-수정-빠르게-하기.md

### LSP Hover로 함수 시그니처 및 문서 조회
- **카테고리**: 도구 활용
- **설명**: "What parameters does the displayBooks function accept use LSP?" 프롬프트로 필수/선택 파라미터, 타입, 설명 문서를 조회할 수 있다.
- **출처**: Claude-Code-LSP-사용법-버그-수정-빠르게-하기.md

### LSP Real-Time Diagnostics로 실행 전 에러 감지
- **카테고리**: 코드 품질
- **설명**: LSP가 활성화되면 모든 편집 후 언어 서버가 진단(에러, 경고, 힌트)을 Claude Code에 보고한다.
- **출처**: Claude-Code-LSP-사용법-버그-수정-빠르게-하기.md

### 프롬프트에 "use LSP" 명시적 지정
- **카테고리**: 프롬프트 엔지니어링
- **설명**: Claude Code가 예상대로 LSP를 사용하지 않을 때 프롬프트에 "use LSP"를 명시적으로 추가한다.
- **출처**: Claude-Code-LSP-사용법-버그-수정-빠르게-하기.md

### LSP Document Symbol로 파일 구조 파악
- **카테고리**: 도구 활용
- **설명**: "Show me all the symbols in backend/index.js use LSP" 프롬프트로 파일에 정의된 모든 클래스, 함수, 변수를 구조화된 목록으로 파악할 수 있다.
- **출처**: Claude-Code-LSP-사용법-버그-수정-빠르게-하기.md

### LSP Workspace Symbol로 프로젝트 전체 심볼 검색
- **카테고리**: 도구 활용
- **설명**: "Find all methods that contain innerHTML" 프롬프트로 텍스트가 아닌 실제 코드 심볼을 프로젝트 전체에서 검색한다.
- **출처**: Claude-Code-LSP-사용법-버그-수정-빠르게-하기.md

### LSP 사용 적합성 판단 기준
- **카테고리**: 워크플로우
- **설명**: LSP는 대규모 코드베이스, 여러 파일에 걸친 복잡한 디버깅, 정확한 함수 시그니처 파악, 리팩토링 영향 분석에 적합하다.
- **출처**: Claude-Code-LSP-사용법-버그-수정-빠르게-하기.md

---

## 문서 5: Claude-Mem-Giving-Claude-Code-a-Long-Term-Memory.md

### 세션 간 영구 메모리 시스템
- **카테고리**: 도구 활용
- **설명**: Claude-Mem 플러그인을 사용하여 AI 코딩 어시스턴트의 세션 간 컨텍스트를 유지한다. 프롬프트, 도구 사용 내역, 관찰 결과, 세션 요약 등을 자동으로 캡처하여 SQLite에 로컬 저장한다.
- **출처**: Claude-Mem-Giving-Claude-Code-a-Long-Term-Memory.md

### 점진적 공개(Progressive Disclosure) 패턴
- **카테고리**: 프롬프트 엔지니어링
- **설명**: 모든 컨텍스트를 한 번에 주입하는 대신, 세션 시작 시 관찰 제목과 토큰 비용 추정치만 주입하고 필요할 때만 상세 정보를 검색하는 레이어 방식을 사용한다.
- **출처**: Claude-Mem-Giving-Claude-Code-a-Long-Term-Memory.md

### 자연어 기반 히스토리 검색
- **카테고리**: AI 에이전트/협업
- **설명**: "How did we implement authentication?"와 같은 자연어 질문으로 프로젝트 히스토리를 검색한다. FTS5 키워드 검색과 시맨틱 벡터 검색을 결합한 하이브리드 검색 방식을 사용한다.
- **출처**: Claude-Mem-Giving-Claude-Code-a-Long-Term-Memory.md

### 프라이버시 태그 기반 민감 정보 보호
- **카테고리**: 보안/테스트
- **설명**: `<private>API_KEY=super-secret</private>` 형태로 민감한 내용을 래핑하면 Claude-Mem이 해당 내용을 저장소에서 자동으로 제외한다.
- **출처**: Claude-Mem-Giving-Claude-Code-a-Long-Term-Memory.md

### 지능적 컨텍스트 압축
- **카테고리**: 생산성/마인드셋
- **설명**: 원시 트랜스크립트를 그대로 저장하는 대신 AI가 지능적으로 정보를 압축한다. 유용한 것만 주입하고 필요할 때 AI가 추가 정보를 요청할 수 있게 한다.
- **출처**: Claude-Mem-Giving-Claude-Code-a-Long-Term-Memory.md

### 자동 관찰 캡처 및 학습 추출
- **카테고리**: 워크플로우
- **설명**: 코딩 세션 중 모든 도구 실행과 결과를 자동으로 캡처한다. 백그라운드 Worker가 이러한 관찰에서 학습 내용을 추출하고 세션 요약을 생성한다.
- **출처**: Claude-Mem-Giving-Claude-Code-a-Long-Term-Memory.md

### /clear 명령어와 메모리 연속성 유지
- **카테고리**: 도구 활용
- **설명**: `/clear` 명령어로 현재 대화 컨텍스트를 정리해도 Claude-Mem이 새로운 컨텍스트를 재주입하고 동일한 세션 추적을 계속한다.
- **출처**: Claude-Mem-Giving-Claude-Code-a-Long-Term-Memory.md

### 로컬 Web Viewer UI 활용
- **카테고리**: 도구 활용
- **설명**: localhost:37777에서 제공되는 Web Viewer UI를 통해 세션 탐색, 관찰 내용 확인, 요약 검사 등의 기능을 시각적으로 수행한다.
- **출처**: Claude-Mem-Giving-Claude-Code-a-Long-Term-Memory.md

---

## 문서 6: Claude-Sonnet-4.5-Full-Stack-App-Build-Test.md

### 단일 프롬프트 풀스택 개발
- **카테고리**: 프롬프트 엔지니어링
- **설명**: 복잡한 풀스택 애플리케이션을 작은 단계로 나누지 않고 전체 요구사항을 한 번에 제공하는 방식이다. AI가 약 3분 만에 프로덕션 수준의 애플리케이션을 구축할 수 있다.
- **출처**: Claude-Sonnet-4.5-Full-Stack-App-Build-Test.md

### 구조화된 프롬프트 템플릿 사용
- **카테고리**: 프롬프트 엔지니어링
- **설명**: 프롬프트를 Core Features, Technical Stack, UI Guidelines으로 명확히 구분하여 작성한다. 구조화하면 AI가 더 정확한 결과물을 생성한다.
- **출처**: Claude-Sonnet-4.5-Full-Stack-App-Build-Test.md

### 기술 스택 명시적 지정
- **카테고리**: 프롬프트 엔지니어링
- **설명**: Tailwind CSS와 Shad CN 등 원하는 기술 스택을 명시적으로 지정하여 AI가 기본 UI를 생성하는 것을 방지한다.
- **출처**: Claude-Sonnet-4.5-Full-Stack-App-Build-Test.md

### AI 신뢰 모드로 작업 가속화
- **카테고리**: 워크플로우
- **설명**: Claude Code의 명령 실행 확인 요청에 "예, 다시 묻지 마세요"를 선택하여 AI를 신뢰하고 자율적으로 작업하게 한다.
- **출처**: Claude-Sonnet-4.5-Full-Stack-App-Build-Test.md

### AI 프롬프트 최적화 기능 통합
- **카테고리**: 도구 활용
- **설명**: 애플리케이션 내에 "Optimize" 버튼을 구현하여 입력된 프롬프트를 AI API로 전송하고 구조화된 최적화 버전을 받아온다.
- **출처**: Claude-Sonnet-4.5-Full-Stack-App-Build-Test.md

### 프롬프트 라이브러리 구축
- **카테고리**: 생산성/마인드셋
- **설명**: AI 작업에 사용하는 프롬프트를 재사용하기 위해 라이브러리로 저장하고 관리한다. 효과적인 프롬프트를 축적하면 일관된 품질의 결과물을 얻을 수 있다.
- **출처**: Claude-Sonnet-4.5-Full-Stack-App-Build-Test.md

### 보일러플레이트 자동화
- **카테고리**: 워크플로우
- **설명**: 보일러플레이트 코드 작성에 AI를 활용하여 개발자가 더 높은 수준의 아키텍처 설계와 비즈니스 로직에 집중할 수 있게 한다.
- **출처**: Claude-Sonnet-4.5-Full-Stack-App-Build-Test.md

### 반복적 UI 개선 프롬프트
- **카테고리**: 프롬프트 엔지니어링
- **설명**: UI가 불만족스러울 때 현재 상태에 대한 명확한 피드백과 원하는 방향을 구체적으로 제시한다.
- **출처**: Claude-Sonnet-4.5-Full-Stack-App-Build-Test.md

### "형편없는 프롬프트 테스트"
- **카테고리**: 생산성/마인드셋
- **설명**: AI 모델의 지능을 평가하는 방법으로 "얼마나 형편없는 프롬프트를 주어도 놀라운 결과를 만들어내는가"를 기준으로 삼는다.
- **출처**: Claude-Sonnet-4.5-Full-Stack-App-Build-Test.md

### AI 생성 코드 검증 워크플로우
- **카테고리**: 코드 품질
- **설명**: AI가 생성한 코드는 항상 데이터베이스 저장, API 호출, 인증 등 핵심 기능이 정상 작동하는지 검증한다.
- **출처**: Claude-Sonnet-4.5-Full-Stack-App-Build-Test.md

### 서버 사이드 API 키 보호
- **카테고리**: 보안/테스트
- **설명**: AI API 호출은 반드시 서버 사이드에서 처리하여 API 키가 클라이언트에 노출되지 않도록 한다.
- **출처**: Claude-Sonnet-4.5-Full-Stack-App-Build-Test.md

### AI 보조 개발 워크플로우 적용
- **카테고리**: 워크플로우
- **설명**: 전통적인 워크플로우 대신 "요구사항 정의→프롬프트 작성→AI 생성(3분)→백엔드 설정(5분)→테스트 및 검증"의 새로운 워크플로우를 적용한다.
- **출처**: Claude-Sonnet-4.5-Full-Stack-App-Build-Test.md

### AI 생성 코드 아키텍처 리팩토링
- **카테고리**: TDD/개발 방법론
- **설명**: AI가 생성한 코드를 리팩토링하여 Hexagonal Architecture, Clean Architecture 등 더 나은 아키텍처 패턴을 적용한다.
- **출처**: Claude-Sonnet-4.5-Full-Stack-App-Build-Test.md

### AI 생성 코드 보안 체크리스트 적용
- **카테고리**: 보안/테스트
- **설명**: AI 생성 코드의 보안 취약점(SQL Injection, XSS, CSRF 등)을 체크리스트를 통해 검토한다.
- **출처**: Claude-Sonnet-4.5-Full-Stack-App-Build-Test.md

### AI 생성 코드에 테스트 추가
- **카테고리**: TDD/개발 방법론
- **설명**: AI가 생성한 코드에 단위 테스트, 통합 테스트, E2E 테스트를 추가하여 코드 품질을 보장한다.
- **출처**: Claude-Sonnet-4.5-Full-Stack-App-Build-Test.md

### AI 도구의 빠른 프로토타이핑 보조 활용
- **카테고리**: AI 에이전트/협업
- **설명**: 경험 많은 개발자는 AI를 "코드 작성자"가 아닌 "빠른 프로토타이핑 보조 도구"로 활용한다.
- **출처**: Claude-Sonnet-4.5-Full-Stack-App-Build-Test.md

### 팀 워크플로우에 AI 코드 리뷰 가이드라인 통합
- **카테고리**: AI 에이전트/협업
- **설명**: AI 도구를 팀 워크플로우에 통합하고, AI 생성 코드 리뷰 가이드라인을 수립한다.
- **출처**: Claude-Sonnet-4.5-Full-Stack-App-Build-Test.md

---

## 문서 7: Code Smarter, Not Harder- AI-Powered Dev Hacks for All.md

### 명확하고 구조화된 프롬프트 작성
- **카테고리**: 프롬프트 엔지니어링
- **설명**: AI와의 효과적인 의사소통을 위해 컨텍스트, 예시, 구체적인 지시사항을 포함한 구조화된 프롬프트를 작성한다.
- **출처**: Code Smarter, Not Harder.md

### Zero-Shot, Few-Shot, Chain-of-Thought 프롬프팅
- **카테고리**: 프롬프트 엔지니어링
- **설명**: 상황에 따라 다른 프롬프팅 기법을 선택한다. Zero-Shot은 예시 없이 직접 질문, Few-Shot은 예시를 제공, Chain-of-Thought는 단계별 추론을 요청한다.
- **출처**: Code Smarter, Not Harder.md

### XML 태그를 활용한 프롬프트 구조화
- **카테고리**: 프롬프트 엔지니어링
- **설명**: XML 태그를 사용하여 정보를 구조화하고, 복잡한 문제를 관리 가능한 부분으로 분해(Task Decomposition)한다.
- **출처**: Code Smarter, Not Harder.md

### 효과적인 프롬프트 라이브러리 구축
- **카테고리**: 생산성/마인드셋
- **설명**: 효과적으로 작동한 프롬프트들을 Claude Project 등에 저장하여 재사용하고 적응시킨다.
- **출처**: Code Smarter, Not Harder.md

### 음성 인식을 활용한 프롬프트 입력
- **카테고리**: 생산성/마인드셋
- **설명**: MacOS 내장 음성 인식(dictation) 기능을 활용하여 복잡하고 긴 프롬프트를 빠르게 입력한다.
- **출처**: Code Smarter, Not Harder.md

### AI 유형별 전문 분야 매칭
- **카테고리**: 도구 활용
- **설명**: 각 AI 도구의 강점에 맞게 작업을 배분한다. Academic 유형은 사실/연구/분석, Creative 유형은 글쓰기/브레인스토밍, Engineer 유형은 코딩/기술 문서에 활용한다.
- **출처**: Code Smarter, Not Harder.md

### 개념 분해를 통한 학습 보조
- **카테고리**: 워크플로우
- **설명**: 복잡한 프로그래밍 개념을 AI에게 단순화하여 설명해달라고 요청한다.
- **출처**: Code Smarter, Not Harder.md

### 맞춤형 학습 경로 생성
- **카테고리**: 워크플로우
- **설명**: AI에게 특정 기술 학습을 위한 개인화된 학습 경로를 요청한다.
- **출처**: Code Smarter, Not Harder.md

### AI를 활용한 코드 이해 전략
- **카테고리**: 코드 품질
- **설명**: 낯선 코드를 AI에 붙여넣고 목적, 디자인 패턴, 핵심 의존성, 잠재적 부작용 등을 질문한다.
- **출처**: Code Smarter, Not Harder.md

### 레거시 코드 분석 및 현대화 제안
- **카테고리**: 코드 품질
- **설명**: 레거시 코드에 대해 역사적 맥락을 질문하고 현대적 방식으로 리팩토링하는 방법을 요청한다.
- **출처**: Code Smarter, Not Harder.md

### 자동 문서 생성
- **카테고리**: 도구 활용
- **설명**: AI를 활용하여 클래스/함수/메서드 문서, 복잡한 알고리즘 설명, 사용 예제, API 엔드포인트 문서를 자동 생성한다.
- **출처**: Code Smarter, Not Harder.md

### Claude Projects를 활용한 README 생성기
- **카테고리**: 도구 활용
- **설명**: Claude Projects에 README 생성 전문 프롬프트 템플릿을 저장하여 활용한다.
- **출처**: Code Smarter, Not Harder.md

### 워크플로우 자동화 도구 개발
- **카테고리**: 도구 활용
- **설명**: AI를 활용하여 CLI 도구, IDE 플러그인, 브라우저 확장, 리포팅 도구 등 개발 워크플로우를 간소화하는 도구를 개발한다.
- **출처**: Code Smarter, Not Harder.md

### 데이터 변환 및 분석
- **카테고리**: 도구 활용
- **설명**: AI를 활용하여 JSON, CSV, XML 등 형식 간 데이터 변환, JSON 객체를 Java Record로 변환, 데이터 유효성 검사 규칙 작성을 수행한다.
- **출처**: Code Smarter, Not Harder.md

### 현실적인 테스트 데이터 생성
- **카테고리**: 보안/테스트
- **설명**: AI에게 스키마 요구사항에 맞는 현실적인 테스트 데이터 생성을 요청한다. 다양한 사용자 프로필, 엣지 케이스를 포함한다.
- **출처**: Code Smarter, Not Harder.md

### 데이터베이스 쿼리 및 스키마 작업
- **카테고리**: 도구 활용
- **설명**: AI를 활용하여 복잡한 SQL 쿼리 작성, 데이터베이스 스키마 설계, 기존 쿼리 성능 최적화, SQL 방언 간 변환을 수행한다.
- **출처**: Code Smarter, Not Harder.md

### 로컬 LLM 실행
- **카테고리**: 도구 활용
- **설명**: Ollama, Open WebUI, Docker Model Runner 등을 활용하여 로컬에서 LLM을 실행한다. 개인정보 보호와 보안 면에서 이점이 있다.
- **출처**: Code Smarter, Not Harder.md

### AI 코딩 도구에 가이드라인 제공
- **카테고리**: AI 에이전트/협업
- **설명**: AI 코딩 도구에 guidelines.md 같은 가이드라인 파일을 제공하여 개인/팀의 코딩 스타일과 일치하는 결과물을 얻는다.
- **출처**: Code Smarter, Not Harder.md

### AI를 주니어 개발자로 취급하는 파일럿 마인드셋
- **카테고리**: AI 에이전트/협업
- **설명**: "You are the Pilot, Not a passenger" - AI를 주니어 프로그래머로 간주하고 파일럿으로서 주도한다.
- **출처**: Code Smarter, Not Harder.md

### AI 생성 코드의 비판적 검토
- **카테고리**: 코드 품질
- **설명**: AI가 잘못되거나 비효율적인 코드를 생성할 수 있음을 인지하고, 항상 AI 생성 코드를 검토하고 이해한다.
- **출처**: Code Smarter, Not Harder.md

### 점진적 AI 워크플로우 통합
- **카테고리**: 워크플로우
- **설명**: AI 도구를 기존 워크플로우에 점진적으로 통합한다. 문서화와 코드 리뷰 작업부터 시작하여 점차 확대한다.
- **출처**: Code Smarter, Not Harder.md

---

## 문서 8: Code-like-a-surgeon.md

### 외과의사 모델 (Surgeon Model)
- **카테고리**: AI 에이전트/협업
- **설명**: AI를 개발자의 지원 시스템으로 활용하여 부차적 작업(준비 작업, 문서화 등)을 위임하고, 개발자는 핵심 창의적 작업에만 집중하는 협업 모델이다.
- **출처**: Code-like-a-surgeon.md

### 코드베이스 가이드 사전 작성
- **카테고리**: 워크플로우
- **설명**: 큰 작업을 시작하기 전에 AI 에이전트에게 관련 코드베이스 영역에 대한 가이드를 작성하도록 지시한다.
- **출처**: Code-like-a-surgeon.md

### 스파이크 구현 위임 (Spike Implementation)
- **카테고리**: AI 에이전트/협업
- **설명**: 큰 변경사항에 대한 초기 시도(스파이크)를 AI가 먼저 수행하도록 위임한다. 결과물을 직접 사용하지 않더라도 방향성을 설정하는 스케치로 활용한다.
- **출처**: Code-like-a-surgeon.md

### TypeScript 오류 수정 자동화
- **카테고리**: 코드 품질
- **설명**: 명확한 스펙이 있는 TypeScript 오류나 버그를 AI에게 위임하여 수정한다.
- **출처**: Code-like-a-surgeon.md

### 비동기 문서화 작업
- **카테고리**: 생산성/마인드셋
- **설명**: 개발한 내용에 대한 문서를 AI에게 작성하도록 지시하여, 개발자가 코드 작성에 집중하면서도 필요한 문서화를 병행할 수 있게 한다.
- **출처**: Code-like-a-surgeon.md

### 비활성 시간 백그라운드 작업
- **카테고리**: 워크플로우
- **설명**: 점심 시간이나 밤사이 같은 비활성 시간에 AI 에이전트가 비동기적으로 백그라운드에서 작업을 수행하도록 한다.
- **출처**: Code-like-a-surgeon.md

### 자율성 슬라이더 (Autonomy Slider)
- **카테고리**: 생산성/마인드셋
- **설명**: 작업의 성격에 따라 AI 자율성 수준을 조절하는 개념이다. 주요 작업에서는 세심한 주의로, 부차적 작업에서는 느슨하게 에이전트가 무감독으로 작업하도록 허용한다.
- **출처**: Code-like-a-surgeon.md

### 주요/부차적 작업 분리 전략
- **카테고리**: 워크플로우
- **설명**: 개발 작업을 주요 작업(핵심 창의적 작업)과 부차적 작업(grunt work)으로 명확히 구분하고, 각각에 다른 AI 활용 전략을 적용한다.
- **출처**: Code-like-a-surgeon.md

### 24/7 AI 에이전트 가용성 활용
- **카테고리**: AI 에이전트/협업
- **설명**: AI 에이전트는 인간과 달리 24시간 grunt work를 수행할 수 있다. 인간 인턴에게는 요구하기 어려운 작업을 자유롭게 지시할 수 있다.
- **출처**: Code-like-a-surgeon.md

### 대규모 코드베이스 온보딩 가속화
- **카테고리**: 생산성/마인드셋
- **설명**: AI 코딩 도구를 적극 활용하는 환경에서 대규모 코드베이스에 새로 합류한 개발자가 심각한 생산성 향상을 경험할 수 있다.
- **출처**: Code-like-a-surgeon.md

---

## 문서 9: Codex 개발자와의 대담.md

### 병렬 에이전트 위임
- **카테고리**: AI 에이전트/협업
- **설명**: 여러 에이전트를 동시에 시작하여 병렬로 작업을 위임하는 방식. 까다로운 버그처럼 어려운 작업에도 다수의 에이전트를 동시에 투입한다.
- **출처**: Codex 개발자와의 대담.md

### 풍요의 사고방식 (Abundance Mindset)
- **카테고리**: 생산성/마인드셋
- **설명**: 작업이 작동할지 깊이 생각하지 않고 많은 작업을 마구 요청하는 접근법. 성공하면 가치가 있고 실패해도 손해가 적다는 사고방식.
- **출처**: Codex 개발자와의 대담.md

### 긴급 장애 처리(On Call Triage) 자동화
- **카테고리**: 워크플로우
- **설명**: 버그의 정확한 원인을 모르더라도 에이전트에게 먼저 해결을 요청. 에이전트가 바로 수정하거나, 초안을 제공하거나, 버그 위치를 찾아줄 수 있다.
- **출처**: Codex 개발자와의 대담.md

### 아침 태스크 배치 전략
- **카테고리**: 워크플로우
- **설명**: 매일 아침 하고 싶은 일을 생각한 후 휴대폰으로 여러 작업을 에이전트에게 요청해두고, 책상에 도착해서 완료된 결과 중 사용할 것을 선택하는 비동기 작업 방식.
- **출처**: Codex 개발자와의 대담.md

### Ask 모드와 Code 모드의 전략적 구분
- **카테고리**: 프롬프트 엔지니어링
- **설명**: 탐색적이고 불명확한 작업에는 Ask 모드를 사용하고, 구현이 명확한 작업에는 Code 모드를 사용한다.
- **출처**: Codex 개발자와의 대담.md

### 문서화 작업 자동화
- **카테고리**: 코드 품질
- **설명**: "문서 추가할 곳 제안해 줘"와 같은 프롬프트로 에이전트에게 코드베이스에서 문서화가 필요한 부분을 찾아내고 문서화 작업을 수행하도록 위임한다.
- **출처**: Codex 개발자와의 대담.md

### 자동 버그 탐색 및 수정 제안
- **카테고리**: 보안/테스트
- **설명**: "버그 좀 찾아서 그 버그를 수정하거나 개선할 작업들을 제안해 줘"와 같이 에이전트에게 코드베이스 전체를 분석하여 버그를 발견하고 수정 작업을 제안하도록 요청한다.
- **출처**: Codex 개발자와의 대담.md

### 소셜 코딩 (Social Coding)
- **카테고리**: AI 에이전트/협업
- **설명**: 여러 사람이 화상 통화로 함께 화면을 공유하면서 각자 에이전트들을 동시에 여러 기능과 버그 수정에 투입한다.
- **출처**: Codex 개발자와의 대담.md

### 병합 가능한 작은 PR 분할
- **카테고리**: 코드 품질
- **설명**: 큰 리팩터링 작업을 병합 충돌 없이 각기 독립적으로 컴파일되는 여러 개의 작은 PR로 나누어 처리하도록 에이전트에게 요청한다.
- **출처**: Codex 개발자와의 대담.md

### 테스트 실행을 통한 자동 검증
- **카테고리**: 보안/테스트
- **설명**: 에이전트가 코드 변경 후 테스트를 실행하여 변경 사항을 자동으로 검증한다. 테스트 결과와 함께 출처 인용 정보를 제공하여 투명성을 확보한다.
- **출처**: Codex 개발자와의 대담.md

### 50줄 이하의 작은 변경 단위 유지
- **카테고리**: 코드 품질
- **설명**: 1000줄짜리 대형 PR 대신 50줄짜리 변경 사항 20개를 검토하는 것이 더 효율적. 에이전트가 생성하는 코드를 작고 검토 가능한 단위로 유지한다.
- **출처**: Codex 개발자와의 대담.md

### 에이전트 환경 설정 최적화
- **카테고리**: 도구 활용
- **설명**: 에이전트가 효과적으로 작업할 수 있도록 환경을 설정하는 데 시간 투자. 에이전트 팀의 생산성을 높이기 위한 관리자적 관점에서 필요한 도구와 테스트 환경을 구성한다.
- **출처**: Codex 개발자와의 대담.md

### 위임과 실시간 페어링의 통합
- **카테고리**: AI 에이전트/협업
- **설명**: 비동기적으로 작업을 위임하는 것과 실시간으로 협업하는 것을 하나의 경험으로 통합한다.
- **출처**: Codex 개발자와의 대담.md

### 코드베이스 스타일 자동 적응
- **카테고리**: 코드 품질
- **설명**: 에이전트가 자체적으로 옳다고 생각하는 스타일이 아닌 실제 코드베이스의 스타일을 따르도록 훈련한다.
- **출처**: Codex 개발자와의 대담.md

### 인터넷 차단 보안 모드
- **카테고리**: 보안/테스트
- **설명**: 환경 설정 시에만 네트워크 접근을 허용하고 에이전트 실행 시에는 인터넷을 차단하여 정보 유출 위험을 방지한다.
- **출처**: Codex 개발자와의 대담.md

---

## 문서 10: Coding Guidelines for Your AI Agents.md

### AI 에이전트용 코딩 가이드라인 파일 생성
- **카테고리**: AI 에이전트/협업
- **설명**: `.junie/guidelines.md` 파일에 코딩 스타일, 모범 사례, 일반 선호도를 명시하여 AI 에이전트가 코드 생성 시 자동으로 따르도록 한다.
- **출처**: Coding Guidelines for Your AI Agents.md

### 구체적인 가이드라인을 포함한 프롬프트 작성
- **카테고리**: 프롬프트 엔지니어링
- **설명**: AI에게 코드 생성을 요청할 때 "Use constructor-based dependency injection" 등 구체적인 가이드라인을 명시한다.
- **출처**: Coding Guidelines for Your AI Agents.md

### 레거시 프로젝트용 가이드라인 자동 추출
- **카테고리**: 워크플로우
- **설명**: 기존 코드베이스가 있는 프로젝트에서 AI에게 현재 코드베이스의 코딩 컨벤션, 코드 구조, 테스트 접근법을 분석하여 guidelines.md 파일을 생성하도록 요청한다.
- **출처**: Coding Guidelines for Your AI Agents.md

### 기술별 가이드라인 카탈로그 활용
- **카테고리**: AI 에이전트/협업
- **설명**: Java, Spring Boot, Docker 등 각 기술별로 정리된 가이드라인 카탈로그(junie-guidelines 저장소)를 활용하여 AI 에이전트에게 제공한다.
- **출처**: Coding Guidelines for Your AI Agents.md

### 그린필드 프로젝트용 표준 가이드라인 적용
- **카테고리**: 워크플로우
- **설명**: 새로운 프로젝트를 시작할 때 가이드라인 카탈로그에서 해당 기술 스택의 가이드라인을 가져와 설정한다.
- **출처**: Coding Guidelines for Your AI Agents.md

### 가이드라인의 점진적 개선
- **카테고리**: 코드 품질
- **설명**: AI가 생성한 guidelines.md 파일을 기반으로 팀의 필요에 맞게 추가 가이드라인을 넣거나 기존 항목을 수정한다.
- **출처**: Coding Guidelines for Your AI Agents.md

### AI 에이전트에게 명확한 의도 전달
- **카테고리**: 프롬프트 엔지니어링
- **설명**: AI 에이전트가 가정을 하지 않도록 의도를 매우 명확하게 전달해야 한다.
- **출처**: Coding Guidelines for Your AI Agents.md

### 안티패턴 방지 가이드라인 명시
- **카테고리**: 코드 품질
- **설명**: 가이드라인에 "Avoid using Optional in request bodies", "Don't use field injection" 등 피해야 할 안티패턴을 명시적으로 포함한다.
- **출처**: Coding Guidelines for Your AI Agents.md

---

## 카테고리별 기법 수 요약

| 카테고리 | 기법 수 |
|----------|---------|
| 프롬프트 엔지니어링 | 23 |
| 워크플로우 | 26 |
| AI 에이전트/협업 | 30 |
| 도구 활용 | 26 |
| 코드 품질 | 15 |
| 생산성/마인드셋 | 13 |
| 보안/테스트 | 10 |
| TDD/개발 방법론 | 2 |
| AI-Ops | 4 |
| **총계** | **129** |

---

## 핵심 테마 요약

### 1. PDA (Progressive Disclosure Architecture)
- Reference Files와 Lazy Loading으로 토큰 78-85% 절감
- 컨텍스트 오버플로우 방지
- 스크립트 분리로 기계적 작업 제로 토큰 비용 달성

### 2. 슬래시 명령어 시스템
- 반복 작업 단일 명령어 자동화
- !/$/@ 접두사로 컨텍스트 주입
- 팀 표준 내장 및 암묵지 형식지 변환

### 3. 전문화된 서브에이전트 아키텍처
- Plan/Explore/Implement 역할 분리
- 컨텍스트 오염 방지
- 동적 모델 선택으로 비용 최적화

### 4. LSP 통합
- IDE 수준의 코드 인텔리전스 CLI에서 사용
- Go-to-Definition, Find References, Hover 등
- 대규모 코드베이스 탐색 가속화

### 5. 세션 간 메모리 지속
- Claude-Mem 플러그인으로 영구 메모리 구현
- 자동 관찰 캡처 및 학습 추출
- 하이브리드 검색 (FTS5 + 시맨틱 벡터)

### 6. 외과의사 모델
- 주요/부차적 작업 분리 전략
- 자율성 슬라이더 개념
- 24/7 AI 에이전트 가용성 활용

### 7. 병렬 에이전트 전략
- 풍요의 사고방식 (Abundance Mindset)
- 아침 태스크 배치 전략
- 소셜 코딩 패턴
