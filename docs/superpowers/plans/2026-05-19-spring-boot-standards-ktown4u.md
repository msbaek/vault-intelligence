# Spring Boot Project Standards (ktown4u edition) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** ktown4u 사내 Java 21 + Spring Boot 3.x 컨벤션을 단일 Obsidian markdown 가이드로 정리해 Claude Code 등 AI agent에게 제공할 single source of truth를 만든다. S1(Dan Vega Junie gist, 외부 best practice)과 S3(`kt4u/system-prompts/claude/CLAUDE.md` 25k, 사내 실제 컨벤션)를 통합하되 충돌 시 사내 규약(S3)을 우선한다.

**Architecture:**
- 단일 markdown 문서 `spring-boot-project-standards-ktown4u.md`를 `000-SLIPBOX/MINE/DOCS/`에 저장 (기존 3문서와 동일 위치 · frontmatter 컨벤션).
- 섹션별로 "S1 권고 + S3 사내 표준"을 대조하고 코드 예시(Good/Bad)와 위반 시 anti-pattern을 함께 제시.
- 후속 활용(skill·sub-agent·hook 변환) 검토는 별도 backlog 항목으로 남김 — 본 plan은 vault 문서까지만.

**Tech Stack:** Obsidian markdown · frontmatter (id/aliases/tags/author/created_at/source/related) · wikilinks · vault-intelligence sub-agent (`obsidian-forward-related-injector`) · git (`/commit` skill, Korean-safe).

**산출물 경로**
- 가이드 문서: `~/DocumentsLocal/msbaek_vault/000-SLIPBOX/MINE/DOCS/spring-boot-project-standards-ktown4u.md`
- 갱신 문서: `~/DocumentsLocal/msbaek_vault/000-SLIPBOX/MINE/DOCS/ai-agent-guides-backlog.md` (☐ → ✅ + 새 후속 활용 backlog)

**Failure Conditions** (이 중 하나라도 발생하면 plan 실패로 간주)
- S3 사내 규약과 S1 외부 권고가 충돌할 때 S1을 우선시한 채 작성.
- "더 자세한 내용은 S1 참고" 같은 placeholder 사용 — S1/S3 핵심은 모두 본문에 흡수해야 함.
- frontmatter `created_at` quoting 누락, 또는 키 순서가 기존 3문서와 불일치.
- 12개 H2 섹션 중 어느 하나에 코드 예시가 빠짐.
- Related Notes 5개 자동 추가 누락 (sub-agent 위임 안 함).
- backlog 갱신 누락 (Top 1 ✅ 표시 + 후속 활용 backlog 항목 추가).

---

## File Structure

**문서 outline (H2 12개)**

| §   | 제목                                                  | 핵심 source | 약 길이 |
| --- | ----------------------------------------------------- | ----------- | ------- |
| 1   | 프로젝트 기반 설정 (Java 21 LTS · Spring Boot 3.x)    | S1          | 短       |
| 2   | 패키지 구조 — package-by-feature                      | S1 + S3     | 中      |
| 3   | Java 코드 스타일 16종 (Query/Command·Yoda·Null Object) | S3          | 長      |
| 4   | @Service 클래스 — 유즈케이스 동사 + Request/Response  | S3          | 中      |
| 5   | Constructor Injection + @ConfigurationProperties      | S1          | 短      |
| 6   | HTTP Client — RestClient (RestTemplate 제거)          | S1          | 短      |
| 7   | Data Carriers — Records vs Class + Lombok 조합        | S1 + S3     | 中      |
| 8   | 데이터베이스 / JPA — Aggregate Root만 Repository      | S1 + S3     | 中      |
| 9   | Error Handling + Silent vs Fail Fast 결정 매트릭스    | S1 + S3     | 中      |
| 10  | Test Strategy — JUnit 5 · Mockito · Testcontainers    | S1          | 中      |
| 11  | DIP & 패키지 간 통신 — 인터페이스 소유권 + 도메인 이벤트 | S3          | 中      |
| 12  | 자주 위반되는 룰 & Blame Command 연결                 | S3          | 短      |

각 섹션 = "S1/S3 출처 명시 → 핵심 원칙 → Good 예시 → Bad 예시 (anti-pattern) → ktown4u 맥락 (해당 시)".

---

## Task 1: Spec 입력 자료 정리

**Files:**
- Read: `/Users/msbaek/git/kt4u/system-prompts/claude/CLAUDE.md` (25k, 745 lines)
- Read: cached S1 — 이전 세션의 Dan Vega gist 내용 (이미 transcript에 fetch됨)
- Scratch (선택): `/tmp/spring-standards-spec.md` — 섹션별 인용 정리용 임시 파일

- [ ] **Step 1: S3 CLAUDE.md 재읽기 + 12 섹션별로 인용할 블록 식별**

