# Aggregate Design Principles SSOT Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Vaughn Vernon의 "Effective Aggregate Design" 4 rules를 ktown4u Pre-order/Order/Inventory 사례 중심으로 완전 정리한 SSOT 문서를 vault에 신규 작성하고, backlog Top 1 항목을 ✅ 처리한다.

**Architecture:** 단일 markdown 문서 (`000-SLIPBOX/MINE/DOCS/aggregate-design-principles-ktown4u.md`, 800~1000 lines) + backlog (`ai-agent-guides-backlog.md`) 갱신. vault 기존 5개 자료를 `[[wikilink]]`로 흡수해 SSOT 역할 수행. ktown4u-java-code-style / bounded-context-naming 등 자매 문서와 cross-link.

**Tech Stack:** Obsidian markdown (frontmatter `id/aliases/tags/author/created_at/source/related`), 한글 본문 + 영어 코드, `[[wikilink]]`, hierarchical tags (slash-separated lowercase). Java 17 record + Lombok 코드 예시.

---

## File Structure

**Create:**
- `~/DocumentsLocal/msbaek_vault/000-SLIPBOX/MINE/DOCS/aggregate-design-principles-ktown4u.md` (신규 SSOT, 800~1000 lines)

**Modify:**
- `~/DocumentsLocal/msbaek_vault/000-SLIPBOX/MINE/DOCS/ai-agent-guides-backlog.md` (Top 1 ✅, Top 5 재정렬, "이미 작성된 문서 5 → 6")

**Reference (read-only, [[wikilink]]만 사용):**
- `003-RESOURCES/DDD/Effective Aggregate Design.md`
- `003-RESOURCES/DDD/Aggregate/DDD-Aggregate-Reference-Memory-vs-ID.md`
- `003-RESOURCES/DDD/Aggregates-An In-depth Examination by Thomas Coopman Gien Verschatse - DDD Europe.md`
- `003-RESOURCES/DDD/Tactical Domain-Driven Design.md`
- `003-RESOURCES/DDD/What is a DDD Aggregate.md`

---

## Document Structure (목차)

```
§0 Frontmatter + 개요 (40 lines)
§1 핵심 철학: Aggregate = 불변식 + 동시성 + Consistency 경계 (60 lines)
§2 Rule 1 — Small Aggregate (120 lines)
§3 Rule 2 — Reference by ID (130 lines)
§4 Rule 3 — Eventual Consistency outside boundary (120 lines)
§5 Rule 4 — Single transaction per Aggregate root (110 lines)
§6 4 Rules 결합 결정 트리 (80 lines)
§7 ktown4u 사례 1: Pre-order Aggregate (90 lines)
§8 ktown4u 사례 2: Order + OrderLine (80 lines)
§9 ktown4u 사례 3: Inventory 차감/예약 (70 lines)
§10 Anti-pattern 카탈로그 + 체크리스트 (80 lines)
§11 Cross-reference + Related Notes (30 lines)
```

총 ~1000 lines 목표. 각 task는 ⅓~⅒ 분량.

---

## Task 1: Spec 정리 + 자료 매핑 표

**Files:**
- Modify: `~/git/vault-intelligence/docs/superpowers/plans/2026-05-20-aggregate-design-principles-ktown4u.md` (이 파일 — 아래 매핑 표 추가)

- [ ] **Step 1: vault 자료 → 신규 문서 섹션 매핑 표 작성**

본 plan 파일 끝에 아래 표를 append:

```markdown
## Source → Section Mapping

| vault 자료 ([[wikilink]]) | 활용 섹션 | 어떻게 흡수 |
| --- | --- | --- |
| [[Effective Aggregate Design]] | §1, §2, §3, §4, §5 | Vernon 원전 4 rules 본문, 금융 시스템 70% 통계 |
| [[DDD-Aggregate-Reference-Memory-vs-ID]] | §3, §6 | Memory vs ID 결정 트리 (Rule 2 보강), ValueObject 감싸기 패턴 |
| [[Aggregates-An In-depth Examination by Thomas Coopman Gien Verschatse - DDD Europe]] | §1, §10 | "복잡한 entity = aggregate" 오해 반박, 불변식·동시성 실제 필요할 때만 |
| [[Tactical Domain-Driven Design]] | §5, §6 | optimistic locking, invariant enforcement 책임 분리 |
| [[What is a DDD Aggregate]] | §1, §10 | 정의·invariant root 책임, anti-pattern 예시 |
| [[ktown4u-java-code-style]] | §7, §8, §9 | Record + Lombok 3종 세트, Factory Method 4종, @Builder 금지 |
| [[bounded-context-naming]] | §3, §11 | BC 간 ID 참조 시 같은 명사 다른 의미 (Sales Customer vs Shipping Prospect) |
| [[bounded-context-separation-principles]] | §4, §11 | BC 분리 = aggregate 분리 != 동일, eventual consistency BC 횡단 패턴 |
| [[victor-rentea-package-by-feature-naming]] | §6, §11 | use case 단위 = 단일 aggregate root 변경 단위 |
| [[spring-boot-project-standards-ktown4u]] | §7, §11 | persistence 경계, repository 패턴 |
```

- [ ] **Step 2: 4 rules 핵심 한 줄 요약 카드 작성**

본 plan 파일 끝에 추가:

```markdown
## 4 Rules 카드 (각 섹션 헤더로 재사용)

- **Rule 1 — Small Aggregate**: 불변식이 요구하는 최소 범위로 제한. 70% 사례는 root + value object만.
- **Rule 2 — Reference by ID**: 경계 외부 객체는 ValueObject로 감싼 ID로만 참조. Memory reference는 같은 aggregate 내부에서만.
- **Rule 3 — Eventual Consistency outside boundary**: aggregate 경계를 넘는 규칙은 domain event + 명시적 inconsistency window (초 vs 일).
- **Rule 4 — Single transaction per Aggregate root**: 1 트랜잭션 = 1 aggregate root 변경. 2개 이상이면 event 기반 재설계.
```

- [ ] **Step 3: Commit**

```bash
cd ~/git/vault-intelligence && git add docs/superpowers/plans/2026-05-20-aggregate-design-principles-ktown4u.md
git commit -F /tmp/commit-msg.txt   # 메시지: "plan(aggregate): source mapping + 4 rules cards 추가"
```

---

## Task 2: 신규 파일 frontmatter + §0 개요 + §1 핵심 철학

**Files:**
- Create: `~/DocumentsLocal/msbaek_vault/000-SLIPBOX/MINE/DOCS/aggregate-design-principles-ktown4u.md`

- [ ] **Step 1: 파일 생성 (frontmatter + §0 + §1)**

