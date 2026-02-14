# AI Practice 기법 수집 요약

## 개요

vault-intelligence 시스템을 활용하여 Obsidian vault의 AI 관련 문서에서 실용적인 기법들을 체계적으로 수집한 프로젝트입니다.

| 항목 | 내용 |
|------|------|
| 수집 기간 | 2025-01-03 ~ 2026-01-04 |
| 대상 문서 | 286개 (~/DocumentsLocal/msbaek_vault/003-RESOURCES/AI) |
| 처리 방식 | 10개 문서 단위 배치 처리 (29 배치) |
| 추출 기법 | 1,745개 → 중복 제거 후 **1,403개** |

---

## 카테고리별 분포

```
AI-Assisted Development   ██████████████████████████████████████████████████ 574 (40.9%)
Prompt Engineering        ███████████████████████ 272 (19.4%)
Agent & Workflow          ████████████████ 187 (13.3%)
Tools & Integration       ███████████████ 179 (12.8%)
Quality & Security        ██████████ 122 (8.7%)
Learning & Mindset        ██████ 69 (4.9%)
```

---

## 카테고리별 핵심 기법

### 1. AI-Assisted Development (574개)

**주요 기법**:
- **스펙 주도 개발 (Spec-Driven Development)**: AI가 명확한 명세서를 기반으로 작업하도록 하여 5배 생산성 향상
- **모델별 역할 분리**: Plan Mode에 Opus, Execution Mode에 Sonnet 활용
- **계획 우선 접근법**: SPARC 방법론, Plan-First Execution
- **세션 연속성 관리**: `-c`, `-r` 플래그로 컨텍스트 유지

### 2. Prompt Engineering (272개)

**주요 기법**:
- **출력 형식 명시**: `<format>` 태그로 원하는 형식 지정
- **단계적 사고 유도**: "step-by-step" 접근법
- **역할 부여**: 전문가 페르소나 설정
- **예제 제공**: Few-shot 프롬프팅

### 3. Agent & Workflow (187개)

**주요 기법**:
- **MCP (Model Context Protocol)**: 외부 도구 통합
- **서브에이전트 오케스트레이션**: 병렬 처리 및 역할 분리
- **Human-in-the-Loop**: 인간 검토 지점 설정
- **지식 그래프 활용**: 문서 간 관계 분석

### 4. Tools & Integration (179개)

**주요 기법**:
- **Claude Code CLI**: 터미널 기반 개발 워크플로우
- **Skills 시스템**: 도메인 특화 확장
- **Hooks**: 이벤트 기반 자동화
- **Git Worktrees**: 병렬 브랜치 작업

### 5. Quality & Security (122개)

**주요 기법**:
- **TDD + AI 통합**: 테스트로 AI 결과물 검증
- **다층 검증**: 코드 리뷰 + 자동화 테스트
- **OWASP Top 10 인식**: 보안 취약점 예방
- **Pre-commit Hooks**: 커밋 전 품질 게이트

### 6. Learning & Mindset (69개)

**주요 기법**:
- **Renaissance Developer**: 다분야 역량 개발
- **AI를 멘토로 활용**: 소크라테스식 대화
- **페어 프로그래밍**: 180일 AI 협업 학습
- **검증 마인드셋**: assert-first 접근법

---

## 핵심 인사이트

### Specification-Translation-Verification 패러다임
```
Specification (인간) → Translation (AI) → Verification (인간)
```
- **AI가 대체**: Translation (코드 구현)
- **인간이 담당**: Specification (문제 정의), Verification (검증)

### 생산성 향상 지표
- Spec-Driven Development: **5배** 생산성 향상
- Context Engineering: 토큰 **80-95%** 절감
- Claude Code Skills: 개발 시간 **60%** 단축

---

## 상세 결과

배치별 상세 결과와 전체 기법 목록은 아래 경로에서 확인할 수 있습니다:

- **마스터 문서**: [archive/ai-practice/ai-practice-consolidated/AI-Practice-Master.md](../archive/ai-practice/ai-practice-consolidated/AI-Practice-Master.md)
- **카테고리별 문서**: [archive/ai-practice/ai-practice-consolidated/categories/](../archive/ai-practice/ai-practice-consolidated/categories/)
- **배치별 결과**: [archive/ai-practice/ai-practice-results/](../archive/ai-practice/ai-practice-results/)

---

*이 문서는 vault-intelligence의 실제 활용 사례로, 대규모 문서 분석 및 지식 추출 워크플로우를 보여줍니다.*