```
Read /Users/msbaek/git/kt4u/system-prompts/claude/CLAUDE.md (전문)
12개 H2 섹션 각각에 매칭되는 S3의 line range를 기록:
- §2 (패키지 구조) ← S3 line 524-744
- §3 (코드 스타일 16종) ← S3 line 8-478
- §4 (@Service) ← S3 line 480-516
- §8 (DB) ← S3 line 518-523
- §9 (Silent vs Fail Fast) ← S3 line 93-148
- §11 (DIP & 패키지 통신) ← S3 line 608-744
- §12 (Blame Command 연결) ← S3 commands/*.md
```

- [ ] **Step 2: S1 (Dan Vega gist) 핵심 메시지 재확인**

S1은 이전 세션에서 WebFetch로 가져온 내용. 압축 후에도 transcript jsonl에 남아 있음. 필요 시 다시 fetch:

Run: `curl -s https://gist.githubusercontent.com/danvega/1ce70885c6f8b588322bc2c948ec8381/raw | head -200`

S1에서 §1, §5, §6, §7, §10에 매칭되는 권고를 추출 (이 섹션들은 S1이 주 source).

- [ ] **Step 3: 충돌 케이스 식별 + 우선순위 결정 메모**

S1과 S3가 충돌하는 케이스를 명시적으로 표로 정리. 예시:
- Lombok `@Builder`: S1은 권장, S3는 **금지** → S3 우선
- 필드 명명: S1 일반 `getXxx()`, S3는 Record 스타일 `xxx()` → S3 우선
- 패키지 구조: 양쪽 모두 package-by-feature 합의 — 충돌 없음

이 표는 §최상단 "정책 우선순위" 박스로 문서에 포함.

- [ ] **Step 4: 검증**

12개 섹션 모두 S1 또는 S3 (또는 양쪽)에서 인용할 내용이 있는지 체크. 빈 섹션이 있으면 outline 축소 검토.

(이 Task는 commit 없음 — 정보 수집 단계)

---

## Task 2: 문서 스켈레톤 + frontmatter 작성

**Files:**
- Create: `~/DocumentsLocal/msbaek_vault/000-SLIPBOX/MINE/DOCS/spring-boot-project-standards-ktown4u.md`

- [ ] **Step 1: frontmatter 작성 (기존 3문서 컨벤션 정확히 따름)**

기존 `bounded-context-naming.md` frontmatter 패턴:
- id (Title Case + 자연어)
- aliases (3-5개)
- tags (hierarchical, slash-separated)
- author: msbaek
- created_at: "2026-05-19" (quoted)
- source: 출처 명시
- related: []

```markdown
---
id: Spring Boot Project Standards (ktown4u edition)
aliases:
  - Spring Boot 프로젝트 표준 (ktown4u)
  - ktown4u Java 21 Spring Boot 3.x 컨벤션
  - Spring Boot ktown4u SSOT
tags:
  - architecture/spring
  - architecture/spring-boot
  - development/java
  - development/naming
  - development/code-style
  - ktown4u/coding-standards
author: msbaek
created_at: "2026-05-19"
source: S1 (Dan Vega Junie gist) + S3 (kt4u/system-prompts/claude/CLAUDE.md)
related: []
---

# Spring Boot Project Standards (ktown4u edition)

ktown4u 사내 Java 21 + Spring Boot 3.x 컨벤션의 단일 진실 원천(SSOT).
Claude Code 등 AI agent에게 제공할 가이드 문서.

## 정책 우선순위 (충돌 시)

S3(사내 규약) > S1(외부 best practice). 충돌 케이스는 본문 §해당 섹션에 명시.

## 목차

1. 프로젝트 기반 설정
2. 패키지 구조 — package-by-feature
3. Java 코드 스타일 16종
4. @Service 클래스 — 유즈케이스 동사 + Request/Response
5. Constructor Injection + @ConfigurationProperties
6. HTTP Client — RestClient
7. Data Carriers — Records vs Class + Lombok
8. 데이터베이스 / JPA
9. Error Handling + Silent vs Fail Fast 결정 매트릭스
10. Test Strategy
11. DIP & 패키지 간 통신
12. 자주 위반되는 룰 & Blame Command 연결

---

<!-- 섹션별 본문은 Task 3-7에서 채움 -->
```

- [ ] **Step 2: 스켈레톤 저장 + 위치 검증**

Run: `ls -la ~/DocumentsLocal/msbaek_vault/000-SLIPBOX/MINE/DOCS/spring-boot-project-standards-ktown4u.md`
Expected: 파일 존재, ~50줄.

- [ ] **Step 3: Commit (선택 — vault git이 있다면)**

vault repo의 git 사용 여부는 별도. 보통 vault 전체를 한꺼번에 commit하므로 이 task는 skip하고 마지막 Task에서 묶어 commit.

---

## Task 3: §1-2 본문 작성 (프로젝트 기반 + 패키지 구조)

**Files:**
- Modify: `~/DocumentsLocal/msbaek_vault/000-SLIPBOX/MINE/DOCS/spring-boot-project-standards-ktown4u.md` (§1, §2 추가)