```markdown
---
id: Aggregate Design Principles for ktown4u
aliases:
  - Aggregate Design Principles
  - DDD Aggregate 4 Rules
  - Vernon Aggregate Rules
  - ktown4u Aggregate 설계 가이드
tags:
  - development/ddd
  - architecture/ddd/tactical-design
  - architecture/ddd/aggregate
  - architecture/ddd/consistency-boundary
  - domain-modeling
author: msbaek
created_at: "2026-05-20"
source: "vault synthesis (Effective Aggregate Design + 4 supporting documents) + ktown4u domain application"
related:
  - "[[Effective Aggregate Design]]"
  - "[[DDD-Aggregate-Reference-Memory-vs-ID]]"
  - "[[ktown4u-java-code-style]]"
  - "[[bounded-context-naming]]"
  - "[[bounded-context-separation-principles]]"
---

# Aggregate Design Principles for ktown4u

> **목적**: Vaughn Vernon "Effective Aggregate Design" 4 rules를 ktown4u 도메인 (Pre-order / Order / Inventory) 에 적용한 실전 SSOT.
> **선행 문서**: [[ktown4u-java-code-style]] (Record + Lombok), [[bounded-context-naming]] (BC 식별).
> **읽는 순서**: §1 철학 → §2~§5 4 rules → §6 결정 트리 → §7~§9 ktown4u 사례 → §10 Anti-pattern → §11 Cross-reference.

## §0 한눈에 보는 4 Rules

| Rule | 한 줄 요약 | 위반 시 신호 |
| --- | --- | --- |
| **1. Small Aggregate** | 불변식이 요구하는 최소 범위로 제한 | lock 경합 증가, 트랜잭션 실패율 ↑ |
| **2. Reference by ID** | 경계 외부 객체는 ValueObject ID로만 참조 | 객체 그래프 폭증, 의도치 않은 상태 변경 |
| **3. Eventual Consistency outside boundary** | aggregate 경계를 넘는 규칙은 domain event 기반 | 분산 lock, deadlock, 마이크로서비스 분리 곤란 |
| **4. Single transaction per Aggregate root** | 1 트랜잭션 = 1 aggregate root 변경 | 동시성 경합, 분산 트랜잭션 복잡성 |

→ 4 rules는 **하나의 원리의 4가지 면**: "aggregate = 불변식 + 동시성 + consistency = 트랜잭션 경계" (§1 참조).

## §1 핵심 철학: Aggregate = 불변식 + 동시성 + Consistency 경계

### §1.1 3개 개념이 사실은 하나

DDD에서 가장 자주 혼동되는 부분 — **aggregate boundary, transaction boundary, consistency boundary 는 동일한 것** (Vernon, [[What is a DDD Aggregate]]).

- **불변식 (Invariant)**: 항상 참이어야 하는 비즈니스 규칙. 예: "주문 총액 = sum(orderLine.amount)".
- **동시성 (Concurrency)**: 동시에 변경되어도 불변식이 유지되어야 하는 범위 → optimistic lock 단위.
- **Consistency 경계**: 한 트랜잭션에서 ACID로 보장해야 하는 데이터 범위.

→ 세 개념이 모두 같은 경계를 가리키면 aggregate 설계가 자연스럽게 도출됨. 다르면 aggregate 경계를 잘못 잡은 것.

### §1.2 "복잡한 entity = aggregate"는 오해

Coopman/Verschatse (DDD Europe, [[Aggregates-An In-depth Examination by Thomas Coopman Gien Verschatse - DDD Europe]]) 가 지적한 흔한 함정:

> "Entity가 여러 필드를 갖고 children을 가진다고 aggregate가 되는 것이 아니다. **불변식과 동시성이 실제로 필요할 때만** aggregate."

- ❌ Anti-pattern: "Customer에 Address, Phone, Preference가 있으니까 Customer = aggregate"
- ✅ Correct: "Customer의 모든 필드가 한 트랜잭션에서 함께 변경되어야 할 invariant가 있는가? 없으면 Customer는 단순 entity, Address/Preference는 별도 aggregate 또는 VO일 수 있음"

### §1.3 도메인 전문가 인터뷰가 필수

> Vernon: "도메인 전문가에게 'A를 변경할 때 B도 반드시 같은 순간에 일관되어야 합니까?' 라고 물어라. 답이 'No, 1~2초 늦어도 된다'면 → 다른 aggregate."

ktown4u 예: "Pre-order 수량을 변경할 때 매장 재고가 즉시 반영되어야 합니까?" → 도메인 답이 "1초 이내면 충분" → Pre-order 와 Inventory 는 **다른 aggregate, eventual consistency**.

### §1.4 vault에서 시작하기

본 문서를 읽기 전 또는 함께 권장:
- [[Effective Aggregate Design]] — Vernon 원전 (4 rules 본문 + 금융 시스템 사례)
- [[What is a DDD Aggregate]] — 정의·root 책임 정리
- [[Tactical Domain-Driven Design]] — invariant enforcement, optimistic lock 패턴
```

- [ ] **Step 2: 문서 검증**

```bash
wc -l ~/DocumentsLocal/msbaek_vault/000-SLIPBOX/MINE/DOCS/aggregate-design-principles-ktown4u.md
# Expected: ~80 lines (frontmatter + §0 + §1)
grep -c "^## " ~/DocumentsLocal/msbaek_vault/000-SLIPBOX/MINE/DOCS/aggregate-design-principles-ktown4u.md
# Expected: 2 (§0, §1)
```

- [ ] **Step 3: Commit (vault 자동 백업 cron이 처리하므로 명시적 commit 불필요, 다음 task로 진행)**

---

## Task 3: §2 Rule 1 — Small Aggregate

**Files:**
- Modify: `~/DocumentsLocal/msbaek_vault/000-SLIPBOX/MINE/DOCS/aggregate-design-principles-ktown4u.md` (append §2)

- [ ] **Step 1: §2 본문 추가**

파일 끝에 append:

```markdown
## §2 Rule 1 — Small Aggregate

> **한 줄**: 불변식이 요구하는 최소 범위로 제한. 70% 사례는 root + value object만으로 충분.

### §2.1 Vernon의 실증 데이터

[[Effective Aggregate Design]] 의 핵심 통계 (금융 시스템 분석):

| Aggregate 구성 | 비율 |
| --- | --- |
| root entity + value object 만 | **~70%** |
| root + 1~2 local entity (composite) | ~30% |
| 거대 composite (5개 이상 entity) | 거의 0 (대부분 설계 오류) |

→ **default는 작게 시작**, composite 가 필요하다는 명백한 invariant 가 있을 때만 확장.

### §2.2 "작다"의 정의

- 메모리 관점: 한 트랜잭션에서 메모리에 올려도 부담 없는 크기
- 동시성 관점: 동시 변경 시 lock 경합이 비즈니스 throughput 을 막지 않는 크기
- 불변식 관점: invariant 검증에 필요한 데이터만 포함하는 크기

### §2.3 작게 유지하는 5가지 휴리스틱

1. **Children 컬렉션 크기 무제한 금지** — `List<OrderLine>` 이 수천 건이 될 수 있으면 OrderLine 을 별도 aggregate 후보로 검토.
2. **외부 aggregate 직접 참조 금지** — Rule 2 와 결합. Customer entity 를 Order 내부에 두지 말고 `CustomerId` 로 참조.
3. **시간 의존 데이터는 스냅샷** — 주문 시점 가격은 Product 참조가 아니라 `Money price` 로 복사 저장.
4. **report·조회용 필드 분리** — "지난 30일 주문 합계" 같은 필드는 aggregate 내부가 아니라 별도 read model.
5. **derived field 계산 시점 분리** — 매 변경마다 재계산해야 하는 derived field 가 무거우면 aggregate 가 너무 큰 것.

### §2.4 일반 e-commerce 예시

```java
// ❌ Anti-pattern: 거대 Order aggregate
public class Order {
  private OrderId id;
  private Customer customer;           // Customer 전체 참조 (외부 aggregate)
  private List<OrderLine> lines;       // OK (내부)
  private List<Payment> payments;      // Payment 가 별도 aggregate 후보
  private List<Shipment> shipments;    // Shipment 도 별도 aggregate 후보
  private List<RefundRequest> refunds; // Refund 라이프사이클 별도
  private InventoryReservation inv;    // 다른 BC
  // ... 12개 필드
}

// ✅ Small aggregate
public class Order {
  private OrderId id;
  private CustomerId customerId;       // ID 참조 (Rule 2)
  private List<OrderLine> lines;       // local entity
  private Money totalAmount;           // derived, 변경 시 재계산
  private OrderStatus status;
  // 끝. Payment, Shipment, Refund 는 각각 별도 aggregate.
}
```

### §2.5 ktown4u 적용 hint

- **Order**: root + OrderLine (local) + Money 총액. CustomerId / ProductId 는 ID 참조.
- **PreOrder**: root + 예약 수량 + 만료 시간. 재고 차감은 별도 aggregate.
- **Inventory**: root + 가용수량 + 예약수량. 출고/입고는 별도 use case로 이벤트 발행.

자세한 사례는 §7~§9 참조.

### §2.6 위반 시 신호

- DB lock 대기 시간 증가 (특정 aggregate 에 read·write 가 몰림)
- 단일 use case 가 여러 트랜잭션으로 분리되는 요구 (Vernon: "aggregate 경계 재검토 신호")
- 객체 그래프 로딩 시간이 SLA 초과 (`@OneToMany` lazy 로 우회하다 N+1)
- 도메인 전문가가 "이 둘은 사실 관련 없다" 라고 답하는데 같은 aggregate

→ 신호 발견 시 §10 anti-pattern 카탈로그 + §6 결정 트리로 재검토.
```

- [ ] **Step 2: 검증**

```bash
wc -l ~/DocumentsLocal/msbaek_vault/000-SLIPBOX/MINE/DOCS/aggregate-design-principles-ktown4u.md
# Expected: ~200 lines (~80 + ~120)
```

---

## Task 4: §3 Rule 2 — Reference by ID

**Files:**
- Modify: `~/DocumentsLocal/msbaek_vault/000-SLIPBOX/MINE/DOCS/aggregate-design-principles-ktown4u.md` (append §3)

- [ ] **Step 1: §3 본문 추가**

