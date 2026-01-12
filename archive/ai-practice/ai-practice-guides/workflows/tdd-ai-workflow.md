# TDD + AI 통합 워크플로우

**생성일**: 2026-01-04
**목적**: TDD와 AI를 결합한 효과적인 개발 방법론

---

## 개요

TDD(Test-Driven Development)와 AI를 결합하면 **개발자의 의도**와 **AI의 생산성**을 모두 활용할 수 있습니다.

> "테스트는 인간이, 구현은 AI가, 리팩토링은 함께"

---

## Red-Green-Refactor + AI 역할

```
┌─────────────────────────────────────────────────────────────────┐
│                     TDD + AI 사이클                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   ┌───────────┐         ┌───────────┐         ┌───────────┐    │
│   │    RED    │────────▶│   GREEN   │────────▶│   BLUE    │    │
│   │ (개발자)   │         │   (AI)    │         │ (AI+개발자) │    │
│   └───────────┘         └───────────┘         └───────────┘    │
│        │                      │                      │          │
│        ▼                      ▼                      ▼          │
│   실패하는 테스트         최소 구현              리팩토링        │
│   작성                  테스트 통과            코드 개선        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Phase 1: Red (개발자 주도)

**왜 개발자가 직접 테스트를 작성하나?**
- 테스트는 **의도**를 표현
- 요구사항을 **실행 가능한 형태**로 변환
- **설계 결정**을 미리 내림
- AI가 **올바른 방향**으로 가도록 가이드

**테스트 작성 원칙:**
```java
@Test
void shouldCalculateDiscountForPremiumMember() {
    // Given - 명확한 전제 조건
    Member member = new PremiumMember("user123");
    Order order = new Order(items, 100_000);

    // When - 테스트할 행동
    int discount = discountService.calculate(member, order);

    // Then - 기대 결과
    assertThat(discount).isEqualTo(10_000); // 10% 할인
}
```

**테스트 네이밍:**
- `should[기대결과]When[조건]`
- `given[상황]When[행동]Then[결과]`

### Phase 2: Green (AI 주도)

**AI에게 구현 요청:**
```markdown
다음 테스트가 통과하도록 구현해줘:

```java
@Test
void shouldCalculateDiscountForPremiumMember() {
    // Given
    Member member = new PremiumMember("user123");
    Order order = new Order(items, 100_000);

    // When
    int discount = discountService.calculate(member, order);

    // Then
    assertThat(discount).isEqualTo(10_000);
}
```

**규칙:**
- 이 테스트만 통과시켜줘
- 기존 테스트를 수정하지 마
- 최소한의 코드로 구현해
- 하드코딩으로 시작해도 좋아
```

**AI 응답 예시:**
```java
public class DiscountService {
    public int calculate(Member member, Order order) {
        if (member instanceof PremiumMember) {
            return order.getAmount() / 10; // 10% 할인
        }
        return 0;
    }
}
```

### Phase 3: Blue (협업)

**리팩토링 요청:**
```markdown
테스트가 통과하니, 리팩토링을 제안해줘.

고려할 점:
1. 할인 정책이 추가될 수 있어 (실버, 골드, VIP 등)
2. 계절 할인, 쿠폰 할인도 고려해야 해
3. 할인 정책 변경 시 코드 수정 최소화

OCP(개방-폐쇄 원칙)를 적용해줘.
```

**AI 제안 검토 후 적용:**
```java
// 할인 전략 패턴 적용
public interface DiscountPolicy {
    int calculate(Member member, Order order);
    boolean supports(Member member);
}

public class PremiumDiscountPolicy implements DiscountPolicy {
    @Override
    public int calculate(Member member, Order order) {
        return order.getAmount() / 10;
    }

    @Override
    public boolean supports(Member member) {
        return member instanceof PremiumMember;
    }
}
```

---

## Spec-First 접근법

### 왜 Spec-First인가?

> "코드는 Specification의 손실 압축이다"

프롬프트나 대화 대신 **명세서**를 먼저 작성:
- 모호함 제거
- 팀 전체가 공유 가능
- 버전 관리 가능
- AI가 더 정확하게 이해

### Specification 작성 예시

```markdown
# 할인 시스템 명세서

## 기능 개요
회원 등급과 주문 금액에 따라 할인을 계산합니다.

## 요구사항

### R1: 등급별 할인율
| 등급 | 할인율 |
|------|--------|
| Premium | 10% |
| Gold | 7% |
| Silver | 5% |
| Basic | 0% |

### R2: 최소 주문 금액
- 50,000원 이상 주문 시에만 할인 적용

### R3: 최대 할인 금액
- 최대 할인 금액은 30,000원

### 예시 케이스

