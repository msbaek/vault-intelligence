# ktown4u Java 코드 스타일 가이드 (Record + Lombok 컨벤션) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** S3 사내 규약(`/Users/msbaek/git/kt4u/system-prompts/claude/CLAUDE.md`)의 Java 코드 스타일 16종 전문을 별도 SSOT 문서로 이관하고, 기존 [[spring-boot-project-standards-ktown4u]] §3을 짧은 인덱스+링크로 축소하여 검색·재사용 효율을 높인다.

**Architecture:** Single-file SSOT in vault `000-SLIPBOX/MINE/DOCS/`. spring-boot-standards §3은 H3별 1-2줄 요약 + wikilink로 축소. 16종을 8개(#1-#8)/8개(#9-#16) 묶음으로 분할 + Record/Lombok 컨벤션 심화 + @Builder 금지 anti-pattern + Factory Method 심화 별도 § 추가.

**Tech Stack:** Markdown (Obsidian flavor), wikilinks, hierarchical tags, frontmatter (id/aliases/tags/author/created_at quoted/source/related), vis hybrid search for Related Notes injection.

---

## File Structure

| 경로 | 책임 |
|---|---|
| `000-SLIPBOX/MINE/DOCS/ktown4u-java-code-style.md` (신규) | 16종 코드 스타일 SSOT + Record/Lombok 심화 + @Builder 금지 + Factory Method |
| `000-SLIPBOX/MINE/DOCS/spring-boot-project-standards-ktown4u.md` (수정) | §3 16종 본문 → 인덱스(H3 제목 + 1줄 요약 + 새 가이드 wikilink)로 축소 |
| `000-SLIPBOX/MINE/DOCS/ai-agent-guides-backlog.md` (수정) | E카테고리 Top 1 ☐→✅, Top 5 표 한 칸씩 승격, 새 가이드 wikilink 추가 |

**왜 단일 파일인가**: 16종은 서로 cross-reference가 빈번(예: #1 final → #15 불변성, #2 Record 명명 → #16 Lombok 조합). 분리 시 wikilink 폭증. 단일 파일 + 명확한 H2/H3 구조가 Zettelkasten 검색 + Obsidian outline에 최적.

---

## Task 1: Spec 입력 정리 + 매핑 표

**Files:**
- Read: `~/git/kt4u/system-prompts/claude/CLAUDE.md` (§Java Code Style 16종)
- Read: `~/DocumentsLocal/msbaek_vault/000-SLIPBOX/MINE/DOCS/spring-boot-project-standards-ktown4u.md` §3 (line 187-631)
- Create: (memory only — Task 2 frontmatter 작성에 사용)

- [ ] **Step 1: §3 16종 H3 헤더 + 행 범위 추출**

Run:
```bash
awk '/^### [0-9]+\./ {print NR ": " $0}' \
  ~/DocumentsLocal/msbaek_vault/000-SLIPBOX/MINE/DOCS/spring-boot-project-standards-ktown4u.md \
  | awk -F: '$2 ~ /^ ### / && NR>0' | head -20
```

Expected output (16 lines):
```
### 1. 파라미터 포맷팅
### 2. Record 스타일 메소드 명명
### 3. Query/Command 메소드 명명 규칙
### 4. 예외 처리 스타일
### 5. Yoda 조건 (상수 좌변)
### 6. 조건문 스타일
### 7. 로깅 스타일
### 8. Null Object 패턴
### 9. 반복문 스타일
### 10. Import 스타일
### 11. 람다/메서드 레퍼런스 우선
### 12. 람다 파라미터 명명 규칙
### 13. 컬렉션 타입 선택 (weakening)
### 14. 클래스 가시성
### 15. 불변성 규칙
### 16. Enum + 클래스 설계 + Lombok 조합
```

- [ ] **Step 2: 새 가이드 § 구조 매핑 표 (memory)**

| 새 가이드 § | 포함되는 §3 항목 | 추가 심화 |
|---|---|---|
| §1 개요 + 철학 | — | Record 스타일 일관성 / Lombok 절제 / final 강제 / Composition over Builder |
| §2 코드 포맷팅·Import (#1, #10) | #1 파라미터 포맷팅, #10 Import 스타일 | qualified import의 collision 케이스 |
| §3 명명 컨벤션 (#2, #3, #11, #12) | #2 Record 스타일, #3 Query/Command, #11 메서드 레퍼런스, #12 람다 파라미터 | 명명 → BC Naming 휴리스틱 1번 연결 |
| §4 비교·조건·로깅 (#5, #6, #7) | #5 Yoda, #6 조건문, #7 로깅 | "payment history: " 같은 프리픽스 컨벤션 표 |
| §5 예외·Null Object (#4, #8) | #4 예외 처리, #8 Null Object | Silent vs Fail Fast 4축 결정 매트릭스 |
| §6 반복문·Collection·가시성·불변성 (#9, #13, #14, #15) | #9 반복문, #13 Collection weakening, #14 클래스 가시성, #15 불변성 | package-private 기본 + final 강제 |
| §7 Record + Lombok 조합 심화 (#16) | #16 Enum + 클래스 설계 + Lombok | `@Getter + @RequiredArgsConstructor + @Accessors(fluent=true)` 3종 세트 / Record vs Lombok class 의사결정 트리 |
| §8 @Builder 금지 anti-pattern | #16.3 (Builder 부분) | 왜 금지? + 대체 패턴 4가지 (생성자, Factory Method, Record, Update 메서드) |
| §9 Factory Method (`from`/`of`/`create`) | (신규 — §3에 없음) | 생성자 PRIVATE 강제 + 명명 컨벤션 (`from` 단일 인자, `of` 다중 인자, `create` 도메인 생성) |
| §10 Cross-reference + Related Notes | — | spring-boot-standards, bounded-context-naming, victor-rentea-package-by-feature-naming |

- [ ] **Step 3: §3 → 새 가이드 이관 후 §3 축소 형태 결정**

기존 §3 (line 187-631)을 다음 형태로 축소:

```markdown
## 3. Java 코드 스타일 (16종 인덱스)

전문은 [[ktown4u-java-code-style]]로 이관. 빠른 참조용 인덱스:

| # | 항목 | 한 줄 요약 |
|---|---|---|
| 1 | 파라미터 포맷팅 | 3개 이상 또는 라인 길면 첫 파라미터부터 개행 |
| 2 | Record 스타일 메소드 명명 | `getXxx()` 대신 `xxx()` |
... (16행)

상세 Bad/Good 예시 + Record/Lombok 심화 + @Builder 금지 근거는 [[ktown4u-java-code-style]] 참조.
```

---

## Task 2: 새 파일 frontmatter + 스켈레톤 + §1 개요

**Files:**
- Create: `~/DocumentsLocal/msbaek_vault/000-SLIPBOX/MINE/DOCS/ktown4u-java-code-style.md`

- [ ] **Step 1: frontmatter + § 스켈레톤 작성**

```markdown
---
id: ktown4u Java Code Style Guide
aliases:
  - ktown4u Java 코드 스타일 가이드
  - Java Code Style (Record + Lombok)
  - 16종 코드 스타일
tags:
  - development/java
  - development/coding-style
  - architecture/clean-code
  - development/lombok
  - development/records
author: msbaek
created_at: "2026-05-19"
source: kt4u/system-prompts §Java Code Style 16종 전문 + spring-boot-project-standards §3 이관
related:
  - "[[spring-boot-project-standards-ktown4u]]"
  - "[[bounded-context-naming]]"
  - "[[victor-rentea-package-by-feature-naming]]"
---

# ktown4u Java 코드 스타일 가이드 (Record + Lombok 컨벤션)

> ktown4u Java 프로젝트 공통 코드 스타일 SSOT. [[spring-boot-project-standards-ktown4u]] §3에서 인덱스로 참조됨.

## 1. 개요 — 4가지 철학

(본문 — Step 2에서 작성)

## 2. 코드 포맷팅·Import

## 3. 명명 컨벤션

## 4. 비교·조건·로깅

## 5. 예외 처리 + Null Object

## 6. 반복문·Collection·가시성·불변성

## 7. Record + Lombok 조합 심화

## 8. @Builder 금지 anti-pattern

## 9. Factory Method 패턴 (`from` / `of` / `create`)

## 10. Cross-reference
```

- [ ] **Step 2: §1 개요 본문 작성 — 4가지 철학**

```markdown
## 1. 개요 — 4가지 철학

ktown4u Java 코드 스타일은 다음 4가지 철학에 기반한다. 16종 룰은 모두 이 철학의 구체적 표현이다.

### 1.1 Record 스타일 일관성

Java 14에서 도입된 `record`의 `xxx()` accessor 컨벤션을 일반 클래스에도 일관 적용. `getXxx()`/`setXxx()` JavaBean 컨벤션은 *legacy* 취급.

**왜**: Record와 일반 클래스 간 호출 스타일 불일치는 리팩토링(record ↔ class 전환) 시 호출 사이트 모두 수정해야 하는 비용을 발생시킨다. 일관 컨벤션은 전환 비용을 0으로 만든다.

### 1.2 Lombok 절제 — 3종 세트만 허용

`@Getter` + `@RequiredArgsConstructor` + `@Accessors(fluent = true)` 3종 조합만 표준. `@Setter` `@Data` `@Builder` `@AllArgsConstructor`는 **금지**.

**왜**: 무절제한 Lombok은 (a) 불변성 파괴(@Setter), (b) 잘못된 객체 생성 허용(@Builder의 부분 객체), (c) equals/hashCode 자동생성 함정(@Data)을 초래한다. 3종 세트는 *읽기 전용 + 필수 인자 강제* 의도를 명확히 한다.

### 1.3 final 강제 — 모든 필드·파라미터·로컬 변수

필드·메소드 파라미터·로컬 변수 모두 기본 `final`. 재할당이 필요할 때만 의도적으로 final 제거.

**왜**: 불변 데이터 흐름은 추적 가능성을 극대화한다. "이 변수가 언제 바뀌었지?" 디버깅 시간을 0으로 만든다. 재할당 의도가 있다면 *그것을 명시적으로 드러내는 것*이 정상이다.

### 1.4 Composition over Builder — Factory Method 우선

객체 생성은 *생성자* 또는 *Factory Method* (`from` / `of` / `create`). @Builder는 금지.

**왜**: Builder는 (a) 부분 객체 (필수 필드 누락) 생성을 허용해 invariant 파괴, (b) Record와 비호환, (c) 객체 생성 의도(어떤 시나리오의 생성인가)를 이름에서 잃어버린다. Factory Method는 *생성 의도*를 메소드 이름에 인코딩한다 (예: `Order.from(request)` vs `Order.fromLegacyExcel(row)`).

→ 16종 세부 룰은 §2-§9에서 상세히 다룬다.
```

- [ ] **Step 3: 파일 생성 검증**

Run: `wc -l ~/DocumentsLocal/msbaek_vault/000-SLIPBOX/MINE/DOCS/ktown4u-java-code-style.md`
Expected: ~80 라인 (frontmatter + §1 + § 스켈레톤)

---

## Task 3: §2-§3 본문 (#1, #10 / #2, #3, #11, #12)

**Files:**
- Modify: `~/DocumentsLocal/msbaek_vault/000-SLIPBOX/MINE/DOCS/ktown4u-java-code-style.md`
- Source: spring-boot-project-standards-ktown4u.md §3 (#1, #10, #2, #3, #11, #12 본문)

- [ ] **Step 1: §2 코드 포맷팅·Import 작성**

기존 §3 #1, #10 본문을 그대로 이관 + qualified import collision 케이스 추가:

```markdown
## 2. 코드 포맷팅·Import

### 2.1 파라미터 포맷팅 (#1)

메소드/생성자 파라미터가 3개 이상이거나 라인이 길어질 때 여러 라인으로 개행. 첫 번째 파라미터부터 개행하고 같은 들여쓰기로 정렬, 닫는 괄호는 마지막 파라미터와 같은 들여쓰기 레벨.

**Good — 파라미터 개행**:

\`\`\`java
public OrderPayment create(
    final Long sellDaddrNo,
    final String kpid,
    final PaymentStatusCode statusCode,
    final LocalDateTime createdAt
) {
    // 구현
}

// Good - 짧은 파라미터는 한 라인
public void delete(final Long id) {
    // 구현
}
\`\`\`

**Bad — 긴 라인을 한 줄로**:

\`\`\`java
public OrderPayment create(final Long sellDaddrNo, final String kpid, final PaymentStatusCode statusCode, final LocalDateTime createdAt) {
    // 구현
}
\`\`\`

### 2.2 Import 스타일 (#10)

와일드카드 import 금지. 모든 import는 fully qualified.

**Good**:
\`\`\`java
import com.ktown4u.order.domain.Order;
import com.ktown4u.payment.domain.Payment;
\`\`\`

**Bad**:
\`\`\`java
import com.ktown4u.order.domain.*;
import com.ktown4u.payment.domain.*;
\`\`\`

#### 2.2.1 동명 클래스 collision 처리

같은 클래스명이 서로 다른 패키지에 있을 때 — 한쪽은 import, 다른쪽은 FQN 직접 사용. *둘 다 FQN*은 가독성 저하.

**Good**:
\`\`\`java
import com.ktown4u.order.domain.Status;  // 자주 쓰는 쪽만 import

public class OrderService {
    public void update(Status orderStatus, com.ktown4u.payment.domain.Status paymentStatus) {
        // 명확
    }
}
\`\`\`
```

- [ ] **Step 2: §3 명명 컨벤션 작성 — #2, #3**

기존 §3 #2, #3 본문 이관 + 명명 → BC Naming 휴리스틱 연결:

```markdown
## 3. 명명 컨벤션

### 3.1 Record 스타일 메소드 명명 (#2)

모든 클래스에서 `getXxx()` 대신 `xxx()` 사용. Record의 accessor 컨벤션을 일반 클래스에도 일관 적용.

**Good**:
\`\`\`java
public String code() {
    return this.code;
}

public OrderStatus status() {
    return this.status;
}
\`\`\`

**Bad**:
\`\`\`java
public String getCode() {
    return this.code;
}

public OrderStatus getStatus() {
    return this.status;
}
\`\`\`

**왜**: §1.1 — Record ↔ class 리팩토링 비용 0.

### 3.2 Query/Command 메소드 명명 규칙 (#3)

조회(Query) 메소드와 명령(Command) 메소드의 명명 패턴을 분리.

**Query (단순 조회·검색)**:
- 단일: `xxx()` — 예: `code()`, `status()`
- 조건부: `xxxBy(criteria)` — 예: `findByOrderId(id)`, `existsByKpid(kpid)`
- 용도별: `xxxFor(purpose)` — 예: `priceFor(member)`, `discountFor(coupon)`

**Command (상태 변경)**:
- 도메인 의도가 드러나는 동사 — 예: `place()`, `cancel()`, `settle()`, `refund()`
- ❌ `setXxx()` 금지 — JavaBean 컨벤션은 상태 변경 의도를 숨김

**Good**:
\`\`\`java
public class Order {
    public OrderStatus status() { ... }                  // Query 단일
    public List<OrderItem> itemsBy(ProductCategory c) { ... }  // Query 조건부
    public Money priceFor(Member member) { ... }         // Query 용도별
    public void place() { ... }                          // Command 도메인 동사
    public void cancelWith(Reason reason) { ... }        // Command 인자 포함
}
\`\`\`

**Bad**:
\`\`\`java
public class Order {
    public OrderStatus getStatus() { ... }               // ❌ JavaBean 게터
    public void setStatus(OrderStatus s) { ... }         // ❌ 의도 숨김
    public void updateStatus(OrderStatus s) { ... }      // ❌ 모호 (왜 update?)
}
\`\`\`

**참고**: 메소드 명명 휴리스틱은 패키지·BC 명명과 같은 메커니즘 — [[bounded-context-naming]] 휴리스틱 1번 "동사·능력(Capability) 우선" 참조.

### 3.3 람다/메서드 레퍼런스 우선 (#11)

람다 본문이 단순 메소드 호출이면 메소드 레퍼런스 사용.

**Good**:
\`\`\`java
orders.stream().map(Order::id).toList();
orders.forEach(System.out::println);
\`\`\`

**Bad**:
\`\`\`java
orders.stream().map(o -> o.id()).toList();
orders.forEach(o -> System.out.println(o));
\`\`\`

### 3.4 람다 파라미터 명명 규칙 (#12)

람다 파라미터는 변수가 표현하는 *대상*의 이름. 한 글자 약어(`o`, `x`, `e`) 금지.

**Good**:
\`\`\`java
orders.stream().filter(order -> order.status() == PLACED).toList();
events.forEach(event -> publisher.publish(event));
\`\`\`

**Bad**:
\`\`\`java
orders.stream().filter(o -> o.status() == PLACED).toList();
events.forEach(e -> publisher.publish(e));
\`\`\`
```

- [ ] **Step 3: 검증**

Run: `grep -c "^### " ~/DocumentsLocal/msbaek_vault/000-SLIPBOX/MINE/DOCS/ktown4u-java-code-style.md`
Expected: ≥6 (§2.1, §2.2, §2.2.1, §3.1, §3.2, §3.3, §3.4)

---

## Task 4: §4-§5 본문 (#5, #6, #7 / #4, #8)

**Files:**
- Modify: `~/DocumentsLocal/msbaek_vault/000-SLIPBOX/MINE/DOCS/ktown4u-java-code-style.md`

- [ ] **Step 1: §4 비교·조건·로깅 작성**

기존 §3 #5, #6, #7 본문 이관 + 로깅 프리픽스 컨벤션 표 추가:

```markdown
## 4. 비교·조건·로깅

### 4.1 Yoda 조건 — 상수 좌변 (#5)

상수와 변수를 비교할 때 *상수를 좌변에* 배치. `=` 오타로 인한 의도하지 않은 할당을 컴파일 타임에 방지.

**Good**:
\`\`\`java
if (PLACED == order.status()) { ... }
if (PaymentStatus.SETTLED.equals(payment.status())) { ... }
if ("KR".equals(country)) { ... }
\`\`\`

**Bad**:
\`\`\`java
if (order.status() == PLACED) { ... }                  // 변수 좌변
if (payment.status().equals(PaymentStatus.SETTLED)) { ... }  // NPE 위험
if (country.equals("KR")) { ... }                      // NPE 위험
\`\`\`

**왜**: `equals` 좌변이 null이면 NPE. 상수 좌변은 null safe 보장.

### 4.2 조건문 스타일 (#6)

조건문 단일 라인 / 중괄호 의무. 한 줄 if 금지.

**Good**:
\`\`\`java
if (order.isEmpty()) {
    return;
}
\`\`\`

**Bad**:
\`\`\`java
if (order.isEmpty()) return;
if (order.isEmpty())
    return;
\`\`\`

**왜**: 디버거에서 break point 설정 시 한 줄 if는 진입 여부 판단 불가. 중괄호는 diff에서 추가 라인 인식 명확.

### 4.3 로깅 스타일 (#7)

기능별 로그 메시지 프리픽스를 통일. 검색 가능성을 위해.

**프리픽스 컨벤션 표** (예시):

| 도메인 | 프리픽스 |
|---|---|
| 결제 | `"payment history: "` |
| 주문 | `"order history: "` |
| 배송 | `"shipping history: "` |
| 회원 | `"member action: "` |
| 외부 API | `"external API: "` |
| 이벤트 publish | `"event publish: "` |

**Good**:
\`\`\`java
log.info("payment history: settled, paymentId={}, amount={}", paymentId, amount);
log.warn("external API: PG timeout, gateway={}, durationMs={}", gateway, duration);
\`\`\`

**Bad**:
\`\`\`java
log.info("Payment settled: " + paymentId);  // 프리픽스 없음, 문자열 결합
log.info("결제 완료 " + paymentId);          // 한글 메시지 (검색 어려움)
\`\`\`

**왜**: 로그 검색 시 `grep "payment history:"` 한 번으로 도메인 전체 흐름 추적 가능.
```

- [ ] **Step 2: §5 예외·Null Object 작성**

기존 §3 #4, #8 본문 이관 + Silent vs Fail Fast 4축 결정 매트릭스:

```markdown
## 5. 예외 처리 + Null Object

### 5.1 예외 처리 스타일 (#4)

업무 예외(Domain Exception)는 `IllegalArgumentException`/`IllegalStateException` 같은 표준 RuntimeException을 *직접* 사용. 커스텀 예외 클래스 남발 금지.

**Good**:
\`\`\`java
public void cancel() {
    if (PLACED != this.status) {
        throw new IllegalStateException("취소 가능 상태가 아님: " + this.status);
    }
    this.status = CANCELED;
}
\`\`\`

**Bad**:
\`\`\`java
public void cancel() {
    if (this.status != PLACED) {
        throw new OrderCancellationException("취소 불가");  // 커스텀 예외 남발
    }
    this.status = CANCELED;
}
\`\`\`

**왜**: 커스텀 예외는 (a) 클래스 폭발, (b) 호출 사이트에서 catch 절 폭증, (c) 표준 예외와 의미 중복. 표준 예외 + 명확한 메시지가 더 강력.

#### 5.1.1 Silent vs Fail Fast 4축 결정 매트릭스

예외를 *잡아 삼키느냐(Silent)* vs *던지느냐(Fail Fast)* 결정 시 4축 평가:

| 축 | Silent (catch + log) 선택 | Fail Fast (rethrow) 선택 |
|---|---|---|
| **테스트 커버리지** | 낮음 (코드 경로 미보장) | 높음 (모든 분기 검증됨) |
| **기능 중요도** | 낮음 (부가 기능) | 높음 (핵심 트랜잭션) |
| **시스템 성숙도** | 낮음 (초기 단계, 미발견 케이스 多) | 높음 (안정 운영, 예외=버그) |
| **영향 범위** | 좁음 (단일 사용자) | 넓음 (전체 시스템·데이터 정합성) |

**판단 규칙**: 4축 중 1개라도 Fail Fast 쪽이면 *Fail Fast 우선*. 모호하면 *반드시 질문* (혼자 결정 금지).

**Silent 예시 — 모든 축이 Silent 쪽**:
\`\`\`java
try {
    cacheClient.invalidate(orderId);  // 캐시 무효화 실패는 부가 기능, 낮은 영향
} catch (CacheException e) {
    log.warn("cache invalidation failed, orderId={}", orderId, e);
    // 흐름 계속
}
\`\`\`

**Fail Fast 예시 — 1축이라도 Fail Fast 쪽**:
\`\`\`java
public void settle(final Payment payment) {
    paymentGateway.charge(payment);  // 결제 실패 = 데이터 정합성 위협
    // try-catch 없음 → 위로 전파
}
\`\`\`

### 5.2 Null Object 패턴 (#8)

`null` 반환 대신 *의도 있는 빈 객체*를 반환. NPE 가능성을 메소드 시그니처에서 제거.

**Good**:
\`\`\`java
public List<Order> findByMember(final Long memberId) {
    return orders.stream()
        .filter(o -> o.memberId().equals(memberId))
        .toList();  // 빈 리스트 = Null Object
}

public Optional<Order> findById(final Long id) {
    return Optional.ofNullable(repository.find(id));  // Optional = Null Object
}
\`\`\`

**Bad**:
\`\`\`java
public List<Order> findByMember(final Long memberId) {
    List<Order> result = orders.stream()
        .filter(o -> o.memberId().equals(memberId))
        .toList();
    return result.isEmpty() ? null : result;  // ❌ null 반환
}

public Order findById(final Long id) {
    return repository.find(id);  // ❌ null 가능, 시그니처에서 안 보임
}
\`\`\`

**왜**: 호출자 측에서 null 체크 강제 → 빠뜨리면 NPE. Null Object는 *컴파일러가 강제하는 contract*.
```

- [ ] **Step 3: 검증**

Run: `grep -c "^### \|^#### " ~/DocumentsLocal/msbaek_vault/000-SLIPBOX/MINE/DOCS/ktown4u-java-code-style.md`
Expected: ≥10 (§3까지 7개 + §4.1, §4.2, §4.3, §5.1, §5.1.1, §5.2)

---

## Task 5: §6 본문 (#9, #13, #14, #15)

**Files:**
- Modify: `~/DocumentsLocal/msbaek_vault/000-SLIPBOX/MINE/DOCS/ktown4u-java-code-style.md`

- [ ] **Step 1: §6 반복문·Collection·가시성·불변성 작성**

기존 §3 #9, #13, #14, #15 본문 이관:

```markdown
## 6. 반복문·Collection·가시성·불변성

### 6.1 반복문 스타일 (#9)

`for-each` 또는 Stream 우선. 인덱스 기반 `for (int i = 0; ...)` 금지 (인덱스 자체가 필요한 경우 제외).

**Good**:
\`\`\`java
for (final Order order : orders) {
    process(order);
}

orders.stream()
    .filter(o -> PLACED == o.status())
    .forEach(this::process);
\`\`\`

**Bad**:
\`\`\`java
for (int i = 0; i < orders.size(); i++) {
    process(orders.get(i));  // ❌ 인덱스 불필요
}
\`\`\`

### 6.2 Collection 타입 선택 — weakening (#13)

선언 타입은 *가장 약한 인터페이스* 사용. `ArrayList`/`HashMap`을 직접 노출 금지.

**Good**:
\`\`\`java
public List<Order> orders() {
    return List.copyOf(this.orders);
}

private final Map<Long, Order> ordersById = new HashMap<>();  // 내부 구현은 구체 타입 OK

public Map<Long, Order> ordersById() {
    return Map.copyOf(this.ordersById);  // 반환은 약한 타입 + 불변 복사
}
\`\`\`

**Bad**:
\`\`\`java
public ArrayList<Order> orders() {           // ❌ 구체 타입 노출
    return this.orders;                       // ❌ 가변 노출
}
\`\`\`

**왜**: 약한 타입은 (a) 구현 교체 자유도 ↑, (b) 호출자가 `ArrayList`-specific 메소드(예: `ensureCapacity`)에 의존하지 못함.

### 6.3 클래스 가시성 (#14)

기본 `package-private`. `public`은 *의도적으로* 외부 패키지에서 호출되는 클래스만.

**Good**:
\`\`\`java
package com.ktown4u.order.application;

// public — 외부 패키지(예: web layer)에서 호출
public class PlaceOrder {
    private final OrderRepository repository;
    // ...
}

// package-private — 같은 패키지 내부에서만
class OrderValidator {
    boolean isValid(final Order order) { ... }
}
\`\`\`

**Bad**:
\`\`\`java
public class OrderValidator {  // ❌ 외부에서 호출 안 함에도 public
    public boolean isValid(final Order order) { ... }
}
\`\`\`

**왜**: package-private 기본은 (a) 캡슐화 강화, (b) public API 폭증 방지, (c) 리팩토링 범위 축소. [[victor-rentea-package-by-feature-naming]] 패키지 명명과 결합 시 *진짜 public*만 명확히 드러난다.

### 6.4 불변성 규칙 (#15)

필드·메소드 파라미터·로컬 변수 모두 기본 `final`. 재할당이 필요할 때만 final 제거.

**Good**:
\`\`\`java
public class Order {
    private final Long id;
    private final OrderStatus status;
    private final List<OrderItem> items;

    public void process(final Member member) {
        final Money total = calculateTotal(member);
        final Discount discount = discountFor(member);
        // ...
    }
}
\`\`\`

**Bad**:
\`\`\`java
public class Order {
    private Long id;                 // ❌ final 없음
    private OrderStatus status;
    private List<OrderItem> items;

    public void process(Member member) {  // ❌ 파라미터 final 없음
        Money total = calculateTotal(member);  // ❌ 로컬 final 없음
        // ...
    }
}
\`\`\`

**왜**: §1.3 — 불변 데이터 흐름은 디버깅 시간을 0으로 만든다.
```

- [ ] **Step 2: 검증**

Run: `grep -c "^### \|^#### " ~/DocumentsLocal/msbaek_vault/000-SLIPBOX/MINE/DOCS/ktown4u-java-code-style.md`
Expected: ≥14 (이전 10개 + §6.1, §6.2, §6.3, §6.4)

---

## Task 6: §7 Record + Lombok 조합 심화 (#16)

**Files:**
- Modify: `~/DocumentsLocal/msbaek_vault/000-SLIPBOX/MINE/DOCS/ktown4u-java-code-style.md`

- [ ] **Step 1: §7 Record + Lombok 조합 심화 작성**

기존 §3 #16 본문 이관 + Record vs Lombok class 의사결정 트리:

```markdown
## 7. Record + Lombok 조합 심화

### 7.1 Record vs Lombok class — 의사결정 트리

| 케이스 | 선택 | 이유 |
|---|---|---|
| 순수 불변 데이터 보관 (DTO, Value Object) | **Record** | 컴파일러가 equals/hashCode/toString 자동 생성, 4-line으로 끝남 |
| 동작(behavior)이 있는 도메인 객체 (Entity, Aggregate) | **Lombok class** | 메소드 정의 + 상태 캡슐화 필요, Record는 메소드 추가 시 비대 |
| JPA Entity | **Lombok class** | JPA가 기본 생성자 + setter 요구 — Record 비호환 |
| Builder 패턴이 필요해 보이는 케이스 | **Factory Method 또는 Record** | §8 @Builder 금지 — 어느 쪽도 Builder 안 씀 |

### 7.2 Lombok 3종 세트 — `@Getter` + `@RequiredArgsConstructor` + `@Accessors(fluent = true)`

**표준 조합 (오직 이것만 허용)**:

\`\`\`java
@Getter
@RequiredArgsConstructor
@Accessors(fluent = true)
public class Order {
    private final Long id;
    private final OrderStatus status;
    private final List<OrderItem> items;

    public void place() { ... }
    public void cancel() { ... }
}

// 호출 사이트
final Order order = new Order(1L, PLACED, items);
final OrderStatus status = order.status();   // getXxx() 대신 xxx() — §3.1
\`\`\`

**왜 이 3종**:
- `@Getter` → 모든 필드 read 접근
- `@RequiredArgsConstructor` → `final` 필드 모두 받는 생성자 (불변 강제)
- `@Accessors(fluent = true)` → `getXxx()` → `xxx()` Record 스타일 일관 (§3.1)

### 7.3 금지 Lombok annotation

| Annotation | 금지 이유 | 대체 |
|---|---|---|
| `@Setter` | 불변성 파괴 | 도메인 의도가 드러나는 Command 메소드 (예: `cancel()`) |
| `@Data` | `@Setter` + equals/hashCode 자동생성 함정 | 3종 세트 또는 Record |
| `@Builder` | 부분 객체 생성 허용, Record 비호환 — §8 상세 | 생성자 + Factory Method |
| `@AllArgsConstructor` | 필드 순서 의존성 (필드 추가 시 모든 호출 깨짐) | `@RequiredArgsConstructor` (final 필드만) |
| `@NoArgsConstructor` | JPA 외 사용 시 invariant 파괴 (필수 필드 없이 생성) | JPA Entity는 `@NoArgsConstructor(access = PROTECTED)` 허용 |

### 7.4 Enum 설계 패턴

Enum에 단순 상수 외에 *행위*도 포함. switch 문 대신 polymorphism.

**Good**:
\`\`\`java
public enum OrderStatus {
    PLACED {
        @Override
        public OrderStatus cancel() { return CANCELED; }
    },
    PAID {
        @Override
        public OrderStatus cancel() { return REFUND_REQUESTED; }
    },
    CANCELED {
        @Override
        public OrderStatus cancel() {
            throw new IllegalStateException("이미 취소된 주문");
        }
    };

    public abstract OrderStatus cancel();
}
\`\`\`

**Bad**:
\`\`\`java
public enum OrderStatus { PLACED, PAID, CANCELED }

// 호출 사이트에서 switch
public OrderStatus cancel(OrderStatus current) {
    switch (current) {
        case PLACED: return CANCELED;
        case PAID: return REFUND_REQUESTED;
        case CANCELED: throw new IllegalStateException("이미 취소");
    }
    throw new IllegalStateException("unknown");
}
\`\`\`

**왜**: 새 상태 추가 시 — Good은 enum 한 곳만 수정, Bad는 모든 switch 사이트 수정.
```

- [ ] **Step 2: 검증**

Run: `grep -c "^### \|^#### " ~/DocumentsLocal/msbaek_vault/000-SLIPBOX/MINE/DOCS/ktown4u-java-code-style.md`
Expected: ≥18 (이전 14개 + §7.1, §7.2, §7.3, §7.4)

---

## Task 7: §8 @Builder 금지 anti-pattern

**Files:**
- Modify: `~/DocumentsLocal/msbaek_vault/000-SLIPBOX/MINE/DOCS/ktown4u-java-code-style.md`

- [ ] **Step 1: §8 작성 — @Builder 금지 근거 + 대체 패턴 4가지**

```markdown
## 8. @Builder 금지 anti-pattern

`@Builder`는 ktown4u 코드 스타일에서 **금지**. §1.4 (Composition over Builder) 철학의 구체적 적용.

### 8.1 왜 금지하는가 — 3가지 근거

#### 근거 1: 부분 객체 생성 허용 → invariant 파괴

\`\`\`java
@Builder
public class Order {
    private final Long id;             // 필수
    private final OrderStatus status;  // 필수
    private final List<OrderItem> items;  // 필수
}

// Builder는 필수 필드 누락을 컴파일러가 못 잡음
final Order brokenOrder = Order.builder()
    .id(1L)
    // status, items 누락
    .build();  // ❌ 컴파일 통과, 런타임에 NPE 또는 비정상 상태
\`\`\`

생성자는 컴파일러가 강제:
\`\`\`java
public class Order {
    private final Long id;
    private final OrderStatus status;
    private final List<OrderItem> items;

    public Order(final Long id, final OrderStatus status, final List<OrderItem> items) {
        this.id = id;
        this.status = status;
        this.items = items;
    }
}

// 누락 시 컴파일 에러
final Order order = new Order(1L);  // ❌ 컴파일 에러 — 즉시 발견
\`\`\`

#### 근거 2: Record와 비호환

Record는 `@Builder`를 적용할 수 없음 (Record는 final + canonical constructor가 고정). Builder 사용 시 Record 채택이 불가능해짐 — §7.1 의사결정 트리의 "Record" 선택지가 봉쇄됨.

#### 근거 3: 생성 의도(intent)가 이름에서 사라짐

\`\`\`java
// Builder — 어떤 시나리오의 Order인지 이름에 없음
final Order order = Order.builder()
    .id(1L).status(PLACED).items(items).source(WEB).build();

final Order order2 = Order.builder()
    .id(2L).status(PLACED).items(items).source(LEGACY_EXCEL).build();
\`\`\`

Factory Method는 의도를 이름에 인코딩:
\`\`\`java
final Order order = Order.fromWebRequest(request);
final Order order2 = Order.fromLegacyExcelRow(row);
\`\`\`

### 8.2 대체 패턴 4가지

#### 대체 1: 생성자 + Factory Method (가장 일반적)

\`\`\`java
public class Order {
    private final Long id;
    private final OrderStatus status;
    private final List<OrderItem> items;

    private Order(final Long id, final OrderStatus status, final List<OrderItem> items) {
        this.id = id;
        this.status = status;
        this.items = items;
    }

    public static Order fromWebRequest(final CreateOrderRequest request) {
        return new Order(
            request.id(),
            PLACED,
            request.items()
        );
    }

    public static Order restore(final Long id, final OrderStatus status, final List<OrderItem> items) {
        return new Order(id, status, items);
    }
}
\`\`\`

#### 대체 2: Record (불변 데이터)

\`\`\`java
public record OrderRequest(
    Long memberId,
    List<OrderItemRequest> items,
    Address shippingAddress
) {
    public static OrderRequest from(final WebFormDto dto) {
        return new OrderRequest(
            dto.memberId(),
            dto.items().stream().map(OrderItemRequest::from).toList(),
            Address.from(dto.address())
        );
    }
}
\`\`\`

#### 대체 3: Update 메서드 (Builder처럼 점진 구성하고 싶을 때)

\`\`\`java
public class Order {
    // 필수 필드만 생성자로
    public Order(final Long id, final List<OrderItem> items) { ... }

    // 선택 필드는 도메인 메소드로 (의도 명확)
    public Order applyCoupon(final Coupon coupon) {
        return new Order(this.id, applyDiscount(this.items, coupon));
    }

    public Order changeShippingAddress(final Address newAddress) { ... }
}
\`\`\`

#### 대체 4: Test Fixture (테스트에서 Builder가 필요해 보일 때)

테스트 fixture는 *프로덕션 코드가 아니므로* Builder 패턴을 직접 구현해도 됨 — 단 `@Builder` annotation은 여전히 금지, 명시적 Test Fixture 클래스로:

\`\`\`java
public class OrderFixture {
    private Long id = 1L;
    private OrderStatus status = PLACED;
    private List<OrderItem> items = List.of(OrderItemFixture.default_());

    public OrderFixture id(final Long id) { this.id = id; return this; }
    public OrderFixture status(final OrderStatus status) { this.status = status; return this; }
    public OrderFixture items(final List<OrderItem> items) { this.items = items; return this; }

    public Order build() {
        return new Order(id, status, items);
    }

    public static OrderFixture anOrder() {
        return new OrderFixture();
    }
}

// 사용
final Order order = anOrder().status(CANCELED).build();
\`\`\`
```

- [ ] **Step 2: 검증**

Run: `grep -c "^### \|^#### " ~/DocumentsLocal/msbaek_vault/000-SLIPBOX/MINE/DOCS/ktown4u-java-code-style.md`
Expected: ≥23 (이전 18개 + §8.1, §8.1.1, §8.1.2, §8.1.3, §8.2, §8.2.1, §8.2.2, §8.2.3, §8.2.4 — `####` 포함)

---

## Task 8: §9 Factory Method 심화

**Files:**
- Modify: `~/DocumentsLocal/msbaek_vault/000-SLIPBOX/MINE/DOCS/ktown4u-java-code-style.md`

- [ ] **Step 1: §9 작성 — Factory Method 명명 컨벤션 + 생성자 PRIVATE 강제**

```markdown
## 9. Factory Method 패턴 (`from` / `of` / `create`)

§1.4 + §8의 결과로, 객체 생성은 Factory Method가 *기본 선택지*. 명명 컨벤션을 통일하여 의도를 인코딩.

### 9.1 명명 컨벤션

| 메소드명 | 용도 | 예시 |
|---|---|---|
| `from(X)` | 단일 인자로 변환·복원 | `Order.from(request)`, `Money.from(BigDecimal)` |
| `of(X, Y, ...)` | 다중 인자로 직접 구성 (값 객체 위주) | `Money.of(KRW, 1000)`, `Range.of(start, end)` |
| `create(...)` | 도메인 *생성* 시나리오 (Entity 신규 생성) | `Order.create(memberId, items)` |
| `restore(...)` | 영속화 계층에서 복원 (Entity 재구성) | `Order.restore(id, status, items)` (JPA hydration) |
| `default_()` / `empty()` | 기본 또는 빈 인스턴스 | `Money.zero()`, `OrderItems.empty()` |

**Good**:
\`\`\`java
public class Order {
    private Order(...) { ... }

    public static Order create(final Long memberId, final List<OrderItem> items) {
        return new Order(
            null,                       // ID는 영속화 시 부여
            PLACED,
            items,
            LocalDateTime.now()
        );
    }

    public static Order restore(
        final Long id,
        final OrderStatus status,
        final List<OrderItem> items,
        final LocalDateTime placedAt
    ) {
        return new Order(id, status, items, placedAt);
    }

    public static Order fromLegacyOrder(final LegacyOrder legacy) {
        return new Order(
            legacy.id(),
            mapStatus(legacy.statusCode()),
            legacy.items().stream().map(OrderItem::fromLegacy).toList(),
            legacy.createdAt()
        );
    }
}
\`\`\`

**Bad**:
\`\`\`java
public class Order {
    public Order(...) { ... }  // ❌ public 생성자

    // ❌ 명명 불일치
    public static Order build(...) { ... }
    public static Order make(...) { ... }
    public static Order newOrder(...) { ... }
}
\`\`\`

### 9.2 생성자 PRIVATE 강제

Factory Method를 강제하기 위해 *모든 도메인 클래스의 생성자는 `private`*. 외부에서는 Factory Method만 호출 가능.

**Good**:
\`\`\`java
public class Order {
    private Order(final Long id, ...) {  // private 생성자
        this.id = id;
    }

    public static Order create(...) { ... }    // 외부 진입점
    public static Order restore(...) { ... }
}
\`\`\`

**Bad**:
\`\`\`java
public class Order {
    public Order(final Long id, ...) {  // ❌ public — Factory Method 우회 가능
        this.id = id;
    }
}
\`\`\`

#### 9.2.1 예외 — JPA Entity

JPA는 reflection으로 기본 생성자 호출 → `@NoArgsConstructor(access = AccessLevel.PROTECTED)` 허용. 단 *애플리케이션 코드에서는 호출 금지*.

\`\`\`java
@Entity
@Getter
@Accessors(fluent = true)
@NoArgsConstructor(access = PROTECTED)  // JPA 전용
public class Order {
    @Id @GeneratedValue
    private Long id;
    private OrderStatus status;

    private Order(final OrderStatus status, final List<OrderItem> items) {
        this.status = status;
        this.items = items;
    }

    public static Order create(final List<OrderItem> items) {
        return new Order(PLACED, items);
    }
}
\`\`\`
```

- [ ] **Step 2: 검증**

Run: `grep -c "^### \|^#### " ~/DocumentsLocal/msbaek_vault/000-SLIPBOX/MINE/DOCS/ktown4u-java-code-style.md`
Expected: ≥26 (이전 23개 + §9.1, §9.2, §9.2.1)

---

## Task 9: spring-boot-standards §3 축소

**Files:**
- Modify: `~/DocumentsLocal/msbaek_vault/000-SLIPBOX/MINE/DOCS/spring-boot-project-standards-ktown4u.md` (line 187-631 → 축소)

- [ ] **Step 1: 기존 §3 본문 (line 191-631) 위치 확인**

Run:
```bash
grep -n "^## 3\.\|^## 4\." \
  ~/DocumentsLocal/msbaek_vault/000-SLIPBOX/MINE/DOCS/spring-boot-project-standards-ktown4u.md
```

Expected: `## 3.` (line ~187) + `## 4.` (line ~632)

- [ ] **Step 2: §3 본문을 인덱스 표로 교체**

기존 line 187-631 영역을 다음으로 대체 (Edit 사용, old_string은 정확히 `## 3.` 헤더부터 `## 4.` 이전까지):

```markdown
## 3. Java 코드 스타일 (16종 인덱스)

> **전문은 [[ktown4u-java-code-style]]로 이관**. 본 문서는 빠른 참조용 인덱스만 유지.

| # | 항목 | 한 줄 요약 | 새 가이드 § |
|---|---|---|---|
| 1 | 파라미터 포맷팅 | 3개 이상 또는 라인 길면 첫 파라미터부터 개행 | §2.1 |
| 2 | Record 스타일 메소드 명명 | `getXxx()` 대신 `xxx()` | §3.1 |
| 3 | Query/Command 메소드 명명 규칙 | Query: `xxx`/`xxxBy`/`xxxFor`, Command: 도메인 동사 | §3.2 |
| 4 | 예외 처리 스타일 | 표준 `IllegalArgumentException`/`IllegalStateException` 직접 사용 | §5.1 |
| 5 | Yoda 조건 (상수 좌변) | `if (PLACED == status)` 형태 | §4.1 |
| 6 | 조건문 스타일 | 단일 라인 금지, 중괄호 의무 | §4.2 |
| 7 | 로깅 스타일 | 기능별 프리픽스 통일 (`"payment history: "`) | §4.3 |
| 8 | Null Object 패턴 | `null` 반환 금지, Optional 또는 빈 컬렉션 | §5.2 |
| 9 | 반복문 스타일 | for-each 또는 Stream, 인덱스 for 금지 | §6.1 |
| 10 | Import 스타일 | 와일드카드 금지, fully qualified | §2.2 |
| 11 | 람다/메서드 레퍼런스 우선 | 단순 메소드 호출은 `Class::method` | §3.3 |
| 12 | 람다 파라미터 명명 규칙 | `o`/`x`/`e` 금지, 의미 있는 이름 | §3.4 |
| 13 | 컬렉션 타입 선택 (weakening) | 반환은 `List`/`Map` 약한 타입 + 불변 복사 | §6.2 |
| 14 | 클래스 가시성 | package-private 기본, public은 의도적으로 | §6.3 |
| 15 | 불변성 규칙 | 필드·파라미터·로컬 모두 `final` | §6.4 |
| 16 | Enum + 클래스 설계 + Lombok 조합 | Lombok 3종 세트만 허용, @Builder 금지 | §7 + §8 |

**심화 주제** (새 가이드 별도 § 참조):
- §7 Record + Lombok 조합 심화 — Record vs Lombok class 의사결정 트리, 3종 세트 표준
- §8 @Builder 금지 anti-pattern — 3가지 근거 + 4가지 대체 패턴
- §9 Factory Method 패턴 — `from`/`of`/`create`/`restore` 명명 컨벤션 + 생성자 PRIVATE 강제

```

- [ ] **Step 3: 축소 후 §3 라인 수 검증**

Run:
```bash
awk '/^## 3\./,/^## 4\./' \
  ~/DocumentsLocal/msbaek_vault/000-SLIPBOX/MINE/DOCS/spring-boot-project-standards-ktown4u.md \
  | wc -l
```

Expected: ~30 라인 (기존 ~445 → 30, 93% 축소)

---

## Task 10: Cross-link 검증 + Related Notes 자동 추가

**Files:**
- Modify: `~/DocumentsLocal/msbaek_vault/000-SLIPBOX/MINE/DOCS/ktown4u-java-code-style.md` (§10 + Related Notes)
- Sub-agent: `obsidian-forward-related-injector`

- [ ] **Step 1: §10 Cross-reference 작성 (자매 문서 wikilink)**

```markdown
## 10. Cross-reference

본 가이드는 다음 자매 문서와 묶음으로 사용:

- [[spring-boot-project-standards-ktown4u]] — Spring Boot 프로젝트 표준 (본 가이드의 §3 인덱스가 위치)
- [[bounded-context-naming]] — BC 명명 규칙 (§3.2 메소드 명명과 같은 메커니즘: 동사·능력 우선)
- [[victor-rentea-package-by-feature-naming]] — 패키지 명명 (§6.3 package-private 가시성과 결합 시 진짜 public만 노출)

### 변경 이력

| 날짜 | 변경 | 비고 |
|---|---|---|
| 2026-05-19 | 초안 — S3 `~/git/kt4u/system-prompts/claude/CLAUDE.md` §Java Code Style 16종 + spring-boot-standards §3 본문 통합 | Top 1 가이드 자동 승격 후 작성 |
```

- [ ] **Step 2: obsidian-forward-related-injector sub-agent 위임**

Dispatch with prompt:
```
A 문서: ~/DocumentsLocal/msbaek_vault/000-SLIPBOX/MINE/DOCS/ktown4u-java-code-style.md

vis hybrid search top-10 → 자기 자신 + daily notes + score≤0 제외 → 상위 5개를 "## Related Notes" 섹션에 추가.

자매 문서 3개([[spring-boot-project-standards-ktown4u]], [[bounded-context-naming]], [[victor-rentea-package-by-feature-naming]])는 §10에 이미 명시되어 있으므로 Related Notes 5개는 *다른 문서*에서 선별. 중복 방지.

검색 쿼리: "ktown4u Java 코드 스타일 Record Lombok"
보조 쿼리(결과 빈약 시): "Java 코드 컨벤션 final 불변성 Factory Method"
```

- [ ] **Step 3: Related Notes 5개 결과 검증**

Run:
```bash
sed -n '/^## Related Notes/,$p' \
  ~/DocumentsLocal/msbaek_vault/000-SLIPBOX/MINE/DOCS/ktown4u-java-code-style.md
```

Expected: 5개 `[[...]]` 라인, 자매 문서 3개와 중복 없음.

---

## Task 11: backlog 갱신 + commit + 보고

**Files:**
- Modify: `~/DocumentsLocal/msbaek_vault/000-SLIPBOX/MINE/DOCS/ai-agent-guides-backlog.md`

- [ ] **Step 1: backlog Top 1 (E카테고리) ☐ → ✅**

기존 line 99의 항목:
```
☐ **ktown4u Java 코드 스타일 가이드 (Record + Lombok 컨벤션)** — ...
```

→ 변경:
```
✅ **ktown4u Java 코드 스타일 가이드 (Record + Lombok 컨벤션)** — [[ktown4u-java-code-style]] (16종 + Record/Lombok 심화 + @Builder 금지 + Factory Method) | _S3 25k 문서 압축, spring-boot-standards §3는 인덱스로 축소_
```

- [ ] **Step 2: "이미 작성된 문서" 카운트 4 → 5 + 새 가이드 추가**

기존 list에 추가:
```
- [[ktown4u-java-code-style]] — Java 코드 스타일 16종 SSOT + Record/Lombok 심화 (2026-05-19)
```

- [ ] **Step 3: Top 5 표 재정렬**

기존 Top 1 (Java 코드 스타일) 완료 → 한 칸씩 승격:
- Top 1 ← 기존 Top 2 (Aggregate Design Principles)
- Top 2 ← 기존 Top 3 (6 팀 아키텍처 패턴 결정 트리)
- Top 3 ← 기존 Top 4 (Blame Command 패턴)
- Top 4 ← 기존 Top 5 (Domain Event 설계)
- Top 5 신규 ← "6위~10위 후보" 중 가장 자연스러운 다음 작업 — *Test List + Walking Skeleton (C)* 후보 1순위 (이미 작성된 가이드 4개 + Aggregate Design을 묶는 메타 가이드)

표 footer 갱신:
```
> [[ktown4u-java-code-style]] 작성 완료 (Top 1 ✅ — S3 16종 전문 SSOT). [[spring-boot-project-standards-ktown4u]] §3은 30라인 인덱스로 축소됨.
```

- [ ] **Step 4: vault git 상태 확인 (자동 백업 cron 대기)**

Run: `cd ~/DocumentsLocal/msbaek_vault && git status --short -- 000-SLIPBOX/MINE/DOCS/`

자동 백업 cron이 10분 주기로 돌므로 (이전 작업 16:08/16:18/16:28/16:38 패턴 확인), 1) 백업 cron 대기 또는 2) 명시적 `/commit` 호출. 권장: 명시적 `/commit`으로 의미 있는 commit 메시지 부여.

- [ ] **Step 5: `/commit` skill 호출 (Korean-safe)**

vault 내부에서 `/commit` 호출. 예상 commit 메시지:
```
docs(slipbox): Java 코드 스타일 가이드 SSOT 신규 + spring-boot-standards §3 축소

- 신규: ktown4u-java-code-style.md (16종 + Record/Lombok 심화 + @Builder 금지 + Factory Method)
- 축소: spring-boot-project-standards-ktown4u.md §3 (~445 → 30 라인, 인덱스 형태)
- 갱신: ai-agent-guides-backlog.md (Top 1 ✅, 표 재정렬, "이미 작성된 문서" 5개로)
```

- [ ] **Step 6: 사용자 보고**

내용:
- 신규 파일 경로 + 라인 수
- spring-boot-standards §3 축소 (445 → 30 라인) 확인
- backlog 갱신 요약 (Top 1 → ✅, Top 5 한 칸씩 승격, 신규 Top 5)
- Related Notes 5개 후보 명시
- 다음 추천: 새 Top 1 = "Aggregate Design Principles" — 작성 의향 확인

---

## Self-Review (작성 후 점검)

**1. Spec coverage:** backlog Top 1 항목의 spec(Query/Command 명명 / final 강제 / Lombok 3종 세트 / @Builder 금지 / Factory Method `from`/`of` / S3 §Java Code Style 16종 전문)을 모든 §에 매핑:
- Query/Command 명명 → §3.2 ✓
- final 강제 → §1.3 (철학) + §6.4 (구체 룰) ✓
- Lombok 3종 세트 → §7.2 ✓
- @Builder 금지 → §8 전체 ✓
- Factory Method `from`/`of` → §9.1 ✓
- 16종 전문 → §2 (#1, #10) + §3 (#2, #3, #11, #12) + §4 (#5, #6, #7) + §5 (#4, #8) + §6 (#9, #13, #14, #15) + §7 (#16) ✓ — 모두 16종 커버

**2. Placeholder scan:** 본 plan에서 "TBD/TODO/생략/(생략)" 검색 — 모든 Task에 실제 코드 블록·정확한 경로·예상 출력 포함됨. ✓

**3. Type consistency:**
- 파일명: `ktown4u-java-code-style.md` 전체 task 동일 ✓
- 섹션 번호: §1-§10 일관 ✓
- frontmatter `id`: "ktown4u Java Code Style Guide" 단일 사용 ✓
- backlog 항목 ☐/✅ 일관 ✓
- §3 인덱스 표의 "새 가이드 §" 열 = 실제 § 번호와 일치 (Task 9 Step 2 표 ↔ Task 3-8 § 번호) ✓

**4. Risk:**
- Task 3-8 (16종 본문 + 심화)이 plan 분량의 75% — 각 task는 H3 4개 이내로 제한했으므로 개별 task 분량은 관리 가능.
- Task 9 (§3 축소)은 spring-boot-standards에 영향 — Edit의 old_string 충돌 위험. 대비책: line 번호 기반 grep 사전 검증 (Step 1).
- 사용자 선택 "별도 SSOT" 결정에 따라 §3 축소가 필수 — Task 9 누락 시 SSOT 위반. self-review 통과.

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-05-19-ktown4u-java-code-style.md`.

직전 가이드(spring-boot-project-standards-ktown4u)와 동일 11-task 패턴. SSDD continuous execution으로 진행 권장.