```markdown
## §3 Rule 2 — Reference by ID

> **한 줄**: 경계 외부 객체는 ValueObject ID로만 참조. Memory reference는 같은 aggregate 내부에서만.

### §3.1 Vernon의 원칙

[[Effective Aggregate Design]]:

> "Prefer references to external Aggregates only by their globally unique identity, not by holding a direct object reference."

→ 직접 객체 참조는 의도치 않은 상태 변경, 거대 객체 그래프 로딩, 분산 시스템 분리 곤란을 야기.

### §3.2 Memory vs ID 결정 트리

[[DDD-Aggregate-Reference-Memory-vs-ID]] 에서 정리된 결정 플로우:

```
변경 대상이 같은 aggregate root 의 일부인가?
├─ Yes → Memory reference OK (예: Order → OrderLine)
└─ No  → ID reference 필수 (예: Order → CustomerId)
         │
         └─ ValueObject 로 감쌌는가?
            ├─ Yes → 타입 안전 (CustomerId, OrderId, ProductId)
            └─ No  → primitive obsession 안티패턴 (Long, UUID 그대로 사용 금지)
```

### §3.3 ValueObject 로 감싸는 이유

```java
// ❌ Primitive obsession
public class Order {
  private Long customerId;   // Long 이 customer인지 product인지 누가 알아?
  private Long productId;
  // 메서드 시그니처에서 의미 손실
  public void place(Long customerId, Long productId) { ... }
}

// ✅ Typed ID
public record CustomerId(long value) {}
public record ProductId(long value) {}

public class Order {
  private CustomerId customerId;
  private ProductId productId;
  public void place(CustomerId customerId, ProductId productId) { ... }
}
```

→ 컴파일러가 customerId 자리에 productId 가 들어가는 실수를 잡음. [[ktown4u-java-code-style]] §3 명명 규칙과 일관.

### §3.4 ID 참조로 인한 트레이드오프

| 측면 | Memory reference | ID reference |
| --- | --- | --- |
| 일관성 | 강한 일관성 (같은 트랜잭션) | Eventual (Rule 3 적용) |
| 결합도 | 강함 (Customer 변경 → Order 영향) | 약함 (독립적 변경) |
| 로딩 비용 | 객체 그래프 폭증 위험 | 필요시 Application Service 에서 조합 |
| 마이크로서비스 분리 | 어려움 | 자연스러움 |

→ **default 는 ID 참조**, memory reference 는 같은 aggregate 내부에서만.

### §3.5 ID 만으로 부족할 때 — Application Service 조합

```java
// Application Service: 여러 aggregate 조회·조합
@Service
@RequiredArgsConstructor
public class OrderPlacementService {
  private final OrderRepository orderRepo;
  private final CustomerRepository customerRepo;
  private final ProductRepository productRepo;

  public OrderPlacedResponse placeOrder(PlaceOrderCommand cmd) {
    // 1. 외부 aggregate 조회 (ID 로)
    Customer customer = customerRepo.findById(cmd.customerId());
    Product product = productRepo.findById(cmd.productId());

    // 2. 검증 (이 시점 정보로)
    customer.assertActive();
    product.assertAvailable();

    // 3. Order 생성 (ID 만 전달, Customer/Product 객체 전달 금지)
    Order order = Order.place(cmd.customerId(), cmd.productId(), product.priceSnapshot());

    // 4. 저장 (Order aggregate 만 변경)
    orderRepo.save(order);
    return OrderPlacedResponse.from(order);
  }
}
```

→ Customer 와 Product 는 조회용으로만 사용, Order 트랜잭션에서 변경 금지 (Rule 4).

### §3.6 BC 경계를 가로지를 때 — 같은 명사 다른 의미

[[bounded-context-naming]] 에서 강조한 원리와 결합:

```
Sales BC                  Shipping BC
Order { customerId } -ID->  ShipmentRequest { logisticsProspectId }
                            (같은 사람인데 의미가 다름)
```

→ Sales 의 `CustomerId` 와 Shipping 의 `LogisticsProspectId` 는 **글로벌 unique ID 는 같지만 ValueObject 타입은 다름**. ACL 에서 변환.

### §3.7 ktown4u 적용 hint

```java
// Order aggregate (Sales BC)
public class Order {
  private OrderId id;
  private CustomerId customerId;     // VO ID
  private List<OrderLine> lines;
  // ...
}

public class OrderLine {  // local entity
  private OrderLineId id;
  private ProductId productId;       // VO ID (외부 aggregate)
  private Money priceSnapshot;       // 시점 가격 복사 (Product 변경과 독립)
  private int quantity;
}
```

→ Product 의 가격 변동이 과거 주문에 영향 없음 (스냅샷).

### §3.8 위반 시 신호

- `@OneToMany(fetch = LAZY)` 로 N+1 회피 노력 (객체 그래프 너무 큼)
- Order entity 안에 Customer 전체 데이터 (이름, 주소, 연락처) 가 들어 있음
- 트랜잭션 안에서 다른 aggregate 의 setter 호출 (Rule 4 도 위반)
- ID 가 `Long` / `UUID` raw 타입으로 노출 (primitive obsession)
```

- [ ] **Step 2: 검증**

```bash
wc -l ~/DocumentsLocal/msbaek_vault/000-SLIPBOX/MINE/DOCS/aggregate-design-principles-ktown4u.md
# Expected: ~330 lines (200 + ~130)
```

---

## Task 5: §4 Rule 3 — Eventual Consistency outside boundary

**Files:**
- Modify: `~/DocumentsLocal/msbaek_vault/000-SLIPBOX/MINE/DOCS/aggregate-design-principles-ktown4u.md` (append §4)

- [ ] **Step 1: §4 본문 추가**

```markdown
## §4 Rule 3 — Eventual Consistency outside boundary

> **한 줄**: aggregate 경계를 넘는 규칙은 domain event 기반. 명시적 inconsistency window (초 vs 일) 정의 필수.

### §4.1 Vernon의 원칙

[[Effective Aggregate Design]]:

> "Any rule that spans Aggregates will not be expected to be up-to-date at all times. Through event processing, batch processing, or other update mechanisms, other dependencies can be resolved within some specified time."

→ 강한 일관성은 **하나의 aggregate 내부에서만** 보장. 경계 외부는 비동기/이벤트 기반.

### §4.2 Eric Evans의 원리

[[Effective Aggregate Design]] 인용:

- 트랜잭션 경합 감소 → 시스템 확장성·복원력 향상
- 다중 aggregate 변경 시 분산 lock·deadlock 위험 회피
- 마이크로서비스 분리 시 BC 횡단 트랜잭션 불필요

### §4.3 "허용 inconsistency window" 명시 필수

도메인 전문가와 함께 결정:

| 비즈니스 영역 | 허용 window | 이유 |
| --- | --- | --- |
| 결제 → 배송 준비 | 수 초 (5초 이내) | 고객 경험 |
| 주문 → 재고 차감 | 1초 이내 | oversell 방지 |
| 주문 → 매출 보고서 | 수 분~수 시간 | report 라서 OK |
| 회원 등급 변경 → 할인 적용 | 다음 주문부터 | 일 단위로 충분 |

→ **숫자로 명시**, "eventual" 만 말하면 불충분.

### §4.4 Domain Event 패턴 기본

```java
// 1. Aggregate 가 이벤트 발행
public class Order {
  private final List<DomainEvent> events = new ArrayList<>();

  public static Order place(CustomerId customerId, ProductId productId, Money price) {
    Order order = new Order(/* ... */);
    order.events.add(new OrderPlacedEvent(order.id, customerId, productId, price));
    return order;
  }

  public List<DomainEvent> pullEvents() {
    List<DomainEvent> pulled = List.copyOf(events);
    events.clear();
    return pulled;
  }
}

// 2. Application Service 가 트랜잭션 commit 후 발행
@Service
@RequiredArgsConstructor
public class OrderPlacementService {
  private final OrderRepository orderRepo;
  private final DomainEventPublisher publisher;

  @Transactional
  public void placeOrder(PlaceOrderCommand cmd) {
    Order order = Order.place(cmd.customerId(), cmd.productId(), cmd.price());
    orderRepo.save(order);
    // 같은 트랜잭션 안에서 publish (outbox pattern 권장)
    publisher.publishAll(order.pullEvents());
  }
}

// 3. 별도 트랜잭션에서 Inventory aggregate 업데이트
@Component
@RequiredArgsConstructor
public class InventoryUpdater {
  private final InventoryRepository inventoryRepo;