- [ ] **Step 1: §1 프로젝트 기반 설정 작성**

내용 (S1 기반):
- Java 21 LTS (왜: virtual threads, pattern matching, sealed classes)
- Spring Boot 3.x (Spring 6, Jakarta EE 9+)
- Maven (Gradle 사용 불가 정책 없음 — S3 침묵)
- 의존성 최소화 원칙 (YAGNI — S3 General Rules와 일치)

코드 예시:
```xml
<!-- Good: pom.xml minimal -->
<parent>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-parent</artifactId>
    <version>3.3.0</version>
</parent>
```

YAGNI 인용 (S3 §General Rules line 6): "명확하게 사용할 곳이 있는 상황에서만 코드를 추가해. 특히 사용하지 않는 메서드를 만들지 말 것."

- [ ] **Step 2: §2 패키지 구조 — package-by-feature 작성**

S3 line 524-587 (Package-by-Feature 원칙 + Bad layer 예시) 인용 + [[victor-rentea-package-by-feature-naming]] wikilink + [[bounded-context-naming]] 휴리스틱 1번(동사/능력) 연결.

코드 예시 (Good + Bad 모두 포함, S3 원문 인용):
```java
// Good - Package-by-Feature
src/main/java/
├── payment/
│   ├── CreatePayment.java          // Service (유즈케이스 동사)
│   ├── PaymentController.java
│   ├── PaymentRepository.java      // package-private
│   └── Payment.java                // Domain
```

ktown4u 맥락: Pre-order Management, Catalog Curation 등 BC가 곧 top-level package.

- [ ] **Step 3: Edit로 §1, §2를 스켈레톤 `<!-- 섹션별 본문은 ... -->` 자리에 삽입**

Edit `old_string: <!-- 섹션별 본문은 Task 3-7에서 채움 -->`
Edit `new_string: <§1 본문>\n\n---\n\n<§2 본문>\n\n---\n\n<!-- 섹션별 본문은 Task 4-7에서 채움 -->`

- [ ] **Step 4: 진행률 검증**

Run: `wc -l ~/DocumentsLocal/msbaek_vault/000-SLIPBOX/MINE/DOCS/spring-boot-project-standards-ktown4u.md`
Expected: ~150줄.

---

## Task 4: §3 본문 작성 (Java 코드 스타일 16종) — 가장 큰 섹션

**Files:**
- Modify: `~/DocumentsLocal/msbaek_vault/000-SLIPBOX/MINE/DOCS/spring-boot-project-standards-ktown4u.md` (§3 추가)

- [ ] **Step 1: 16종 룰을 H3 소제목으로 나열 (S3 line 8-478 직접 정리)**

H3 16개:
1. 파라미터 포맷팅 (3개 이상 개행)
2. Record 스타일 메소드 명명 (`xxx()` 대신 `getXxx()`)
3. Query/Command 메소드 명명 (`xxxBy()`/`xxxFor()`)
4. 예외 처리 (RuntimeException + 일관 프리픽스)
5. Yoda 조건 (상수 좌변)
6. 조건문 (단일 라인 if-return)
7. 로깅 (일관 프리픽스 + 중복 방지)
8. Null Object 패턴 (Kpid.EMPTY)
9. 반복문 (스트림 우선, `.toList()`, 불변 컬렉션)
10. Import 스타일 (qualified)
11. 람다/메서드 레퍼런스 우선
12. 람다 파라미터 명명 (`it` 충돌 시)
13. Collection 우선 (List → Collection weaken)
14. 클래스 가시성 (package-private 기본)
15. 불변성 (final 강제 — 파라미터 + 로컬 변수)
16. Enum 스타일 (code + description + fluent)
17. 클래스 설계 (Parameter Object + Factory Method `from`/`of`)
18. Lombok 규약 (@Getter + @RequiredArgsConstructor + @Accessors(fluent=true) + **@Builder 금지** + 생성자 PRIVATE)

(16-18은 묶을 수 있으면 묶기 — Lombok 규약은 16/17과 강결합)

- [ ] **Step 2: 각 H3마다 "원칙 → Good → Bad" 3블록 작성 (S3 원문 인용)**

각 H3는 분량 짧게:
- 원칙: 1-2 문장
- Good 코드: S3 원문 그대로
- Bad 코드: S3 원문 그대로
- (선택) 왜: 1 문장 (compile-time 안전성 / 가독성 / 불변성 등)

