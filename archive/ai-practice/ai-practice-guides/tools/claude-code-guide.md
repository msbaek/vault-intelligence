# Claude Code 완전 가이드

**생성일**: 2026-01-04
**버전**: Claude Code v1.x
**목적**: Claude Code의 모든 기능을 효과적으로 활용하는 방법

---

## 필수 설정

### 1. CLAUDE.md 파일

프로젝트 루트에 `CLAUDE.md` 파일을 생성하여 Claude Code에게 프로젝트 컨텍스트를 제공합니다.

```markdown
# 프로젝트 가이드

## 개요
[프로젝트 설명]

## 기술 스택
- 언어: Java 21
- 프레임워크: Spring Boot 3.2
- 빌드: Gradle
- 테스트: JUnit 5, Mockito

## 아키텍처
- Clean Architecture / Hexagonal
- 레이어: Domain → Application → Infrastructure

## 코딩 규칙
- 함수는 20줄 이내
- 단일 책임 원칙 준수
- 테스트 커버리지 80% 이상
- 모든 public 메서드에 Javadoc

## 명령어
- `./gradlew test` - 테스트 실행
- `./gradlew build` - 빌드
- `./gradlew spotlessCheck` - 코드 스타일 검사

## 제약사항
- 기존 테스트를 수정하지 말 것
- 새 의존성 추가 전 승인 필요
- 프로덕션 DB 직접 접근 금지
```

### 2. AGENTS.md (서브에이전트 정의)

```yaml
# .claude/agents/AGENTS.md

code-reviewer:
  name: "Code Reviewer"
  description: "코드 품질 및 보안 검토 전문가"
  model: haiku  # 빠른 응답용
  tools:
    - Read
    - Grep
  system_prompt: |
    당신은 시니어 코드 리뷰어입니다.
    다음 관점에서 코드를 검토합니다:
    - 보안 취약점 (OWASP Top 10)
    - 성능 이슈
    - 코드 품질 (SOLID, Clean Code)
    - 테스트 커버리지

test-writer:
  name: "Test Writer"
  description: "TDD 전문가"
  tools:
    - Read
    - Write
    - Bash
  system_prompt: |
    당신은 TDD 전문가입니다.
    - 테스트 먼저 작성
    - 엣지 케이스 포함
    - Given-When-Then 형식 사용
```

### 3. Skills 설정

```markdown
# .claude/skills/commit.md

---
description: 커밋 메시지 생성 및 커밋 실행
---

1. `git status`로 변경 파일 확인
2. `git diff`로 변경 내용 분석
3. Conventional Commits 형식으로 메시지 생성
4. 사용자 확인 후 커밋 실행

메시지 형식:
- feat: 새 기능
- fix: 버그 수정
- refactor: 리팩토링
- docs: 문서 변경
- test: 테스트 추가/수정
```

### 4. Hooks 설정

```json
// .claude/settings.json
{
  "hooks": {
    "pre-commit": [
      "./gradlew test",
      "./gradlew spotlessCheck"
    ],
    "post-file-edit": [
      "echo '파일이 수정되었습니다'"
    ]
  }
}
```

---

## 핵심 명령어 10선

### 1. 초기화
```bash
claude /init
```
- CLAUDE.md 자동 생성
- 프로젝트 구조 분석
- 기본 설정 추천

### 2. 계획 모드
```bash
claude /plan
# 또는 대화 중
/plan
```
- 복잡한 작업 전 계획 수립
- 구현 전략 논의
- 파일 변경 없이 분석

### 3. 커밋
```bash
claude /commit
```
- 변경사항 분석
- 커밋 메시지 자동 생성
- Conventional Commits 형식

### 4. PR 리뷰
```bash
claude /review-pr 123
# 또는
claude /review-pr https://github.com/owner/repo/pull/123
```

### 5. 세션 이어가기
```bash
# 마지막 세션 이어서
claude --continue
# 또는
claude -c

# 특정 세션 선택
claude --resume
# 또는
claude -r
```

### 6. 도움말
```bash
claude /help
```

### 7. 히스토리 정리
```bash
claude /clear
```

### 8. 비용 확인
```bash
claude /cost
```

### 9. 모델 변경
```bash
claude /model opus
claude /model sonnet
claude /model haiku
```

### 10. 디버그 모드
```bash
claude --verbose
```

---

## 서브에이전트 활용법

### 언제 서브에이전트를 사용하나?

1. **전문 영역 분리** - 코드 리뷰, 테스트 작성, 문서화
2. **병렬 처리** - 여러 파일 동시 분석
3. **일관성 유지** - 동일한 패턴으로 반복 작업

### 서브에이전트 호출 방법