  @EventListener
  @Transactional(propagation = REQUIRES_NEW)  // 별도 트랜잭션
  public void on(OrderPlacedEvent event) {
    Inventory inventory = inventoryRepo.findByProductId(event.productId());
    inventory.reserve(event.quantity());
    inventoryRepo.save(inventory);
  }
}
```

→ Order 트랜잭션 commit 후 Inventory 가 따로 변경 → Rule 4 (1 transaction = 1 aggregate) 준수.

### §4.5 Outbox Pattern (At-least-once + Idempotency)

이벤트 손실 방지:

```java
// 1. Order 저장과 동시에 outbox 테이블에 이벤트 저장 (같은 트랜잭션)
@Transactional
public void placeOrder(PlaceOrderCommand cmd) {
  Order order = Order.place(/* ... */);
  orderRepo.save(order);
  outboxRepo.saveAll(order.pullEvents());  // 같은 트랜잭션 → 원자성
}

// 2. 별도 poller 가 outbox → 메시지 브로커로 전송
// 3. 수신자는 idempotent (eventId 기반 중복 제거)
```

→ At-least-once delivery + idempotent receiver = exactly-once semantic.

### §4.6 ktown4u 적용 hint

- **Pre-order → Inventory**: PreOrderCreatedEvent → Inventory.reserve() (1초 이내 동기화)
- **Order → 매출 보고서**: OrderPlacedEvent → BI 적재 (분 단위)
- **회원 등급 변경 → 할인 정책**: GradeChangedEvent → DiscountPolicy refresh (다음 주문부터)
- **결제 완료 → 배송 준비**: PaymentCompletedEvent → ShipmentRequest 생성 (수 초)

### §4.7 Anti-pattern 회피

- ❌ "모든 aggregate 변경을 한 트랜잭션에 묶기" → 분산 lock, deadlock, throughput 하락
- ❌ "이벤트 없이 polling 으로 동기화" → DB 부하, latency 증가
- ❌ "허용 window 모호 (eventual 만 말함)" → 비즈니스 사이드와 갈등 (oversell 등)
- ❌ "이벤트 발행 후 같은 트랜잭션에서 다른 aggregate 동기 호출" → Rule 4 위반

### §4.8 위반 시 신호

- 동일 use case 에서 여러 aggregate 의 repository.save() 가 같은 @Transactional 안
- 도메인 전문가가 "1초 늦어도 된다" 라고 했는데 강한 일관성으로 구현
- 분산 트랜잭션 (2PC, Saga 동기 버전) 도입 (대부분 aggregate 경계 잘못)
```

- [ ] **Step 2: 검증**

```bash
wc -l ~/DocumentsLocal/msbaek_vault/000-SLIPBOX/MINE/DOCS/aggregate-design-principles-ktown4u.md
# Expected: ~450 lines
```

---

## Task 6: §5 Rule 4 — Single transaction per Aggregate root + §6 결정 트리

**Files:**
- Modify: `~/DocumentsLocal/msbaek_vault/000-SLIPBOX/MINE/DOCS/aggregate-design-principles-ktown4u.md` (append §5, §6)

- [ ] **Step 1: §5 본문 추가**

```markdown
## §5 Rule 4 — Single transaction per Aggregate root

> **한 줄**: 1 트랜잭션 = 1 aggregate root 변경. 2개 이상이면 event 기반 재설계.

### §5.1 Vernon의 원칙

[[Effective Aggregate Design]]:

> "잘 설계된 bounded context는 모든 경우에 하나의 트랜잭션에서 하나의 aggregate만 변경한다."

이점:
- 의도치 않은 부작용 방지 (다른 aggregate 의 lock 점유 X)
- 문서 DB (트랜잭션 미지원) 지원
- 마이크로서비스 분산 자연스러움
- Optimistic lock 단위 명확화

### §5.2 1 transaction = 1 aggregate 강제 메커니즘

[[Tactical Domain-Driven Design]] 에서 강조하는 패턴:

1. **Application Service 는 1개 repository.save() 만 호출**
2. **Repository 인터페이스는 aggregate root 단위로만 존재** (`OrderRepository` O, `OrderLineRepository` X)
3. **Domain event 는 트랜잭션 commit 후 발행** (outbox pattern)
4. **@Transactional 경계 = aggregate 변경 경계**

### §5.3 Application Service 예시

```java
// ✅ 1 transaction = 1 aggregate
@Service
@RequiredArgsConstructor
public class OrderPlacementService {
  private final OrderRepository orderRepo;
  private final CustomerRepository customerRepo;  // 조회만 (저장 X)

  @Transactional
  public OrderId placeOrder(PlaceOrderCommand cmd) {
    Customer customer = customerRepo.findById(cmd.customerId());  // 조회 OK
    customer.assertActive();  // 검증

    Order order = Order.place(cmd.customerId(), cmd.lines());  // 생성
    orderRepo.save(order);  // 1번만 save

    return order.id();
  }
}

// ❌ Anti-pattern: 한 트랜잭션에서 2개 aggregate save
@Transactional
public void placeOrderBad(PlaceOrderCommand cmd) {
  Order order = Order.place(/* ... */);
  orderRepo.save(order);

  Customer customer = customerRepo.findById(cmd.customerId());
  customer.recordOrder(order.id());      // Customer 도 변경
  customerRepo.save(customer);            // 2번째 save → Rule 4 위반

  Inventory inv = inventoryRepo.findByProductId(/* ... */);
  inv.reserve(/* ... */);
  inventoryRepo.save(inv);                // 3번째 save → 분산 lock 위험
}
```

→ Anti-pattern 은 event 기반으로 분해 (§4.4 참조).

### §5.4 Repository 인터페이스 디자인

```java
// ✅ Aggregate root 단위
public interface OrderRepository {
  Order findById(OrderId id);
  void save(Order order);
}

// ❌ Local entity 단위 (Rule 4 위반 유도)
public interface OrderLineRepository {  // 금지
  OrderLine findById(OrderLineId id);
  void save(OrderLine line);  // OrderLine 만 따로 변경 → Order invariant 깨짐
}
```

→ OrderLine 변경은 반드시 `Order.changeLine(...)` 같은 root 메서드를 통해.

### §5.5 Optimistic Locking 단위

```java
@Entity
public class Order {
  @Id private OrderId id;

  @Version  // 낙관적 락
  private long version;

  // ...
}
```

→ Order 단위로 version 관리 → 동시 변경 감지. OrderLine 만 따로 version 두지 않음.

### §5.6 ktown4u 적용 hint

ktown4u use case 검토 패턴:

| Use Case | 변경 aggregate | 1개? |
| --- | --- | --- |
| PlaceOrder | Order | ✅ 1개 |
| ConfirmPreOrder | PreOrder | ✅ 1개 (Inventory 는 event) |
| RefundOrder | Order | ✅ 1개 (Payment 환불은 event) |
| CancelOrderAndRefund | Order + Payment | ❌ 분해 필요 |

→ ❌ case는 saga 또는 event 기반 분해 (§4.4).

### §5.7 위반 시 신호

- 한 @Transactional 메서드에 `repo1.save() ... repo2.save() ... repo3.save()`
- Saga 동기 버전 도입 (대부분 aggregate 경계 잘못)
- Deadlock 발생 (여러 aggregate lock 순서 충돌)
- "이 use case 는 트랜잭션이 너무 무겁다" 라는 불만

## §6 4 Rules 결합 결정 트리

### §6.1 Aggregate 식별 결정 트리

```
새 entity X 를 발견했다. Aggregate인가?

Q1. X 가 변경될 때 보장해야 할 비즈니스 invariant 가 있는가?
├─ No → Entity 또는 ValueObject (aggregate 아님)
└─ Yes ↓

Q2. 그 invariant 가 X 단독으로 검증되는가, 다른 entity와 함께인가?
├─ X 단독 → X 자체가 작은 aggregate
└─ 다른 entity와 함께 → 함께 묶임 ↓

Q3. 같이 묶이는 entity 들은 동시에 변경되는가?
├─ Yes → 같은 aggregate (Rule 1: 가능한 작게)
└─ No (시차 허용) → 별도 aggregate + eventual consistency (Rule 3)

Q4. 외부 aggregate 와의 참조는?
├─ 같은 aggregate 내부 → memory reference
└─ 다른 aggregate → ID reference (Rule 2, ValueObject 로 감싸기)

Q5. Use case 에서 변경하는 aggregate 가 1개인가?
├─ Yes → OK (Rule 4)
└─ No → Domain event 기반으로 분해 (Rule 3)
```

### §6.2 Memory vs ID 참조 결정 (Rule 2 보조)

[[DDD-Aggregate-Reference-Memory-vs-ID]] 기반:

```
참조 대상은?
├─ 같은 aggregate root 의 child entity → Memory reference
├─ 같은 BC 의 다른 aggregate → ID reference (ValueObject)
└─ 다른 BC 의 aggregate → ID reference + ACL 변환 (다른 의미일 수 있음)
```

### §6.3 트랜잭션 분해 결정 (Rule 3·4 결합)

```
한 use case 에서 변경할 aggregate 가 N개라면?

