# TDD 주제별 정리

**생성일**: 2025-08-20  
**총 수집 문서**: 25개+  
**주요 키워드**: TDD, Test Driven Development, Unit Test, Refactoring

## 📚 주요 주제 분류

### 1. TDD 기본 개념 및 원리

#### TDD 정의와 역사
- **TDD 정의**: Kent Beck이 제시한 Test-Driven Design/Development
- **핵심 사이클**: Red-Green-Refactor
- **기본 원칙**: Test First Development

#### 주요 참고 문서
- `003-RESOURCES/TDD/2022-패캠-이너써클/1.TDD/1. TDD.md` - TDD 기본 정의
- `003-RESOURCES/TDD/Did Kent Beck REALLY Invent TDD?.md` - Kent Beck의 TDD 발명 과정
- `notes/dailies/2025-04-20.md` - TDD와 리팩토링의 원칙 및 기법

### 2. TDD 실습 및 워크샵

#### Tennis Game TDD
- **Outside-In TDD 접근법**: 바깥쪽부터 안쪽으로 테스트 작성
- **Unit Test vs Integration Test**: 클래스나 함수 단위의 기대 동작 확인

#### 실습 자료
- `003-RESOURCES/TDD/2022-패캠-이너써클/2.Tennis Game TDD/2. Outside-In TDD for Tennis Game.md`
- `003-RESOURCES/TDD/Working-TDD-Workshop/TDD-Cases.md` - TDD 실습 케이스들
- `003-RESOURCES/TDD/Working-TDD-Workshop/tdd-refactoring-index.md` - TDD 리팩토링 인덱스

### 3. TDD의 일반적인 오해와 문제점

#### Ian Cooper의 TDD 재검토
- **일반적인 오해**: 모든 메서드를 테스트해야 한다는 잘못된 인식
- **올바른 접근**: 동작(Behavior) 중심 테스트, 구현 세부사항 테스트 지양
- **Mock 사용의 문제점**: 내부 구조에 과도하게 결합되는 문제

#### 관련 문서
- `003-RESOURCES/TDD/Misunderstanding/TDD Revisited - Ian Cooper - NDC Porto 2023.md`
- `003-RESOURCES/TDD/Misunderstanding/TDD, Where Did It All Go Wrong (Ian Cooper).md`

### 4. BDD (Behavior Driven Development)

#### BDD vs TDD
- **BDD**: 행동 중심 개발, 사용자 스토리와 시나리오 중심
- **Given-When-Then 패턴**: 테스트 시나리오 구조화

#### 참고 자료
- `997-BOOKS/clean-coders-codecasts/35.behavior driven development.md`

### 5. TDD와 DDD 통합

#### Domain-Driven Design과의 결합
- **Live Coding 예제**: Chris Simon의 TDD & DDD 라이브 코딩
- **도메인 모델링과 테스트**: 비즈니스 로직을 중심으로 한 테스트 설계

#### 관련 문서
- `003-RESOURCES/TDD/RAW/TDD & DDD from the Ground Up Live Coding by Chris Simon.md`

### 6. TDD와 리팩토링

#### Preparatory Refactoring in TDD
- **사전 리팩토링**: 새 기능 추가 전 코드 구조 개선
- **Red-Green-Refactor 사이클**: 리팩토링이 TDD의 핵심 단계

#### 관련 자료
- `003-RESOURCES/REFACTORING/EXAMPLES/Design Better Code with Preparatory Refactoring in TDD.md`
- `997-BOOKS/클린 애자일(Back to Basics).md` - Clean Agile과 리팩토링

### 7. 테스트 종류와 분류

#### TDD 관련 테스트 유형
- **Programmer Test / Developer Test**: 개발자가 작성하는 모든 테스트
- **Unit Test**: 모듈, 클래스, 메서드 등 작은 단위 테스트
- **Integration Test**: 컴포넌트 간 상호작용 테스트

#### 참고 문서
- `003-RESOURCES/TDD/Test 종류.md` - 다양한 테스트 유형 정리

### 8. Clean Code와 TDD

#### Clean Coders Codecasts
- **Test Design Study**: 테스트 설계 연구
- **Test Process**: 테스트 프로세스 이해
- **Uncle Bob의 교육 시리즈**: Clean Code와 TDD 통합 접근

#### 관련 자료
- `997-BOOKS/clean-coders-codecasts/21.test_design_study.md`
- `997-BOOKS/clean-coders-codecasts/22.test process.md`
- `997-BOOKS/clean-coders-my-youtube/Test And Test Doubles.md`

### 9. 아키텍처와 TDD

#### Clean Architecture와 TDD
- **설계와 아키텍처**: 좋은 설계가 TDD를 용이하게 함
- **Vertical Slice Architecture**: 기능별 수직 슬라이스와 테스트

#### 참고 자료
- `997-BOOKS/Clean_Architecture-Evernote/Ch01. What is Design and Architecture.md`
- `003-RESOURCES/ARCHITECTURE/Vertical Slicing Architectures.md`

### 10. 현대적 TDD 도구와 기법

#### AI 시대의 TDD
- **AI 보조 개발**: LLM을 활용한 테스트 작성
- **자동화된 테스트 생성**: AI 기반 unit test 생성

#### Smart Connections과 TDD
- **지식 관리**: Obsidian에서 TDD 관련 지식 연결
- **임베딩 기반 검색**: 의미적 검색을 통한 TDD 자료 발견

#### 관련 문서
- `003-RESOURCES/AI/AI-Assisted Software Development-A Comprehensive Guide with Practical Prompts-2.md`
- `SMART-CONNECTIONS-GUIDE.md`
- `SMART-CONNECTIONS-CONTEXT.md`

## 🎯 TDD 학습 로드맵

### 초급 단계
1. **TDD 기본 개념** 이해 (`1. TDD.md`)
2. **Red-Green-Refactor 사이클** 연습
3. **간단한 예제** 실습 (Tennis Game)

### 중급 단계
1. **Outside-In TDD** 접근법 학습
2. **Test Double** 사용법 이해
3. **리팩토링과 TDD** 통합 연습

### 고급 단계
1. **TDD 일반적 오해** 이해 및 극복
2. **BDD와 TDD** 통합
3. **DDD와 TDD** 결합
4. **Clean Architecture와 TDD** 적용

## 📊 통계 정보

- **총 문서 수**: 25개 이상
- **주요 저자/강사**: Kent Beck, Ian Cooper, Uncle Bob, Chris Simon
- **핵심 키워드**: TDD, Test-Driven Development, Unit Test, BDD, Refactoring
- **문서 분포**: 
  - 기본 개념: 30%
  - 실습/워크샵: 25%
  - 오해와 문제점: 20%
  - 통합 접근법: 15%
  - 도구와 기법: 10%

## 🔗 추가 학습 자료

### 추천 비디오
- Ian Cooper의 "TDD, Where Did It All Go Wrong"
- Clean Coders Codecasts 시리즈
- Chris Simon의 TDD & DDD Live Coding

### 추천 도서
- Kent Beck: "Test-Driven Development by Example"
- Clean Architecture 관련 자료
- Clean Agile 시리즈

### 실습 프로젝트
- Tennis Game TDD
- 다양한 TDD Cases
- Behavior Driven Development 예제

---

이 문서는 Vault Intelligence System V2를 사용하여 수집된 TDD 관련 자료를 체계적으로 정리한 것입니다. 지속적으로 업데이트되며, 새로운 TDD 관련 자료가 추가될 때마다 확장됩니다.