**자동 호출 (PROACTIVELY):**
```yaml
code-reviewer:
  description: "PR 생성 시 자동으로 코드 리뷰 수행"
  when: "Use PROACTIVELY when PR is created"
```

**수동 호출:**
```markdown
@code-reviewer 이 PR을 리뷰해줘
```

### 서브에이전트 예시들

**Security Scanner:**
```yaml
security-scanner:
  description: "보안 취약점 스캐너"
  tools: [Read, Grep]
  system_prompt: |
    OWASP Top 10 기준으로 코드를 스캔합니다:
    1. Injection
    2. Broken Authentication
    3. XSS
    ...
```

**Documentation Writer:**
```yaml
doc-writer:
  description: "문서 작성 전문가"
  model: haiku
  tools: [Read, Write]
  system_prompt: |
    코드를 분석하고 문서를 생성합니다:
    - README.md
    - API 문서
    - 아키텍처 문서
```

---

## MCP 서버 통합

### MCP란?
Model Context Protocol - AI가 외부 도구 및 서비스와 상호작용할 수 있게 하는 프로토콜

### 필수 MCP 서버

```json
// .claude/mcp_config.json
{
  "servers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem"]
    },
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_TOKEN": "${GITHUB_TOKEN}"
      }
    },
    "fetch": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-fetch"]
    }
  }
}
```

### 추천 MCP 서버

| MCP 서버 | 용도 |
|----------|------|
| filesystem | 파일 시스템 접근 |
| github | GitHub 연동 |
| fetch | 웹 콘텐츠 가져오기 |
| postgres | DB 쿼리 |
| playwright | 브라우저 자동화 |
| slack | Slack 연동 |

### MCP 토큰 사용량 주의

> ⚠️ MCP 연결만으로도 토큰을 소비합니다.
> 예: Notion MCP ≈ 30,000 토큰 (컨텍스트의 15%)

**권장사항:**
- 필요한 MCP만 선별 연결
- 큰 컨텍스트가 필요 없으면 분리

---

## 고급 팁

### 1. Git Worktrees 활용

여러 브랜치를 동시에 작업:
```bash
# 워크트리 생성
git worktree add ../feature-auth feature/authentication

# 각 워크트리에서 Claude Code 실행
cd ../feature-auth
claude
```

### 2. Checkpoints 활용

```markdown
현재 상태를 체크포인트로 저장해줘.
이후 문제가 생기면 이 지점으로 롤백할 거야.
```

### 3. 컨텍스트 최적화

**컨텍스트가 커질 때:**
```markdown
현재 대화를 요약하고 새 세션으로 시작하자.
핵심 정보만 유지해줘:
- 현재 작업 중인 기능
- 결정된 아키텍처
- 남은 TODO
```

### 4. 롤백 전략

```markdown
AI가 잘못된 방향으로 갔을 때:
1. git stash 또는 git checkout -- .
2. /clear로 컨텍스트 정리
3. 다른 접근 방식으로 재시작
```

### 5. 비용 최적화

| 작업 | 추천 모델 |
|------|-----------|
| 계획 수립 | Opus |
| 코드 구현 | Sonnet |
| 빠른 리팩토링 | Haiku |
| 문서화 | Haiku |
| 복잡한 디버깅 | Opus |

---

## 트러블슈팅

### "컨텍스트가 너무 큽니다"
```bash
# 새 세션 시작
claude /clear

# 필요한 컨텍스트만 다시 제공
```

### "MCP 연결 실패"
```bash
# MCP 서버 상태 확인
npx @modelcontextprotocol/inspector

# 환경 변수 확인
echo $GITHUB_TOKEN
```

### "API 속도 제한"
```bash
# 잠시 대기 후 재시도
# 또는 다른 모델 사용
claude /model haiku
```

### "예상치 못한 파일 수정"
```bash
# 변경사항 확인
git diff

# 롤백
git checkout -- .

# 더 구체적인 지시와 함께 재시도
```

---

## 일일 워크플로우 예시

```bash
# 1. 어제 작업 이어서 시작
claude -c

# 2. 오늘 할 일 분석
"오늘 할 이슈들을 분석해줘"

# 3. 계획 수립
/plan

# 4. 구현 (TDD 사이클)
"이 테스트가 통과하도록 구현해줘"

# 5. 중간 커밋
/commit

# 6. 리뷰
"오늘 작업한 코드를 리뷰해줘"

# 7. PR 생성
"PR 설명을 작성해줘"
```

---

## 참고 자료

- [Claude Code 공식 문서](https://docs.anthropic.com/en/docs/claude-code)
- [MCP 서버 목록](https://github.com/anthropics/mcp-servers)
- [Claude Code GitHub](https://github.com/anthropics/claude-code)
- [서브에이전트 가이드](https://docs.anthropic.com/en/docs/claude-code/sub-agents)