N == 1 → 단순 @Transactional
N >= 2 → 분해:
        ├─ 첫 aggregate 만 트랜잭션
        ├─ commit 후 domain event 발행 (outbox)
        ├─ 별도 트랜잭션 (REQUIRES_NEW) 에서 다른 aggregate 처리
        └─ 비즈니스 허용 inconsistency window 명시 (§4.3)
```

### §6.4 use case 단위와 aggregate 경계

[[victor-rentea-package-by-feature-naming]] 와 결합:

```
use case 이름 (PlaceOrder, CancelOrder, RefundOrder)
    ↓
1 use case = 1 aggregate root 변경 (Rule 4)
    ↓
패키지 구조도 use case 단위
    ↓
package com.ktown4u.sales.placeorder
  ├─ PlaceOrderCommand
  ├─ PlaceOrderService
  ├─ Order (aggregate root, package-private)
  └─ OrderLine (local entity, package-private)
```

→ aggregate 가 외부에 노출되지 않음 (package-private 가시성, [[ktown4u-java-code-style]] §6.3).
```

- [ ] **Step 2: 검증**

```bash
wc -l ~/DocumentsLocal/msbaek_vault/000-SLIPBOX/MINE/DOCS/aggregate-design-principles-ktown4u.md
# Expected: ~640 lines
```

---

## Task 7: §7 ktown4u 사례 1 — Pre-order Aggregate

**Files:**
- Modify: `~/DocumentsLocal/msbaek_vault/000-SLIPBOX/MINE/DOCS/aggregate-design-principles-ktown4u.md` (append §7)

- [ ] **Step 1: §7 본문 추가**

```markdown
## §7 ktown4u 사례 1 — Pre-order Aggregate

> K-pop 신보 예약 판매 (선결제 + 발매일 동시 출고 + 수량 한정).

### §7.1 비즈니스 컨텍스트

[[bounded-context-naming]] §3 ktown4u 예시:

- Pre-order Management 는 **일반 Order 와 완전히 다른 규칙**: 선결제·발매일 일괄 배송·수량 추첨.
- 같은 BC 안에서 다음 invariant 필요:
  - 예약 수량 > 0
  - 현재 시간 < 예약 만료 시간
  - 누적 예약 수량 ≤ 최대 예약 한도

### §7.2 §6.1 결정 트리 적용

| Q | A | 결론 |
| --- | --- | --- |
| Q1: invariant 있는가? | "예약 수량 > 0 AND 만료 시간 초과 X" | Yes |
| Q2: 단독 vs 다른 entity? | PreOrder 단독 (수량·시간 자기 자신) | 단독 |
| Q3: 같이 변경? | n/a (단독) | — |
| Q4: 외부 참조? | CustomerId, ProductId | ID 참조 |
| Q5: use case 변경 aggregate? | PreOrder 만 | Rule 4 OK |

→ PreOrder 는 작은 aggregate (root + value object).

### §7.3 Aggregate 구현 ([[ktown4u-java-code-style]] 일관)

```java
package com.ktown4u.preorder;

@Getter
@Accessors(fluent = true)
@NoArgsConstructor(access = PROTECTED)
@AllArgsConstructor(access = PRIVATE)
public class PreOrder {
  private PreOrderId id;
  private CustomerId customerId;       // ID 참조 (Rule 2)
  private ProductId productId;         // ID 참조
  private int quantity;
  private LocalDateTime reservedAt;
  private LocalDateTime expiresAt;
  private PreOrderStatus status;

  // Factory Method — [[ktown4u-java-code-style]] §9
  public static PreOrder create(CustomerId customerId, ProductId productId,
                                int quantity, Duration validFor, Clock clock) {
    if (quantity <= 0) throw new IllegalArgumentException("quantity must be positive");
    LocalDateTime now = LocalDateTime.now(clock);
    return new PreOrder(
      PreOrderId.next(),
      customerId,
      productId,
      quantity,
      now,
      now.plus(validFor),
      PreOrderStatus.ACTIVE
    );
  }

  // 도메인 행위 — invariant 검증
  public void confirm(Clock clock) {
    LocalDateTime now = LocalDateTime.now(clock);
    if (now.isAfter(expiresAt)) {
      throw new PreOrderExpiredException(id);
    }
    if (status != PreOrderStatus.ACTIVE) {
      throw new IllegalStateException("cannot confirm: " + status);
    }
    this.status = PreOrderStatus.CONFIRMED;
  }

  public void cancel() {
    if (status == PreOrderStatus.CONFIRMED) {
      throw new IllegalStateException("cannot cancel confirmed pre-order");
    }
    this.status = PreOrderStatus.CANCELLED;
  }
}
```

→ `@Builder` 금지 ([[ktown4u-java-code-style]] §8) → Factory Method 사용.
→ `@NoArgsConstructor(access = PROTECTED)` 는 JPA 예외 (§9 same doc).

### §7.4 Application Service (Rule 4 준수)

```java
@Service
@RequiredArgsConstructor
public class PreOrderService {
  private final PreOrderRepository preOrderRepo;
  private final CustomerRepository customerRepo;
  private final ProductRepository productRepo;
  private final DomainEventPublisher publisher;
  private final Clock clock;

  @Transactional
  public PreOrderId reserve(ReservePreOrderCommand cmd) {
    // 1. 외부 aggregate 조회 (변경 X)
    Customer customer = customerRepo.findById(cmd.customerId());
    Product product = productRepo.findById(cmd.productId());
    customer.assertActive();
    product.assertPreOrderable();

    // 2. PreOrder 생성·저장 (1개 aggregate)
    PreOrder preOrder = PreOrder.create(
      cmd.customerId(), cmd.productId(), cmd.quantity(),
      product.preOrderValidity(), clock
    );
    preOrderRepo.save(preOrder);

    // 3. 이벤트 발행 (commit 후 Inventory 반영, Rule 3)
    publisher.publish(new PreOrderReservedEvent(
      preOrder.id(), preOrder.productId(), preOrder.quantity()
    ));

    return preOrder.id();
  }
}
```

### §7.5 Inventory 와의 Eventual Consistency

```java
@Component
@RequiredArgsConstructor
public class InventoryReservationHandler {
  private final InventoryRepository inventoryRepo;

  @EventListener
  @Transactional(propagation = REQUIRES_NEW)
  public void on(PreOrderReservedEvent event) {
    Inventory inventory = inventoryRepo.findByProductId(event.productId());
    inventory.reserve(event.quantity());  // 별도 aggregate, 별도 트랜잭션
    inventoryRepo.save(inventory);
  }
}
```

→ 도메인 합의: "Pre-order 예약 후 재고 차감 반영은 1초 이내" → eventual consistency window 명시.

### §7.6 핵심 트레이드오프

- **장점**: PreOrder lock 경합 X (Inventory 와 분리), 마이크로서비스 분리 자연스러움
- **위험**: oversell (재고 차감 전 추가 예약) → 대응:
  - 예약 한도를 PreOrder aggregate 의 invariant 로 (예: "상품당 최대 N개 활성 예약")
  - Inventory 차감 실패 시 PreOrder.cancel() 보상 이벤트
```

- [ ] **Step 2: 검증**

```bash
wc -l ~/DocumentsLocal/msbaek_vault/000-SLIPBOX/MINE/DOCS/aggregate-design-principles-ktown4u.md
# Expected: ~730 lines
```

---

## Task 8: §8 Order + OrderLine + §9 Inventory

**Files:**
- Modify: `~/DocumentsLocal/msbaek_vault/000-SLIPBOX/MINE/DOCS/aggregate-design-principles-ktown4u.md` (append §8, §9)

- [ ] **Step 1: §8 본문 추가**

```markdown
## §8 ktown4u 사례 2 — Order + OrderLine (Small Aggregate 트레이드오프)

> 일반 주문 (즉시 결제 + 즉시 배송 준비).

### §8.1 비즈니스 컨텍스트

- Order = root, OrderLine = local entity
- Invariant: "Order.totalAmount == sum(OrderLine.amount)"
- 같은 트랜잭션에서 모든 OrderLine 일관성 보장 필수

### §8.2 §6.1 결정 트리 적용

| Q | A | 결론 |
| --- | --- | --- |
| Q1: invariant 있는가? | "totalAmount == sum(lines.amount)" | Yes |
| Q2: 단독 vs 다른 entity? | OrderLine 들과 함께 | 함께 |
| Q3: 같이 변경? | Yes (라인 추가/삭제 시 totalAmount 재계산) | 같은 aggregate |
| Q4: 외부 참조? | CustomerId, ProductId | ID 참조 |
| Q5: use case 변경 aggregate? | Order 만 (Inventory·Payment 는 event) | Rule 4 OK |

→ Order(root) + OrderLine(local entity) 같은 aggregate. ktown4u 의 70% case (Vernon 통계와 일치).

### §8.3 Aggregate 구현

```java
@Getter
@Accessors(fluent = true)
@NoArgsConstructor(access = PROTECTED)
@AllArgsConstructor(access = PRIVATE)
public class Order {
  private OrderId id;
  private CustomerId customerId;
  private List<OrderLine> lines;
  private Money totalAmount;
  private OrderStatus status;
  @Version private long version;