| 케이스 | 등급 | 주문금액 | 기대 할인 |
|--------|------|----------|-----------|
| 1 | Premium | 100,000 | 10,000 |
| 2 | Premium | 40,000 | 0 (최소금액 미달) |
| 3 | Premium | 500,000 | 30,000 (최대할인 제한) |
| 4 | Basic | 100,000 | 0 |
```

### Spec → Test → Implementation

```markdown
이 명세서를 기반으로 테스트 케이스 목록을 작성해줘.
우선순위:
1. Happy path (기본 케이스)
2. Edge cases (경계값)
3. Error cases (예외 상황)
```

---

## AI 생성 코드 검증 체크리스트

### 1. 기능 검증
- [ ] 모든 테스트가 통과하는가?
- [ ] 엣지 케이스가 처리되었는가?
- [ ] 에러 처리가 적절한가?

### 2. 품질 검증
- [ ] 코드가 읽기 쉬운가?
- [ ] SOLID 원칙을 따르는가?
- [ ] 중복이 없는가?
- [ ] 메서드가 적절한 크기인가?

### 3. 보안 검증
- [ ] 입력 검증이 있는가?
- [ ] SQL Injection 가능성은?
- [ ] XSS 가능성은?
- [ ] 민감 정보 노출은?

### 4. 성능 검증
- [ ] 불필요한 반복이 없는가?
- [ ] N+1 쿼리 문제는?
- [ ] 메모리 누수 가능성은?

### 5. 테스트 품질
- [ ] 테스트가 의도를 명확히 표현하는가?
- [ ] 테스트가 독립적인가?
- [ ] 테스트가 빠른가?
- [ ] 테스트가 결정적인가?

---

## 실전 예제 (Spring Boot)

### 시나리오: 주문 할인 기능 구현

#### Step 1: Spec 작성
```markdown
# 주문 할인 기능 명세

## 기능
- 회원 등급에 따른 할인 적용
- 쿠폰 적용
- 최종 결제 금액 계산

## API
POST /api/orders/{orderId}/discount
Request: { "couponCode": "SPRING2024" }
Response: { "originalAmount": 100000, "discountAmount": 15000, "finalAmount": 85000 }
```

#### Step 2: 첫 번째 테스트 (Red)
```java
@Test
void shouldApplyMemberDiscountToOrder() {
    // Given
    Order order = Order.builder()
        .id(1L)
        .memberId(100L)
        .amount(100_000)
        .build();

    given(memberService.findById(100L))
        .willReturn(new PremiumMember(100L));

    // When
    DiscountResult result = discountService.apply(order);

    // Then
    assertThat(result.getDiscountAmount()).isEqualTo(10_000);
    assertThat(result.getFinalAmount()).isEqualTo(90_000);
}
```

#### Step 3: 구현 요청 (Green)
```markdown
위 테스트가 통과하도록 DiscountService를 구현해줘.

프로젝트 구조:
- domain/: 도메인 객체
- application/: 서비스
- infrastructure/: 리포지토리

규칙:
- 도메인 로직은 도메인 객체에
- 서비스는 조율만
```

#### Step 4: 추가 테스트 (Red)
```java
@Test
void shouldApplyCouponDiscount() { ... }

@Test
void shouldApplyBothMemberAndCouponDiscount() { ... }

@Test
void shouldNotExceedMaxDiscount() { ... }
```

#### Step 5: 삼각측량으로 일반화
```markdown
다음 테스트들이 모두 통과하도록 구현을 일반화해줘:

[테스트 목록]

할인 정책을 전략 패턴으로 분리하고,
새로운 할인 정책을 쉽게 추가할 수 있게 해줘.
```

#### Step 6: 리팩토링 (Blue)
```markdown
테스트가 모두 통과하니, 다음 관점에서 리팩토링해줘:

1. 할인 계산 로직을 도메인 객체로 이동
2. 가독성 개선
3. 테스트 코드 중복 제거

각 변경에 대해 이유를 설명해줘.
```

---

## TPP (Transformation Priority Premise)

AI와 작업할 때도 TPP를 적용하면 더 안정적인 코드를 얻을 수 있습니다.

### 변환 우선순위 (낮음 → 높음)

1. `{}→nil` - 코드 없음 → nil 반환
2. `nil→constant` - nil → 상수 반환
3. `constant→constant+` - 상수 → 더 복잡한 상수
4. `constant→scalar` - 상수 → 변수
5. `statement→statements` - 단일 문장 → 여러 문장
6. `unconditional→if` - 무조건 → 조건문
7. `scalar→collection` - 스칼라 → 컬렉션
8. `collection→complex` - 컬렉션 → 더 복잡한 구조

### AI에게 TPP 적용 요청
```markdown
이 테스트 목록을 TPP에 따라 순서대로 구현해줘:

1. shouldReturnZeroForEmptyList - nil 반환
2. shouldReturnSingleElementSum - 상수
3. shouldReturnTwoElementSum - 스칼라
4. shouldReturnMultipleElementSum - 반복문

각 단계에서 최소한의 변환만 해줘.
```

---

## 주의사항

### AI가 할 수 있는 것
- 테스트를 통과하는 구현
- 리팩토링 제안
- 엣지 케이스 발견
- 패턴 적용

### AI가 할 수 없는 것
- 비즈니스 요구사항 이해
- 아키텍처 결정
- 테스트 의도 파악
- 도메인 지식

### 안티패턴

❌ **AI에게 테스트 작성 요청**
```markdown
이 기능에 대한 테스트를 작성해줘
```

✅ **올바른 접근**
```markdown
내가 작성한 이 테스트가 통과하도록 구현해줘
```

❌ **한 번에 모든 것 요청**
```markdown
사용자 인증 시스템 전체를 구현해줘
```

✅ **올바른 접근**
```markdown
첫 번째 테스트: 유효한 사용자 로그인
이 테스트만 통과시켜줘
```

---

## 참고 자료

- [Kent Beck - Test-Driven Development](https://www.amazon.com/Test-Driven-Development-Kent-Beck/dp/0321146530)
- [Transformation Priority Premise](https://blog.cleancoder.com/uncle-bob/2013/05/27/TheTransformationPriorityPremise.html)
- [TDD in the Age of AI](https://martinfowler.com/articles/tdd-ai.html)