예시 (H3 #5 Yoda):
```markdown
### 5. Yoda 조건 (상수 좌변)

null, 상수, enum 값을 항상 좌변에 배치. 실수로 `=` 사용 시 컴파일 타임에 차단.

```java
// Good
if (null != value) { }
if (EMPTY == this) { }
if ("ACTIVE".equals(status)) { }

// Bad
if (value != null) { }
if (this == EMPTY) { }
```
```

- [ ] **Step 3: §3 전체를 Edit으로 삽입**

Edit `old_string: <!-- 섹션별 본문은 Task 4-7에서 채움 -->`
Edit `new_string: <§3 본문>\n\n---\n\n<!-- 섹션별 본문은 Task 5-7에서 채움 -->`

- [ ] **Step 4: 진행률 검증**

Run: `wc -l ~/DocumentsLocal/msbaek_vault/000-SLIPBOX/MINE/DOCS/spring-boot-project-standards-ktown4u.md`
Expected: ~450-550줄.

---

## Task 5: §4-7 본문 작성 (@Service + Injection + HTTP + Data Carriers)

**Files:**
- Modify: `~/DocumentsLocal/msbaek_vault/000-SLIPBOX/MINE/DOCS/spring-boot-project-standards-ktown4u.md`

- [ ] **Step 1: §4 @Service 클래스 작성**

S3 line 480-516. 핵심:
- 클래스명은 동사로 시작 (`CreateOrderPayment`) — [[bounded-context-naming]] 휴리스틱 1번과 동일 메커니즘 (wikilink 명시)
- 파라미터 `XxxRequest`, 리턴 `XxxResponse` (record 우선)
- **현재 시간 ambient context 제거**: `LocalDateTime.now()` 직접 호출 금지 → Request에 포함 OR 마지막 파라미터로 전달
- 이유: deterministic = 테스트 가능 + 예측 가능

코드 예시 (S3 원문):
```java
@Service
public class CreateOrderPayment {
    public CreateOrderPaymentResponse create(final CreateOrderPaymentRequest request) {
        // request.now() 사용
    }
}

record CreateOrderPaymentRequest(
    Long sellDaddrNo,
    String kpid,
    PaymentStatusCode statusCode,
    LocalDateTime now  // Request에 시간 포함
) {}
```

- [ ] **Step 2: §5 Constructor Injection + @ConfigurationProperties 작성**

S1 기반. 핵심:
- field injection (`@Autowired private SomeService svc`) 금지 — 이유: testability, immutability, missing dependency 즉시 노출
- `@RequiredArgsConstructor` (Lombok) 또는 explicit constructor
- `@ConfigurationProperties(prefix = "...")` + record 조합

코드 예시:
```java
@Service
@RequiredArgsConstructor
class CreatePayment {
    private final PaymentRepository repository;
    private final PaymentGateway gateway;
}

@ConfigurationProperties(prefix = "payment")
record PaymentProperties(String apiKey, Duration timeout) {}
```

- [ ] **Step 3: §6 HTTP Client — RestClient 작성**

S1 기반. 핵심:
- Spring 6+ `RestClient` 사용 — `RestTemplate` 제거 권고
- sync/async 모두 지원
- 빌더 패턴으로 base URL, default header, error handler 설정

코드 예시:
```java
@Bean
RestClient paymentClient(RestClient.Builder builder) {
    return builder
        .baseUrl("https://api.payment.example")
        .defaultHeader("Authorization", "Bearer ...")
        .build();
}
```

- [ ] **Step 4: §7 Data Carriers — Records vs Class + Lombok 조합 작성**

S1 + S3 결합. 핵심:
- **언제 record**: 불변 DTO/VO, 4개 이하 컴포넌트
- **언제 Lombok record-스타일 class**: JPA 엔티티, validation 어노테이션 제약, mutable 필요 (drop case)
- S3 Lombok 조합 인용: `@Getter` + `@RequiredArgsConstructor(access = PRIVATE)` + `@Accessors(fluent = true)` + factory method `of` / `from`
- **@Builder 금지** — 이유: 검증 우회, 가변성 도입

코드 예시 (S3 원문 + S1 record 비교):
```java
// Good - Record (S1 권고)
record CreateOrderPaymentRequest(Long sellDaddrNo, String kpid, LocalDateTime now) {}

// Good - Lombok record-style class (S3, record 사용 불가 시)
@Getter
@RequiredArgsConstructor(access = lombok.AccessLevel.PRIVATE)
@Accessors(fluent = true)
class OrderPayment {
    private final Long sellDaddrNo;
    static OrderPayment of(final Long sellDaddrNo) { return new OrderPayment(sellDaddrNo); }
}

// Bad - @Builder (S3 금지)
@Builder
class OrderPayment { ... }
```

- [ ] **Step 5: §4-7을 Edit으로 삽입**

Edit `old_string: <!-- 섹션별 본문은 Task 5-7에서 채움 -->`
Edit `new_string: <§4-7 본문>\n\n---\n\n<!-- 섹션별 본문은 Task 6-7에서 채움 -->`

- [ ] **Step 6: 진행률 검증**

Run: `wc -l ~/DocumentsLocal/msbaek_vault/000-SLIPBOX/MINE/DOCS/spring-boot-project-standards-ktown4u.md`
Expected: ~700-800줄.

---

## Task 6: §8-10 본문 작성 (JPA + Error Handling + Test Strategy)

**Files:**
- Modify: `~/DocumentsLocal/msbaek_vault/000-SLIPBOX/MINE/DOCS/spring-boot-project-standards-ktown4u.md`

- [ ] **Step 1: §8 데이터베이스 / JPA 작성**

S1 + S3 line 518-523 결합. 핵심:
- **NOW() 함수 SQL 금지** — `LocalDateTime.now()`를 애플리케이션에서 파라미터로 전달 (deterministic)
- **파라미터 바인딩** — SQL Injection 방지
- Aggregate Root만 Repository 인터페이스 보유 (A카테고리 Aggregate 문서와 cross-link)
- N+1 회피: `@EntityGraph`, `JOIN FETCH`
- "DB 만들지 마라" (S1 룰) — 사용자가 명시적으로 요청 안 한 경우 마이그레이션 스크립트 자동 생성 금지

코드 예시:
```java
// Bad - SQL에서 NOW()
@Query("UPDATE Payment p SET p.processedAt = NOW() WHERE p.id = :id")

// Good - 애플리케이션에서 시간 전달
@Query("UPDATE Payment p SET p.processedAt = :now WHERE p.id = :id")
void markProcessed(@Param("id") Long id, @Param("now") LocalDateTime now);
```

- [ ] **Step 2: §9 Error Handling + Silent vs Fail Fast 결정 매트릭스 작성**

S1 (`@ControllerAdvice` + ProblemDetail RFC 7807) + S3 line 93-148 (Silent vs Fail Fast).

핵심 (S3 결정 매트릭스 — 표로 작성):

| 축               | Silent Failure 적절       | Fail Fast 적절   |
| ---------------- | ------------------------- | ---------------- |
| 테스트 커버리지  | 낮음 (레거시)             | 높음 (신규)      |
| 기능 중요도      | 부가 (로깅·모니터링·분석) | 핵심 비즈니스    |
| 시스템 성숙도    | 레거시                    | 새 시스템        |
| 영향 범위        | 격리 가능                 | 전체 영향        |

**불확실하면 사용자에게 질문** (S3 룰 그대로 인용).

코드 예시 (양쪽 패턴):
```java
// Silent - 레거시 부가 기능
try {
    paymentHistoryTracker.track(payment);
} catch (final RuntimeException e) {
    log.warn("payment history: tracking failed", e);
}

// Fail Fast - 신규 핵심 로직
public void processPayment(final Payment payment) {
    if (!payment.isValid()) {
        throw new IllegalArgumentException("Invalid payment: " + payment);
    }
}
```

S1 ProblemDetail 예시:
```java
@RestControllerAdvice
class PaymentExceptionHandler {
    @ExceptionHandler(PaymentValidationException.class)
    ProblemDetail handle(PaymentValidationException e) {
        ProblemDetail pd = ProblemDetail.forStatus(HttpStatus.BAD_REQUEST);
        pd.setTitle("Payment validation failed");
        pd.setDetail(e.getMessage());
        return pd;
    }
}
```

- [ ] **Step 3: §10 Test Strategy 작성**

S1 기반. 핵심:
- 단위 테스트: JUnit 5 + Mockito (도메인 레이어는 mock 최소화)
- 통합 테스트: `@SpringBootTest` (느림 — 정말 필요할 때만)
- DB 테스트: **Testcontainers 우선** (H2는 prod와 SQL dialect 차이로 false positive 위험)
- 컨트롤러: `@WebMvcTest` + `MockMvc`
- Repository: `@DataJpaTest` + Testcontainers MySQL

코드 예시:
```java
@Testcontainers
@DataJpaTest
@AutoConfigureTestDatabase(replace = AutoConfigureTestDatabase.Replace.NONE)
class PaymentRepositoryTest {
    @Container
    static MySQLContainer<?> mysql = new MySQLContainer<>("mysql:8.0");

    @DynamicPropertySource
    static void props(DynamicPropertyRegistry registry) {
        registry.add("spring.datasource.url", mysql::getJdbcUrl);
    }
}
```

- [ ] **Step 4: §8-10을 Edit으로 삽입**

Edit `old_string: <!-- 섹션별 본문은 Task 6-7에서 채움 -->`
Edit `new_string: <§8-10 본문>\n\n---\n\n<!-- 섹션별 본문은 Task 7에서 채움 -->`

- [ ] **Step 5: 진행률 검증**

Run: `wc -l ~/DocumentsLocal/msbaek_vault/000-SLIPBOX/MINE/DOCS/spring-boot-project-standards-ktown4u.md`
Expected: ~950-1050줄.

---

## Task 7: §11-12 본문 작성 (DIP & 패키지 통신 + Blame Command 연결)

**Files:**
- Modify: `~/DocumentsLocal/msbaek_vault/000-SLIPBOX/MINE/DOCS/spring-boot-project-standards-ktown4u.md`

- [ ] **Step 1: §11 DIP & 패키지 간 통신 작성**

S3 line 608-744. 핵심:
- **DIP 준수**: 고수준 → 저수준 직접 의존 금지, 인터페이스에 의존
- **인터페이스 소유권**: 클라이언트(고수준) 패키지에서 인터페이스 정의 — 인프라 패키지에 인터페이스 두면 의존 역전 무효화
- **레이어 의존**: 애플리케이션 → 도메인 / 인프라 → 애플리케이션 / 도메인은 어디에도 의존 안 함
- **이벤트 기반 통신**: 패키지 간 결합 시 도메인 이벤트 우선 (`ApplicationEventPublisher` + `@EventListener`)
- **순환 참조 방지**: 공통 인터페이스 패키지 분리

코드 예시 (S3 원문):
```java
// Good - DIP 준수, 인터페이스는 클라이언트 패키지(order)에서 정의
// order/OrderRepository.java
interface OrderRepository {
    void save(Order order);
}

// infra/JpaOrderRepository.java — 별도 패키지에서 구현
@Repository
class JpaOrderRepository implements OrderRepository { ... }

// Good - 이벤트 기반 패키지 통신
@Service
class CreateOrder {
    private final ApplicationEventPublisher eventPublisher;
    public void create(...) {
        eventPublisher.publishEvent(new OrderCreatedEvent(order.id()));
    }
}

@EventListener
class OrderEventHandler {
    public void handleOrderCreated(final OrderCreatedEvent event) { ... }
}
```

- [ ] **Step 2: §12 자주 위반되는 룰 & Blame Command 연결 작성**

S3 `commands/blame-{korean,code-style,spring}.md` 직접 인용. 핵심:
- 사용자가 즉시 호출하는 violation-reminder 슬래시 커맨드
- `/blame-code-style` — Java 코드 스타일 룰 위반 시 (§3 위반)
- `/blame-spring` — Spring 규칙 위반 시 (§4·§8 위반)
- `/blame-korean` — 한국어 답변 룰 위반 시
- AI agent가 이 룰을 무시하면 → 사용자가 즉시 blame 호출 → "변명 금지, 즉시 수정" 톤으로 reset

`/blame-code-style` 핵심 룰 9개 인용 (S3 원문):
```
- 파라미터 3개 이상 → 개행
- getXxx() → xxx() (Record 스타일)
- Exception → RuntimeException
- value != null → null != value (Yoda)
- 모든 변수에 final
- @Builder 사용 금지
- qualified import 사용
- 메서드 레퍼런스 우선
- Collection 타입 우선
```

`/blame-spring` 핵심 룰 4개:
- @Service 클래스는 동사로 시작 (유즈케이스 명)
- 파라미터 `XxxRequest`, 리턴 `XxxResponse`
- `LocalDateTime.now()` 서비스 직접 호출 금지
- Record 우선

링크: [[ai-agent-guides-backlog]] G카테고리의 Blame Command 패턴.

- [ ] **Step 3: §11-12를 Edit으로 삽입 + 마지막 placeholder 제거**

Edit `old_string: <!-- 섹션별 본문은 Task 7에서 채움 -->`
Edit `new_string: <§11-12 본문>`

- [ ] **Step 4: 진행률 검증 + 전체 스캔**

Run: `wc -l ~/DocumentsLocal/msbaek_vault/000-SLIPBOX/MINE/DOCS/spring-boot-project-standards-ktown4u.md`
Expected: ~1100-1300줄.

Run: `grep -n "<!-- " ~/DocumentsLocal/msbaek_vault/000-SLIPBOX/MINE/DOCS/spring-boot-project-standards-ktown4u.md`
Expected: 0 matches (모든 placeholder 제거 확인).

---

## Task 8: Cross-link 검증 + 본문 정합성 점검

**Files:**
- Modify: `~/DocumentsLocal/msbaek_vault/000-SLIPBOX/MINE/DOCS/spring-boot-project-standards-ktown4u.md`

- [ ] **Step 1: 본문 내 wikilink 일관성 점검**

필수 wikilink (본문에 있어야 함):
- [[victor-rentea-package-by-feature-naming]] (§2에서)
- [[bounded-context-naming]] (§4 @Service 동사 명명 연결)
- [[bounded-context-separation-principles]] (§11 패키지 통신)
- [[ai-agent-guides-backlog]] (§12 Blame Command G카테고리)

Run: `grep -n "\[\[" ~/DocumentsLocal/msbaek_vault/000-SLIPBOX/MINE/DOCS/spring-boot-project-standards-ktown4u.md`
Expected: 4개 모두 등장.

- [ ] **Step 2: 충돌 정책 우선순위 박스 검증**

§최상단 "정책 우선순위" 박스에 명시한 충돌 케이스가 §해당 섹션 본문과 일치하는지:
- `@Builder` 금지 → §7 Data Carriers에서 Bad 예시로 명시 확인
- `getXxx()` → `xxx()` → §3 #2 Record 스타일 메소드 명명에서 다룸 확인

불일치 발견 시 즉시 Edit으로 수정.

- [ ] **Step 3: 12개 섹션 모두 코드 예시 존재 확인**

Run:
```bash
awk '/^## /{section=$0} /^```/{has_code[section]++} END{for(s in has_code) print has_code[s], s}' \
    ~/DocumentsLocal/msbaek_vault/000-SLIPBOX/MINE/DOCS/spring-boot-project-standards-ktown4u.md
```
Expected: 모든 ## 섹션이 최소 1개 이상 ``` 블록 보유 (Failure Conditions 중 "코드 예시 빠짐" 방지).

---

## Task 9: Related Notes 자동 추가 (sub-agent 위임)

**Files:**
- Modify: `~/DocumentsLocal/msbaek_vault/000-SLIPBOX/MINE/DOCS/spring-boot-project-standards-ktown4u.md` (## Related Notes 섹션 추가)

- [ ] **Step 1: `obsidian-forward-related-injector` sub-agent 호출**

`~/.claude/skills/obsidian-document-workflow/` 스킬의 변형 A 패턴.

호출 시 전달:
- 대상 파일: `~/DocumentsLocal/msbaek_vault/000-SLIPBOX/MINE/DOCS/spring-boot-project-standards-ktown4u.md`
- 검색 쿼리: "Spring Boot Project Standards ktown4u" (frontmatter title 우선)
- 모델: sonnet
- 강제 포함 후보: [[victor-rentea-package-by-feature-naming]], [[bounded-context-naming]], [[ai-agent-guides-backlog]] (이미 본문에 인용된 자매 문서 — Related Notes에도 포함해야 가시성 ↑)

Agent prompt 핵심:
- vis hybrid search top-10 + rerank
- 자매 문서 3개 강제 포함 (본문에서 이미 인용됨)
- daily notes 제외, 본인 제외
- 음수 score도 의미 있을 수 있음 (BGE Reranker raw logit)
- 최종 5개 선별

- [ ] **Step 2: ## Related Notes 섹션 추가 검증**

Run: `tail -20 ~/DocumentsLocal/msbaek_vault/000-SLIPBOX/MINE/DOCS/spring-boot-project-standards-ktown4u.md`
Expected: `## Related Notes` H2 + 5개 wikilink + 각 1줄 맥락 설명.

- [ ] **Step 3: backward backlink는 별도 (`vis-backlink-trigger` 스킬이 add-tag 단계에서 처리) — 이 plan에선 skip**

---

## Task 10: ai-agent-guides-backlog.md 갱신

**Files:**
- Modify: `~/DocumentsLocal/msbaek_vault/000-SLIPBOX/MINE/DOCS/ai-agent-guides-backlog.md`

- [ ] **Step 1: Top 1 항목 ☐ → ✅ + wikilink 추가**

Edit:
- old: `- ☐ **Spring Boot Project Standards (ktown4u edition)** — Java 21 LTS, Spring Boot 3.x, Maven, package-by-feature 폴더 구조. _Sources: **S1** 전문 + **S3** §패키지 구조 + [[victor-rentea-package-by-feature-naming]]_`
- new: `- ✅ [[spring-boot-project-standards-ktown4u]] — Java 21 LTS, Spring Boot 3.x, Maven, package-by-feature 폴더 구조. _Sources: **S1** 전문 + **S3** §패키지 구조 + [[victor-rentea-package-by-feature-naming]]_`

- [ ] **Step 2: "이미 작성된 문서" 섹션에 추가 (4번째 항목)**

Edit:
- old: `- ✅ [[bounded-context-naming]] — Central Concept ≠ BC, 명명 휴리스틱 4가지`
- new: `- ✅ [[bounded-context-naming]] — Central Concept ≠ BC, 명명 휴리스틱 4가지\n- ✅ [[spring-boot-project-standards-ktown4u]] — ktown4u Java 21 + Spring Boot 3.x 컨벤션 SSOT (S1+S3 통합)`

- [ ] **Step 3: 새 카테고리 I 신설 — "후속 활용 검토 backlog" (사용자 명시 요구)**

이 카테고리는 가이드 문서를 작성한 *뒤* "어떻게 활용할지" 고민하는 trackable 항목.

Edit (마지막 카테고리 H 뒤에 삽입):

```markdown
### I. 가이드 문서 후속 활용 검토 — Skill / Sub-Agent / Hook 변환

> 이미 작성된 가이드 문서를 *어떤 형태*로 AI agent에게 노출할지 고민하는 backlog.
> 각 가이드 작성 *후* 이 카테고리에 변환 옵션을 검토 항목으로 남긴다.

- ☐ **[[spring-boot-project-standards-ktown4u]] — Skill 변환 검토** — `~/.claude/skills/spring-boot-ktown4u/SKILL.md`로 변환 시 트리거 (Java/Spring 파일 편집 직전 PreToolUse hook) 와 progressive disclosure 구조 설계. _Decision: ROI vs 기존 CLAUDE.md 인용 비교_
- ☐ **Sub-Agent 변환 검토** — `spring-boot-ktown4u-reviewer` 같은 코드 리뷰 sub-agent로 만들지 / 단순 문서 인용으로 충분할지 trade-off. _영향 평가: 토큰 비용 + 정확도 + 트리거 빈도_
- ☐ **Hook 변환 검토** — `/blame-code-style` 자동화 (PostToolUse hook으로 Java 코드 작성 직후 룰 검증). _S3 G카테고리 Blame Command 패턴 연결_
- ☐ **공통 운영 룰**: 새 가이드를 [[ai-agent-guides-backlog]] A-H 카테고리에 작성한 *직후* 이 I 카테고리에 변환 검토 항목을 자동 추가. (예: "A. Aggregate Design Principles 작성 완료 → I 카테고리에 'Aggregate Skill 변환 검토' 항목 추가")
```

- [ ] **Step 4: Top 5 추천 재정렬 (Top 1 ✅ 처리됐으므로 한 칸씩 올림)**

Edit:
- Top 1 (✅된 항목)을 표에서 제거
- 기존 Top 2 (ktown4u Java 스타일 가이드) → Top 1
- 기존 Top 3 → Top 2
- ... 등 1칸씩 위로
- Top 5에 새로 추가: "Domain Event 설계 + ACL 통합 패턴" (기존 6위 후보)

- [ ] **Step 5: backlog 변경 검증**

Run: `grep -c "✅" ~/DocumentsLocal/msbaek_vault/000-SLIPBOX/MINE/DOCS/ai-agent-guides-backlog.md`
Expected: 8개 (기존 3 + 새로 1 + Top 추천 표 안의 wikilink 1 + 본문 인용 등 — 정확한 수치는 작성 후 확인)

Run: `grep -n "^### I\." ~/DocumentsLocal/msbaek_vault/000-SLIPBOX/MINE/DOCS/ai-agent-guides-backlog.md`
Expected: 1 match (새 카테고리 I 신설 확인).

---

## Task 11: Commit + 사용자 검토 요청

**Files:**
- Created: `~/DocumentsLocal/msbaek_vault/000-SLIPBOX/MINE/DOCS/spring-boot-project-standards-ktown4u.md`
- Modified: `~/DocumentsLocal/msbaek_vault/000-SLIPBOX/MINE/DOCS/ai-agent-guides-backlog.md`

- [x] **Step 1: vault git 상태 확인**

Run: `cd ~/DocumentsLocal/msbaek_vault && git status --short -- 000-SLIPBOX/MINE/DOCS/`
Expected: 2개 파일 표시 (new + modified)

- [x] **Step 2: `/commit` skill 호출 (Korean-safe)**

→ vault 자동 백업 cron이 2026-05-19 16:38:49에 두 파일을 commit `2b734cfe` (`+94 / -16`)로 자동 포함함. 별도 `/commit` 불필요.

- [x] **Step 3: 사용자에게 검토 요청 보고**

내용:
- 작성된 파일 경로 + 라인 수
- backlog 갱신 요약 (Top 1 → ✅, Top 추천 재정렬, 카테고리 I 신설)
- Related Notes 5개 후보 명시
- 다음 추천: Top 1이었던 Top 2가 자동으로 Top 1으로 승격 — "ktown4u Java 코드 스타일 가이드 (Record + Lombok 컨벤션)" 작성할지 사용자 의견 확인

---

## Self-Review (작성 후 점검)

**1. Spec coverage:** Top 1 항목의 spec("Java 21 LTS, Spring Boot 3.x, Maven, package-by-feature 폴더 구조 + S1+S3 통합")의 모든 sub-topic이 §1-§12에 매핑되는지 확인 — 매핑 완료.

**2. Placeholder scan:** 본 plan에서 "TBD/TODO/생략" 검색 — Task 1-7 각 step에 실제 코드 블록·예상 출력·구체 경로 포함됨. ✓

**3. Type consistency:**
- 파일명: `spring-boot-project-standards-ktown4u.md` 전체 task에서 동일 ✓
- 섹션 번호: §1-§12 일관 ✓
- frontmatter `id`: "Spring Boot Project Standards (ktown4u edition)" 단일 사용 ✓
- backlog 항목 ☐/✅ 일관 ✓

**4. Risk:**
- Task 4 (코드 스타일 16종)이 가장 큼 — 분량 폭주 시 H3 #1-#8 / #9-#18 두 task로 분리 검토.
- Task 9 sub-agent 위임 시 자매 문서 3개 강제 포함이 실패할 가능성 — fallback: 수동으로 wikilink 5개 직접 작성.

---

## Execution Handoff

**Plan complete and saved to `docs/superpowers/plans/2026-05-19-spring-boot-standards-ktown4u.md`. Two execution options:**

**1. Subagent-Driven (recommended)** — 각 Task를 fresh subagent에 위임, two-stage review로 fast iteration

**2. Inline Execution** — 본 세션에서 executing-plans skill로 batch + checkpoint 실행

**어떤 방식으로 진행할까요?**