  public static Order place(CustomerId customerId, List<OrderLineRequest> lineRequests) {
    if (lineRequests.isEmpty()) throw new IllegalArgumentException("at least 1 line");
    List<OrderLine> lines = lineRequests.stream()
      .map(OrderLine::from)
      .toList();
    Money total = lines.stream()
      .map(OrderLine::amount)
      .reduce(Money.ZERO, Money::add);
    return new Order(OrderId.next(), customerId, lines, total, OrderStatus.PLACED, 0L);
  }

  public void cancel() {
    if (status != OrderStatus.PLACED) {
      throw new IllegalStateException("cannot cancel: " + status);
    }
    this.status = OrderStatus.CANCELLED;
  }
}

@Getter
@Accessors(fluent = true)
@NoArgsConstructor(access = PROTECTED)
@AllArgsConstructor(access = PRIVATE)
public class OrderLine {  // local entity (Order 내부)
  private OrderLineId id;
  private ProductId productId;
  private Money priceSnapshot;  // 주문 시점 가격 복사
  private int quantity;
  private Money amount;

  static OrderLine from(OrderLineRequest req) {
    Money amount = req.priceSnapshot().multiply(req.quantity());
    return new OrderLine(
      OrderLineId.next(), req.productId(), req.priceSnapshot(), req.quantity(), amount
    );
  }
}
```

→ `priceSnapshot` 으로 Product 가격 변동과 독립.

### §8.4 OrderLine 을 별도 aggregate 로 분리하면 안 되는 이유

```java
// ❌ Anti-pattern
public interface OrderLineRepository {
  void save(OrderLine line);  // OrderLine 단독 변경 가능 → totalAmount invariant 깨짐
}

// 시나리오:
// 1. user A: orderLineRepo.save(line1) (quantity 변경)
// 2. user B: orderLineRepo.save(line2) (quantity 변경)
// 3. order.totalAmount 는 stale → invariant 깨짐
```

→ OrderLine 은 반드시 `Order.changeLine(lineId, ...)` 메서드를 통해 변경. `OrderLineRepository` 없음.

### §8.5 ktown4u 트레이드오프: OrderLine 이 매우 많아지면?

- 일반 e-commerce: order line 10~50개 정도. Small aggregate 유지 OK.
- ktown4u 특수: 콘서트 굿즈 단체 주문 (한 주문에 100~500 라인) 가능
- 대응 옵션:
  - **Option A**: 같은 Order 유지 + lazy loading + paging API → 복잡
  - **Option B**: 큰 주문은 별도 BC (Bulk Order Management) → Aggregate 경계 재설계
  - **Option C**: BulkOrder = root, OrderBatch (별도 aggregate) → eventual consistency

→ **default 는 Option A 유지**, 실제 throughput 이슈 발견 시 B/C 검토.

### §8.6 Application Service

```java
@Service
@RequiredArgsConstructor
public class OrderPlacementService {
  private final OrderRepository orderRepo;
  private final CustomerRepository customerRepo;
  private final ProductRepository productRepo;
  private final DomainEventPublisher publisher;

  @Transactional
  public OrderId placeOrder(PlaceOrderCommand cmd) {
    Customer customer = customerRepo.findById(cmd.customerId());
    customer.assertActive();

    // Product 가격 스냅샷 조회 (저장 X)
    List<OrderLineRequest> lineRequests = cmd.lines().stream()
      .map(line -> {
        Product product = productRepo.findById(line.productId());
        return new OrderLineRequest(line.productId(), product.currentPrice(), line.quantity());
      })
      .toList();

    Order order = Order.place(cmd.customerId(), lineRequests);
    orderRepo.save(order);

    publisher.publish(new OrderPlacedEvent(order.id(), order.lines()));
    return order.id();
  }
}
```

## §9 ktown4u 사례 3 — Inventory 차감/예약 (Eventual Consistency 영역)

> 재고 = 가용수량 + 예약수량.

### §9.1 비즈니스 컨텍스트

- Pre-order 예약, 일반 Order 결제 모두 Inventory 에 영향
- 모든 차감을 강한 일관성으로 묶으면 lock 경합 폭증
- 도메인 합의: "재고 반영은 1초 이내" → eventual consistency

### §9.2 §6.1 결정 트리 적용

| Q | A | 결론 |
| --- | --- | --- |
| Q1: invariant 있는가? | "가용수량 >= 0", "가용수량 + 예약수량 == 총수량" | Yes |
| Q2: 단독 vs? | Inventory 단독 (수량 자기 자신) | 단독 |
| Q3: 같이 변경? | n/a | — |
| Q4: 외부 참조? | ProductId | ID 참조 |
| Q5: use case 변경 aggregate? | Inventory 만 (Order 는 event source) | Rule 4 OK |

→ Inventory 단독 aggregate.

### §9.3 Aggregate 구현

```java
@Getter
@Accessors(fluent = true)
@NoArgsConstructor(access = PROTECTED)
@AllArgsConstructor(access = PRIVATE)
public class Inventory {
  private InventoryId id;
  private ProductId productId;
  private int availableQuantity;
  private int reservedQuantity;
  @Version private long version;

  public static Inventory create(ProductId productId, int initialQuantity) {
    if (initialQuantity < 0) throw new IllegalArgumentException("quantity must be non-negative");
    return new Inventory(InventoryId.next(), productId, initialQuantity, 0, 0L);
  }

  public void reserve(int quantity) {
    if (quantity <= 0) throw new IllegalArgumentException("quantity must be positive");
    if (availableQuantity < quantity) {
      throw new InsufficientInventoryException(productId, availableQuantity, quantity);
    }
    this.availableQuantity -= quantity;
    this.reservedQuantity += quantity;
  }

  public void confirm(int quantity) {
    if (reservedQuantity < quantity) {
      throw new IllegalStateException("not enough reserved");
    }
    this.reservedQuantity -= quantity;
  }

  public void release(int quantity) {  // 예약 취소
    if (reservedQuantity < quantity) {
      throw new IllegalStateException("not enough reserved");
    }
    this.reservedQuantity -= quantity;
    this.availableQuantity += quantity;
  }
}
```

→ `@Version` 으로 optimistic lock. 동시 차감 시 충돌 감지 → 재시도.

### §9.4 Event Handler (별도 트랜잭션)

```java
@Component
@RequiredArgsConstructor
public class InventoryHandler {
  private final InventoryRepository inventoryRepo;

  @EventListener
  @Transactional(propagation = REQUIRES_NEW)
  public void on(OrderPlacedEvent event) {
    for (OrderLine line : event.lines()) {
      Inventory inventory = inventoryRepo.findByProductId(line.productId());
      inventory.reserve(line.quantity());
      inventoryRepo.save(inventory);
    }
  }

  @EventListener
  @Transactional(propagation = REQUIRES_NEW)
  public void on(OrderCancelledEvent event) {
    for (OrderLine line : event.lines()) {
      Inventory inventory = inventoryRepo.findByProductId(line.productId());
      inventory.release(line.quantity());  // 보상 이벤트
      inventoryRepo.save(inventory);
    }
  }
}
```

→ Order 와 Inventory 가 독립 트랜잭션 → Rule 4 준수.

### §9.5 핵심 트레이드오프

- **장점**: Inventory 와 Order 가 lock 경합 X, 마이크로서비스 분리 자연스러움
- **위험**: oversell (Order 트랜잭션 commit ~ Inventory 차감 사이) → 대응:
  - Inventory.reserve() 실패 시 OrderCancellationCompensator 가 Order.cancel() 호출
  - 비즈니스 합의: "수 ms 이내 oversell 가능, 자동 환불 + 사과 메일"
  - 또는 Pre-order 단계에서 한도 invariant 로 사전 차단
```

- [ ] **Step 2: 검증**

```bash
wc -l ~/DocumentsLocal/msbaek_vault/000-SLIPBOX/MINE/DOCS/aggregate-design-principles-ktown4u.md
# Expected: ~880 lines
```

---

## Task 9: §10 Anti-pattern 카탈로그 + 체크리스트

**Files:**
- Modify: `~/DocumentsLocal/msbaek_vault/000-SLIPBOX/MINE/DOCS/aggregate-design-principles-ktown4u.md` (append §10)

- [ ] **Step 1: §10 본문 추가**

```markdown
## §10 Anti-pattern 카탈로그 + 체크리스트

### §10.1 7가지 Anti-pattern

#### 1. Enormous Aggregate (Rule 1 위반)

증상: 한 aggregate 에 5+ entity, 12+ 필드, lazy loading 남발.
원인: "관련 있어 보여서" 묶음. invariant 분석 부재.
처방: §6.1 Q3 으로 "같이 변경되는가?" 재검토. 분리 후 event 기반.

#### 2. Direct External Reference (Rule 2 위반)

증상: `Order.customer` (Customer 전체 객체).
원인: ORM 의 `@ManyToOne` 자동 매핑 의존.
처방: `CustomerId customerId` 로 교체. Application Service 에서 조합.

#### 3. Primitive Obsession (Rule 2 보강)

증상: `private Long customerId; private Long productId;` (raw Long).
원인: ValueObject 만드는 비용 회피.
처방: `record CustomerId(long value) {}` 식 typed ID. Java record 로 boilerplate 최소화.

#### 4. Saga of Many Aggregates (Rule 3, 4 위반)

증상: 한 use case 에서 5개 aggregate 동기 변경.
원인: 강한 일관성 집착.
처방: 도메인 전문가에게 "허용 inconsistency window" 질문. Event 기반 분해.

#### 5. Cross-Aggregate Transaction (Rule 4 위반)

증상: 한 @Transactional 메서드에 `repo1.save() ... repo2.save() ...`.
원인: "한 번에 다 끝내자" 사고.
처방: 첫 aggregate 만 트랜잭션 + 나머지는 event. Outbox pattern.

#### 6. Eventual Consistency Without Window (Rule 3 보강)

증상: "eventual" 만 말하고 허용 window 미정의.
원인: 도메인 전문가 인터뷰 누락.
처방: 비즈니스에 "1초? 1분? 1일?" 질문. 문서화.

#### 7. Aggregate Where Entity Suffices (Coopman/Verschatse)

증상: 모든 복잡한 entity 를 aggregate 로 모델링.
원인: "복잡함 = aggregate" 오해.
처방: §6.1 Q1 으로 "비즈니스 invariant 가 실제 있는가?" 확인. 없으면 entity 또는 VO.

### §10.2 코드 리뷰 체크리스트

새 aggregate 또는 use case 리뷰 시:

#### 설계 차원

- [ ] 이 aggregate 의 **invariant 가 명시되어 있는가?** (코드 주석 또는 docstring)
- [ ] 70% 의 Vernon 통계처럼 **root + value object 만으로 충분한가?** (composite 필요성 명백한가?)
- [ ] 외부 aggregate 참조가 **모두 ID (ValueObject) 인가?** (raw Long 없음)
- [ ] 변경 use case 당 **변경 aggregate 가 정확히 1개인가?**
- [ ] 2+ aggregate 변경이 필요하면 **domain event 로 분해되었는가?**

#### 코드 차원

- [ ] **Factory Method** (`create`/`from`/`of`/`restore`) 사용, `new` 직접 호출 또는 `@Builder` 없음 ([[ktown4u-java-code-style]] §8, §9)
- [ ] **`@NoArgsConstructor(access = PROTECTED)`** + `@AllArgsConstructor(access = PRIVATE)` 조합 (JPA 예외)
- [ ] **`@Getter @Accessors(fluent = true)`** (Lombok 3종 세트, [[ktown4u-java-code-style]] §1)
- [ ] **`@Version`** 으로 optimistic lock 적용
- [ ] **Repository 가 aggregate root 단위만** (local entity repo 금지)
- [ ] **Application Service 가 정확히 1개 repository.save() 호출**
- [ ] **`@Transactional` 메서드에서 외부 aggregate 변경 없음** (조회만 OK)

#### Event 차원

- [ ] Domain event 가 **트랜잭션 commit 후** 발행 (outbox 권장)
- [ ] Event handler 가 **`REQUIRES_NEW`** 별도 트랜잭션
- [ ] **허용 inconsistency window** 가 비즈니스와 합의·문서화
- [ ] At-least-once + **idempotent receiver** (eventId 기반 중복 제거)
- [ ] **보상 이벤트** (Cancellation, Refund 등) 설계

### §10.3 위반 발견 시 대응 우선순위

1. **Critical**: Rule 4 위반 (한 트랜잭션 다중 aggregate) → 즉시 분해 (deadlock 위험)
2. **High**: Rule 2 위반 (direct reference) → 다음 sprint 내 ID 참조로 교체
3. **Medium**: Rule 1 위반 (거대 aggregate) → 다음 분기 내 분리 plan
4. **Low**: 명명·VO 누락 → 다음 touch 시 정리
```

- [ ] **Step 2: 검증**

```bash
wc -l ~/DocumentsLocal/msbaek_vault/000-SLIPBOX/MINE/DOCS/aggregate-design-principles-ktown4u.md
# Expected: ~960 lines
```

---

## Task 10: §11 Cross-reference + Related Notes 자동 주입

**Files:**
- Modify: `~/DocumentsLocal/msbaek_vault/000-SLIPBOX/MINE/DOCS/aggregate-design-principles-ktown4u.md` (append §11 + Related Notes section)

- [ ] **Step 1: §11 Cross-reference 본문 추가**

```markdown
## §11 Cross-reference

자매 SSOT 문서와의 관계:

- [[bounded-context-naming]] — Aggregate 가 모이는 BC 식별. §3 Q4 (같은 명사 다른 의미: Sales Customer vs Shipping Prospect) 가 Rule 2 ID 참조와 결합.
- [[bounded-context-separation-principles]] — BC 분리 ≠ Aggregate 분리. BC 횡단 eventual consistency 가 Rule 3 의 대규모 적용.
- [[victor-rentea-package-by-feature-naming]] — Use case 단위 패키지 = 1 aggregate root 변경 (Rule 4). Package-private 가시성으로 aggregate root 만 진짜 public.
- [[ktown4u-java-code-style]] — Aggregate 구현 시 Record + Lombok / Factory Method (`create`/`from`/`of`/`restore`) / `@Builder` 금지 / `@Version` 으로 optimistic lock.
- [[spring-boot-project-standards-ktown4u]] — Repository 패턴 (aggregate root 단위), `@Transactional` 경계, outbox pattern 구현 가이드.

### Vernon 원전 & vault 자료

- [[Effective Aggregate Design]] — Vernon 원전 (4 rules 본문, 금융 시스템 70% 통계의 원천)
- [[DDD-Aggregate-Reference-Memory-vs-ID]] — Rule 2 ID 참조 결정 트리 보강
- [[Aggregates-An In-depth Examination by Thomas Coopman Gien Verschatse - DDD Europe]] — "복잡한 entity = aggregate" 오해 반박, 도메인 인터뷰 필수
- [[Tactical Domain-Driven Design]] — invariant enforcement, optimistic locking 세부
- [[What is a DDD Aggregate]] — 정의, root 책임, anti-pattern 카탈로그
```

- [ ] **Step 2: obsidian-forward-related-injector sub-agent 호출로 Related Notes 자동 추가**

```
Agent({
  description: "Aggregate SSOT Related Notes 주입",
  subagent_type: "obsidian-forward-related-injector",
  prompt: "Inject Related Notes for: /Users/msbaek/DocumentsLocal/msbaek_vault/000-SLIPBOX/MINE/DOCS/aggregate-design-principles-ktown4u.md

Constraints:
- §11 Cross-reference 와 frontmatter related: 에 이미 포함된 wikilink 5개 ([[bounded-context-naming]], [[bounded-context-separation-principles]], [[victor-rentea-package-by-feature-naming]], [[ktown4u-java-code-style]], [[spring-boot-project-standards-ktown4u]]) + Vernon 원전 5개 ([[Effective Aggregate Design]], [[DDD-Aggregate-Reference-Memory-vs-ID]], [[Aggregates-An In-depth Examination by Thomas Coopman Gien Verschatse - DDD Europe]], [[Tactical Domain-Driven Design]], [[What is a DDD Aggregate]]) 는 **제외**
- vis hybrid search top-10 에서 위 10개를 빼고 상위 5개 추가
- Related Notes 섹션은 §11 다음에 (문서 마지막)"
})
```

- [ ] **Step 3: 검증**

```bash
wc -l ~/DocumentsLocal/msbaek_vault/000-SLIPBOX/MINE/DOCS/aggregate-design-principles-ktown4u.md
# Expected: ~1000 lines
grep -c "^## " ~/DocumentsLocal/msbaek_vault/000-SLIPBOX/MINE/DOCS/aggregate-design-principles-ktown4u.md
# Expected: 12 (§0~§11)
grep -c "^- \[\[" ~/DocumentsLocal/msbaek_vault/000-SLIPBOX/MINE/DOCS/aggregate-design-principles-ktown4u.md | head -1
# Expected: Related Notes 5개 추가 확인
```

---

## Task 11: backlog 갱신 + commit + 보고

**Files:**
- Modify: `~/DocumentsLocal/msbaek_vault/000-SLIPBOX/MINE/DOCS/ai-agent-guides-backlog.md`

- [ ] **Step 1: backlog "이미 작성된 문서" 5 → 6 갱신**

frontmatter 직후 또는 첫 섹션에서 "현재 5개" 문구를 "현재 6개"로 변경하고 항목 추가:

```markdown
- [[aggregate-design-principles-ktown4u]] — DDD Aggregate 4 rules (Vernon) + ktown4u Pre-order/Order/Inventory 사례
```

- [ ] **Step 2: §A 1번 항목 ✅ 처리**

```markdown
- ✅ **[[aggregate-design-principles-ktown4u]]** — Vaughn Vernon 4 rules (small / ID 참조 / eventual consistency / 단일 트랜잭션) + Pre-order·Order·Inventory 사례
```

- [ ] **Step 3: Top 5 재정렬 (Aggregate ✅ 후 한 칸씩 승격)**

```markdown
| 순서  | 문서                                                     | 카테고리       | 근거                                                                                                                                                |
| --- | ------------------------------------------------------ | ---------- | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | **6 팀 아키텍처 패턴 결정 트리**                                  | F (**S2**) | 별도 트랙이지만 Claude Code 활용 ROI 최고                                                                                |
| 2   | **Blame Command 패턴 — Behavioral Reset Slash Commands** | G (**S3**) | 메타-혁신, 즉시 활용 가능 + CLAUDE.md 룰 강제 메커니즘                                                       |
| 3   | **Domain Event 설계 + ACL 통합 패턴**                        | A          | Aggregate 다음 자연 후속, BC 간 결합 줄이는 핵심 패턴                                                                                                             |
| 4   | **Test List + Walking Skeleton 단계**                    | C          | 이미 작성된 가이드 6개를 묶는 *프로세스* 메타 가이드                                                  |
| 5   | **Value Object vs Entity 결정 트리**                       | A          | Aggregate 다음 자연 후속, Equality·Immutability·Composition                                                                                              |
```

- [ ] **Step 4: footer 갱신**

```markdown
> [[aggregate-design-principles-ktown4u]] 작성 완료 (Top 1 ✅ — Vernon 4 rules + ktown4u 3사례 + 7 anti-pattern + 체크리스트).
```

- [ ] **Step 5: git status 확인**

```bash
cd ~/DocumentsLocal/msbaek_vault && git status --short -- 000-SLIPBOX/MINE/DOCS/
# Expected: 
#   ?? 000-SLIPBOX/MINE/DOCS/aggregate-design-principles-ktown4u.md  (자동 백업 cron 이 이미 잡았으면 없음)
#    M 000-SLIPBOX/MINE/DOCS/ai-agent-guides-backlog.md
```

- [ ] **Step 6: Korean-safe commit (temp 파일 + -F)**

```bash
cat > /tmp/commit-msg-aggregate.txt << 'EOF_DUMMY'
docs(slipbox): Aggregate Design Principles SSOT 신규 + backlog Top 1 ✅

- 신규: aggregate-design-principles-ktown4u.md (~1000 lines, Vernon 4 rules + ktown4u 3 사례 + 7 anti-pattern + 체크리스트)
- 갱신: ai-agent-guides-backlog.md (§A 1번 ✅, Top 5 재정렬, "이미 작성된 문서" 6개로)
EOF_DUMMY
# 위는 heredoc 회피 위해 실제로는 Write 도구로 temp 파일 생성
cd ~/DocumentsLocal/msbaek_vault && git add 000-SLIPBOX/MINE/DOCS/ && git commit -F /tmp/commit-msg-aggregate.txt && rm /tmp/commit-msg-aggregate.txt
```

- [ ] **Step 7: 사용자 최종 보고**

한국어로:
- 신규 파일 라인 수, §0~§11 구조
- backlog 갱신 요약 (Top 1 ✅, 새 Top 1 = 6 팀 아키텍처 패턴 결정 트리)
- Related Notes 5개 후보
- 다음 추천 작성 후보 확인

---

## Self-Review

**1. Spec coverage 확인:**
- ✅ Rule 1 Small Aggregate (Task 3)
- ✅ Rule 2 Reference by ID (Task 4)
- ✅ Rule 3 Eventual Consistency (Task 5)
- ✅ Rule 4 Single transaction (Task 6 §5)
- ✅ vault 5개 자료 [[wikilink]] 흡수 (Task 1 매핑 표 + 각 task 본문 + Task 10 cross-ref)
- ✅ ktown4u Pre-order/Order/Inventory 사례 (Task 7, 8 §8, 8 §9)
- ✅ ktown4u-java-code-style 일관성 (@Builder 금지, Factory Method, Lombok 3종 — Task 7~9 코드 예시)
- ✅ 결정 트리 (Task 6 §6) / 안티패턴 (Task 9 §10) / 체크리스트 (Task 9 §10.2)
- ✅ 자매 문서 cross-link (Task 10 §11)
- ✅ backlog 갱신 (Task 11)

**2. Placeholder scan:** 없음. 모든 코드 블록 완성, 모든 검증 명령 expected output 포함.

**3. Type consistency:** 
- `PreOrder` / `Order` / `OrderLine` / `Inventory` aggregate root 일관
- `CustomerId` / `ProductId` / `OrderId` / `PreOrderId` / `InventoryId` / `OrderLineId` VO ID 일관
- `Money` VO 일관
- Lombok 어노테이션 조합 (`@Getter @Accessors(fluent=true) @NoArgsConstructor(access=PROTECTED) @AllArgsConstructor(access=PRIVATE) @Version`) 일관

---

## Source → Section Mapping

| vault 자료 ([[wikilink]]) | 활용 섹션 | 어떻게 흡수 |
| --- | --- | --- |
| [[Effective Aggregate Design]] | §1, §2, §3, §4, §5 | Vernon 원전 4 rules 본문, 금융 시스템 70% 통계 |
| [[DDD-Aggregate-Reference-Memory-vs-ID]] | §3, §6 | Memory vs ID 결정 트리 (Rule 2 보강), ValueObject 감싸기 패턴 |
| [[Aggregates-An In-depth Examination by Thomas Coopman Gien Verschatse - DDD Europe]] | §1, §10 | "복잡한 entity = aggregate" 오해 반박, 불변식·동시성 실제 필요할 때만 |
| [[Tactical Domain-Driven Design]] | §5, §6 | optimistic locking, invariant enforcement 책임 분리 |
| [[What is a DDD Aggregate]] | §1, §10 | 정의·invariant root 책임, anti-pattern 예시 |
| [[ktown4u-java-code-style]] | §7, §8, §9 | Record + Lombok 3종 세트, Factory Method 4종, @Builder 금지 |
| [[bounded-context-naming]] | §3, §11 | BC 간 ID 참조 시 같은 명사 다른 의미 (Sales Customer vs Shipping Prospect) |
| [[bounded-context-separation-principles]] | §4, §11 | BC 분리 = aggregate 분리 != 동일, eventual consistency BC 횡단 패턴 |
| [[victor-rentea-package-by-feature-naming]] | §6, §11 | use case 단위 = 단일 aggregate root 변경 단위 |
| [[spring-boot-project-standards-ktown4u]] | §7, §11 | persistence 경계, repository 패턴 |

## 4 Rules 카드 (각 섹션 헤더로 재사용)

- **Rule 1 — Small Aggregate**: 불변식이 요구하는 최소 범위로 제한. 70% 사례는 root + value object만.
- **Rule 2 — Reference by ID**: 경계 외부 객체는 ValueObject로 감싼 ID로만 참조. Memory reference는 같은 aggregate 내부에서만.
- **Rule 3 — Eventual Consistency outside boundary**: aggregate 경계를 넘는 규칙은 domain event + 명시적 inconsistency window (초 vs 일).
- **Rule 4 — Single transaction per Aggregate root**: 1 트랜잭션 = 1 aggregate root 변경. 2개 이상이면 event 기반 재설계.
