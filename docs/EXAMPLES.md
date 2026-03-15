# 🎯 Vault Intelligence System V2 실전 예제 모음

## 📖 문서 내비게이션

- [🏠 프로젝트 홈](../README.md) | [🚀 빠른 시작](QUICK_START.md) | [📚 사용자 가이드](USER_GUIDE.md) | **💡 실전 예제** | [🔧 문제 해결](TROUBLESHOOTING.md) | [⚙️ 개발자 가이드](../CLAUDE.md)

---

실제 사용 상황에 따른 구체적인 예제들을 정리했습니다.

## 📚 목차

1. [Claude Code 대화형 사용](#-claude-code-대화형-사용) ⭐ 권장
2. [서버 모드 (Daemon) 활용 예제](#-서버-모드-daemon-활용-예제) 🆕
3. [검색 예제](#-검색-예제)
4. [중복 감지 예제](#-중복-감지-예제)
5. [주제 수집 예제](#-주제-수집-예제)
6. [MOC 자동 생성 예제](#-moc-자동-생성-예제)
7. [주제 분석 예제](#-주제-분석-예제)
8. [프로그래밍 API 예제](#-프로그래밍-api-예제)
9. [배치 처리 예제](#-배치-처리-예제)
10. [문제 해결 예제](#-문제-해결-예제)
11. [실제 활용 사례](#-실제-활용-사례)

---

## 🤖 Claude Code 대화형 사용

vault-intelligence의 주요 사용 방식은 **Claude Code에서 자연어로 요청**하는 것입니다. CLI를 직접 타이핑하지 않고, Claude에게 원하는 것을 말하면 됩니다.

### 📖 문서 검색

| 요청 예시                                                                                                                  | 설명                              |
| -------------------------------------------------------------------------------------------------------------------------- | --------------------------------- |
| "kent beck이 전문가의 접근법에 대해 언급한 문서 찾아줘"                                                                    | 특정 저자/인물 관련 검색          |
| "kent beck이 ai에게서 피드백을 받을 수 있는데 왜 공부해야하는지 답하면서 생각 뒤틀기를 언급한 영상을 정리한 문서를 찾아줘" | 특정 질문에 답하는 문서 검색      |
| "LSP와 유사한 다른 원칙을 찾아줘"                                                                                          | 특정 원칙/개념 검색               |
| 'Branch by abstraction' 은 SOLID 중 어느 원칙들과 관계가 있을까 ?                                                          | SOLID 원칙과 특정 기법의 관계분석 |

### 📚 MOC 및 정리

| 요청 예시                                      | 설명                       |
| ---------------------------------------------- | -------------------------- |
| "TDD 기법에 대해서 MOC를 만들어줘"             | 주제별 Map of Content 생성 |
| "Spring Boot 초보자를 위한 학습 순서 정리해줘" | 학습 경로 생성             |
| "리팩토링 관련 문서들을 모아서 정리해줘"       | 주제별 문서 수집           |
| "DDD 주제로 학습 로드맵 만들어줘"              | 단계별 학습 가이드         |

### 📊 분석 및 리뷰

| 요청 예시                           | 설명             |
| ----------------------------------- | ---------------- |
| "최근 학습한 AI 관련 내용 요약해줘" | 기간별 학습 리뷰 |
| "지난 주에 추가한 문서들 요약해줘"  | 최근 활동 분석   |
| "내 vault에서 부족한 주제 분석해줘" | 지식 공백 분석   |
| "vault에서 중복된 문서 찾아줘"      | 중복 문서 감지   |

### ✍️ 글쓰기 지원

| 요청 예시                                              | 설명                    |
| ------------------------------------------------------ | ----------------------- |
| "AI 시대 개발자 역할에 대한 브런치 글 참고자료 찾아줘" | 글감 검색               |
| "@초안.md 이 브런치 글 작성 도와줘"                    | 초안 기반 참고자료 추천 |
| "TDD 주제로 기술 세미나 발표 자료 참고문서 찾아줘"     | 발표 준비 지원          |
| "신입 개발자 온보딩 문서 만들 자료 정리해줘"           | 문서 작성 지원          |

### 🔗 관련 문서 탐색

| 요청 예시                                            | 설명           |
| ---------------------------------------------------- | -------------- |
| "이 문서와 관련된 다른 문서 찾아줘"                  | 연관 문서 추천 |
| "클린 코드 책 정리 문서와 비슷한 내용 찾아줘"        | 유사 문서 검색 |
| "리팩토링 패턴 문서에서 참조할만한 실습 예제 찾아줘" | 보완 자료 검색 |

### 🏷️ 태그 및 정리

| 요청 예시                              | 설명           |
| -------------------------------------- | -------------- |
| "이 문서에 적절한 태그 추천해줘"       | 자동 태깅      |
| "997-BOOKS 폴더 문서들 태그 정리해줘"  | 폴더별 태깅    |
| "#topic/tdd 태그가 있는 문서들 보여줘" | 태그 기반 검색 |

---

## 🖥️ 서버 모드 (Daemon) 활용 예제

### 예제 1: 기본 워크플로우

```bash
# 데몬 시작
visd start

# 빠른 반복 검색 (0.1-0.5초 응답)
vis search "TDD" --rerank
vis search "리팩토링" --rerank
vis search "클린 코드" --expand

# 상태 확인
visd status

# 작업 완료 후 중지
visd stop
```

### 예제 2: HTTP API로 스크립트 연동

```bash
# Obsidian 문서 작성 시 관련 문서 검색
curl -s --get \
  --data-urlencode "query=테스트 주도 개발 패턴" \
  --data-urlencode "rerank=true" \
  --data-urlencode "top_k=5" \
  "http://localhost:8741/search" | jq '.results[] | {title, score}'
```

### 예제 3: Python 클라이언트 활용

```python
from src.client import VisClient

# visd가 실행 중이어야 함
client = VisClient()

results = client.search(
    query="객체지향 설계 원칙",
    top_k=10,
    search_method="hybrid",
    rerank=True,
)

for r in results:
    print(f"{r['score']:.4f} - {r['title']}")

# 배치 검색 (데몬 상주로 모든 검색이 즉시 응답)
topics = ["TDD", "리팩토링", "SOLID", "클린 아키텍처"]
for topic in topics:
    results = client.search(topic, top_k=3, rerank=True)
    print(f"\n{topic}: {len(results)}건")
    for r in results[:2]:
        print(f"  - {r['title']}")
```

### 예제 4: curl로 직접 HTTP API 호출

```bash
# visd 실행 중일 때 curl로 직접 검색
curl -s --get \
  --data-urlencode "query=핵심 키워드" \
  "http://localhost:8741/search?search_method=hybrid&rerank=true&top_k=10"
```

---

## 🔍 검색 예제

### 예제 1: 기본 개념 검색

```bash
# TDD 관련 문서 찾기
vis search "테스트 주도 개발"
```

**결과 예시:**

```
📄 검색 결과 (5개):
1. TDD 실무 가이드 (유사도: 0.8542)
2. 클린 코더스 TDD 강의 (유사도: 0.7234)
3. TDD 안티패턴 정리 (유사도: 0.6891)
```

### 예제 2: 영어 키워드 검색

```bash
# SOLID 원칙 관련 문서
vis search "SOLID principles" --top-k 3
```

### 예제 3: 복합 개념 검색

```bash
# 마이크로서비스와 DDD를 함께 다룬 문서
vis search "마이크로서비스 도메인 주도 설계" --threshold 0.5
```

### 예제 4: ColBERT 정밀 검색

```bash
# 긴 문장을 사용한 ColBERT 검색 (권장)
vis search "test driven development refactoring clean code practices" --search-method colbert --top-k 5

# 복합 개념 검색
vis search "dependency injection inversion of control spring framework" --search-method colbert
```

**사용 팁:** ColBERT는 단일 키워드보다 긴 문장에서 성능이 우수합니다.

### 예제 5: 재순위화로 정확도 향상

```bash
# 하이브리드 + 재순위화 (최고 정확도)
vis search "clean architecture principles" --search-method hybrid --rerank --top-k 3

# 의미적 검색 + 재순위화
vis search "design patterns strategy factory" --search-method semantic --rerank
```

**기대 효과:** 정확도 15-25% 향상, 처리 시간 2-3배 증가

### 예제 6: 검색 방법별 비교 테스트

```bash
# 같은 쿼리로 각 방법 비교
query="SOLID principles object oriented design"

vis search "$query" --search-method semantic   # 의미적
vis search "$query" --search-method keyword    # 키워드
vis search "$query" --search-method hybrid     # 하이브리드 (추천)
vis search "$query" --search-method colbert    # ColBERT

# 재순위화 비교
vis search "$query" --search-method hybrid             # 기본
vis search "$query" --search-method hybrid --rerank   # 재순위화
```

### 예제 7: 단일 키워드 최적 검색법

```bash
# 단일 약어/키워드는 ColBERT보다 하이브리드가 효과적
vis search "YAGNI" --search-method hybrid           # ✅ 추천
vis search "TDD" --search-method hybrid --rerank   # ✅ 더 정확

# ColBERT용으로 쿼리 확장
vis search "YAGNI You Aren't Going to Need It agile principle" --search-method colbert
```

### 예제 8: 정확도 조절

```bash
# 낮은 임계값 - 더 많은 결과
vis search "리팩토링" --threshold 0.2 --top-k 20

# 높은 임계값 - 정확한 결과만
vis search "리팩토링" --threshold 0.7 --top-k 5
```

### 예제 5: 특정 분야 검색

```bash
# 프론트엔드 관련
vis search "React 컴포넌트 설계"

# 백엔드 관련
vis search "Spring Boot 아키텍처"

# 데이터베이스 관련
vis search "JPA 성능 최적화"
```

### 🆕 예제 6: ColBERT 토큰 수준 검색 (신규!)

```bash
# ColBERT 검색 - 세밀한 토큰 매칭
vis search "TDD" --search-method colbert

# ColBERT 검색과 재순위화 결합 - 최고 품질
vis search "클린 코드" --search-method colbert --rerank

# ColBERT 검색에서 더 많은 결과
vis search "리팩토링" --search-method colbert --top-k 15
```

**ColBERT vs 다른 검색 방법 비교:**

```bash
# 동일한 쿼리로 다양한 검색 방법 테스트
vis search "테스트 주도 개발" --search-method semantic
vis search "테스트 주도 개발" --search-method keyword
vis search "테스트 주도 개발" --search-method hybrid
vis search "테스트 주도 개발" --search-method colbert
```

### 예제 7: 초기 ColBERT 인덱싱

```bash
# 🎯 처음 사용 시 ColBERT 전체 인덱싱 (1회, 1-2시간)
vis reindex --with-colbert

# ✅ 이후로는 캐시 활용으로 즉시 검색 가능!
vis search "아무 검색어" --search-method colbert
```

---

## 🔎 중복 감지 예제

### 예제 1: 기본 중복 감지

```bash
vis duplicates
```

**결과 해석:**

```
📊 중복 분석 결과:
전체 문서: 2,407개
중복 그룹: 15개          # 15개의 중복 그룹 발견
중복 문서: 45개          # 총 45개 문서가 중복
고유 문서: 2,362개       # 실제 고유한 문서는 2,362개
중복 비율: 1.9%          # 전체의 1.9%가 중복

📋 중복 그룹 상세:
그룹 dup_001:
  문서 수: 3개
  평균 유사도: 0.9123     # 매우 높은 유사도
    - 003-RESOURCES/TDD/basic-concepts.md (150단어)
    - 001-INBOX/tdd-정리.md (142단어)
    - temp/tdd-backup.md (148단어)     # 임시 백업 파일
```

### 예제 2: 중복 그룹 분석

특정 그룹의 문서들을 직접 확인:

```bash
# 첫 번째 중복 그룹의 문서들 비교
cat "003-RESOURCES/TDD/basic-concepts.md" | head -10
cat "001-INBOX/tdd-정리.md" | head -10
```

### 예제 3: 중복 해결 워크플로우

```bash
# 1. 중복 감지
vis duplicates

# 2. 해당 파일들 검토 (수동)
# 3. 불필요한 파일 제거 (수동)
# 4. 재인덱싱으로 반영
vis reindex
```

---

## 📚 주제 수집 예제

### 예제 1: TDD 관련 자료 수집

```bash
vis collect "TDD" --output collections/tdd_materials.md
```

### 예제 2: 쿼리 확장을 통한 포괄적 수집 🆕

```bash
# 기본 확장 수집 (동의어 + HyDE)
vis collect "TDD" --expand --output collections/tdd_expanded.md
```

**확장 검색 결과 비교:**

| 수집 방법 | 문서 수 | 단어 수  | 주요 차이점                                           |
| --------- | ------- | -------- | ----------------------------------------------------- |
| 기본 수집 | 5개     | 22,032개 | clean-coders 시리즈 중심                              |
| 확장 수집 | 5개     | 24,042개 | 더 다양한 TDD 리소스 포함 (003-RESOURCES/TDD 폴더 등) |

### 예제 3: 선택적 확장 기능

```bash
# 동의어만 확장 (정확도 우선)
vis collect "리팩토링" --expand --no-hyde --top-k 15

# HyDE만 활용 (의미적 확장 우선)
vis collect "도메인 모델링" --expand --no-synonyms --threshold 0.2

# 포괄적 수집 (낮은 임계값 + 확장)
vis collect "클린 아키텍처" --expand --threshold 0.1 --top-k 30
```

**생성된 파일 예시 (tdd_materials.md):**

```markdown
# TDD 관련 문서 모음

**수집 일시**: 2025-08-21 14:30:00
**검색 쿼리**: TDD
**쿼리 확장**: 동의어 + HyDE 활성화
**총 문서**: 15개
**총 단어수**: 24,042개

## 📊 수집 통계

- **태그 분포**: testing/tdd (8개), development/methodology (5개)
- **디렉토리**: 003-RESOURCES (10개), 997-BOOKS (3개), SLIPBOX (2개)

## 🔍 확장 검색 정보

- **동의어 확장**: 테스트 주도 개발, 단위 테스트, 테스트 드리븐
- **HyDE 문서**: "TDD는 소프트웨어 개발 방법론 중 하나로..."
- **검색 범위**: 원본 + 3개 동의어 + 1개 HyDE = 총 5개 쿼리

## 📄 수집된 문서

### 1. TDD 기본 개념 (유사도: 0.9234)

**경로**: 003-RESOURCES/TDD/basic-concepts.md
**단어수**: 234단어
**매칭 쿼리**: 동의어("테스트 주도 개발")
**태그**: #testing/tdd #methodology

TDD는 테스트 주도 개발(Test-Driven Development)의 약자로...

### 2. Red-Green-Refactor 사이클 (유사도: 0.8765)

**경로**: 003-RESOURCES/TDD/red-green-refactor.md
**매칭 쿼리**: HyDE 문서
**단어수**: 187단어
...
```

### 예제 4: 책 집필용 챕터별 자료 수집

```bash
# 챕터 1: TDD 기초
vis collect "TDD 기본 개념" --threshold 0.6 --output book/chapter1.md

# 챕터 2: 실무 적용
vis collect "TDD 실무 적용" --threshold 0.5 --output book/chapter2.md

# 챕터 3: 고급 기법
vis collect "TDD 고급 기법" --threshold 0.4 --output book/chapter3.md
```

### 예제 3: 연구 주제별 자료 정리

```bash
# 아키텍처 패턴 연구
vis collect "헥사고날 아키텍처" --top-k 20 --output research/hexagonal.md

# 성능 최적화 연구
vis collect "JPA 성능 최적화" --top-k 15 --output research/jpa_performance.md
```

### 예제 4: 프로젝트별 관련 자료 수집

```bash
# 특정 프로젝트 관련 자료
vis collect "Spring Boot 마이크로서비스" --output projects/microservices.md

# 프론트엔드 프로젝트
vis collect "React 컴포넌트 아키텍처" --output projects/react_arch.md
```

---

## 📚 MOC 자동 생성 예제 🆕

MOC(Map of Content)는 특정 주제에 대한 체계적인 탐색 가이드입니다. 관련 문서들을 카테고리별로 분류하고 학습 경로를 제공합니다.

### 예제 1: 기본 MOC 생성

```bash
# TDD 주제 MOC 생성
vis generate-moc "TDD"
```

**결과 예시:**

```
📊 MOC 생성 결과:
--------------------------------------------------
주제: TDD
총 문서: 20개
핵심 문서: 5개
카테고리: 6개
학습 경로: 6단계
관련 주제: 10개
최근 업데이트: 10개

📋 카테고리별 문서 분포:
  입문/기초: 5개 문서
  개념/이론: 6개 문서
  실습/예제: 9개 문서
  도구/기술: 9개 문서
  심화/고급: 7개 문서
  참고자료: 7개 문서

💾 MOC 파일이 MOC-TDD.md에 저장되었습니다.
```

### 예제 2: 리팩토링 MOC (더 많은 문서 포함)

```bash
# 50개 문서로 더 포괄적인 MOC 생성
vis generate-moc "리팩토링" --top-k 50 --output "리팩토링-완전가이드.md"
```

**결과 예시:**

```
📊 MOC 생성 결과:
--------------------------------------------------
주제: 리팩토링
총 문서: 35개
핵심 문서: 5개
카테고리: 7개
학습 경로: 7단계
관련 주제: 12개

📋 카테고리별 문서 분포:
  입문/기초: 8개 문서
  개념/이론: 12개 문서
  실습/예제: 15개 문서
  도구/기술: 18개 문서
  심화/고급: 10개 문서
  참고자료: 6개 문서
  기타: 3개 문서

💾 MOC 파일이 리팩토링-완전가이드.md에 저장되었습니다.
```

### 예제 3: 포괄적 MOC 생성 (고립 문서 포함)

```bash
# 연결되지 않은 문서들도 포함하여 완전한 MOC 생성
vis generate-moc "Spring Boot" --include-orphans --threshold 0.2
```

**사용 시나리오**: Spring Boot 관련 문서들이 vault 전체에 흩어져 있고, 일부 문서들이 태그나 링크로 연결되지 않은 경우

### 예제 4: 실제 책 집필용 MOC 생성

```bash
# "AI 시대의 TDD 활용" 책 집필을 위한 체계적 MOC
vis generate-moc \
  --topic "TDD" \
  --output "book/TDD-책구성.md" \
  --top-k 100 \
  --threshold 0.25 \
  --include-orphans
```

**결과**: 책의 목차 구성에 활용할 수 있는 체계적인 문서 분류와 학습 경로

### 예제 5: 여러 주제 MOC 일괄 생성

```bash
# 여러 주제에 대한 MOC를 한번에 생성
topics=("TDD" "리팩토링" "클린코드" "DDD" "마이크로서비스")

for topic in "${topics[@]}"; do
    echo "MOC 생성 중: $topic"
    vis generate-moc "$topic" --output "MOCs/MOC-${topic}.md"
done
```

### 예제 6: 프로그래밍 방식 MOC 생성

```python
from src.features.moc_generator import MOCGenerator
from src.features.advanced_search import AdvancedSearchEngine

# 검색 엔진과 MOC 생성기 초기화
engine = AdvancedSearchEngine("/path/to/vault", "cache", config)
moc_generator = MOCGenerator(engine, config)

# TDD MOC 생성
moc_data = moc_generator.generate_moc(
    topic="TDD",
    top_k=50,
    threshold=0.3,
    include_orphans=False,
    output_file="TDD-MOC.md"
)

# 생성된 MOC 정보 출력
print(f"🎯 주제: {moc_data.topic}")
print(f"📄 총 문서: {moc_data.total_documents}개")
print(f"⭐ 핵심 문서: {len(moc_data.core_documents)}개")

print(f"\n📂 카테고리별 분포:")
for category in moc_data.categories:
    print(f"  {category.name}: {len(category.documents)}개")

print(f"\n🛤️ 학습 경로:")
for step in moc_data.learning_path:
    print(f"  {step.step}단계: {step.title} ({step.difficulty_level})")
    print(f"    문서 수: {len(step.documents)}개")

print(f"\n🔗 관련 주제:")
for topic, count in moc_data.related_topics[:5]:
    print(f"  - {topic}: {count}개 문서")
```

### MOC 활용 사례

#### 사례 1: 신입 개발자 온보딩

```bash
# 신입 개발자를 위한 기초 개념 MOC
vis generate-moc "프로그래밍 기초" --top-k 20 --threshold 0.4
```

→ 학습 경로를 따라 체계적으로 기초를 다질 수 있음

#### 사례 2: 기술 세미나 준비

```bash
# TDD 세미나를 위한 발표 자료 구성
vis generate-moc "TDD" --output "seminar/TDD-발표자료.md"
```

→ 입문부터 심화까지 체계적인 발표 구성 가능

#### 사례 3: 팀 스터디 계획

```bash
# 팀 스터디를 위한 단계별 학습 계획
vis generate-moc "클린 아키텍처" --top-k 30
```

→ 생성된 학습 경로를 따라 팀 스터디 진행

#### 사례 4: 개인 지식 점검

```bash
# 특정 분야 지식 현황 파악
vis generate-moc "Spring" --include-orphans
```

→ 빠진 부분이나 약한 영역 파악 가능

### MOC 품질 향상 팁

#### 좋은 MOC를 위한 vault 정리

```bash
# 1. 태그 체계 정리 (MOC 품질 향상)
vis tag "specific-folder/" --recursive

# 2. MOC 생성
vis generate-moc "TDD"

# 3. 결과 확인 후 태그 보완
vis tag "missed-documents/"
```

#### 임계값 최적화 과정

```bash
# 1. 높은 임계값으로 시작 (핵심만)
vis generate-moc "TDD" --threshold 0.5 --top-k 20

# 2. 중간 임계값으로 확장 (균형)
vis generate-moc "TDD" --threshold 0.3 --top-k 50

# 3. 낮은 임계값으로 포괄적 수집
vis generate-moc "TDD" --threshold 0.2 --top-k 100 --include-orphans
```

### 생성된 MOC 문서 예시 구조

```markdown
# 📚 TDD Map of Content

## 🎯 개요

이 Map of Content는 'TDD' 주제에 대한 종합적인 탐색 가이드입니다.

**📊 컬렉션 통계:**

- 총 문서 수: 20개
- 총 단어 수: 48,289개
- 평균 문서 길이: 2,414개 단어

## 🌟 핵심 문서

1. **[[TDD 실무 완벽 가이드]]** (3,241 단어)
2. **[[테스트 주도 개발 원칙]]** (2,156 단어)
3. **[[TDD 실전 적용 사례]]** (2,891 단어)

## 📖 카테고리별 분류

### 입문/기초

- [[TDD란 무엇인가]] - TDD의 기본 개념과 원리
- [[테스트 우선 개발 시작하기]] - 초보자를 위한 단계별 가이드

### 실습/예제

- [[TDD 실습 워크샵]] - 실제 코딩을 통한 TDD 연습
- [[단위 테스트 작성법]] - 좋은 테스트 작성 방법

## 🛤️ 추천 학습 경로

### 1단계: 입문/기초 (입문)

**설명**: TDD에 대한 기본적인 이해와 개념 학습
**추천 문서:**

- [[TDD란 무엇인가]]
- [[테스트 주도 개발 기초]]

### 2단계: 실습/예제 (중급)

**설명**: 실제 사례를 통한 실습과 연습
**추천 문서:**

- [[TDD 실습 워크샵]]
- [[단위 테스트 작성법]]

## 🔗 관련 주제

- **단위 테스트** (12개 문서)
- **리팩토링** (8개 문서)
- **클린 코드** (6개 문서)
```

---

## 📊 주제 분석 예제

### 예제 1: 전체 vault 주제 분석

```bash
vis analyze
```

**결과 예시:**

```
📊 주제 분석 결과:
분석 문서: 2,407개
발견 주제: 25개
클러스터링 방법: K-means

🏷️ 주요 주제들:

주제 1: 소프트웨어 개발 방법론
  문서 수: 342개
  주요 키워드: TDD, 애자일, 스크럼, 개발프로세스, 테스트
  설명: 테스트 주도 개발과 애자일 방법론 관련 문서들...

주제 2: 코드 품질 및 리팩토링
  문서 수: 198개
  주요 키워드: 리팩토링, 클린코드, SOLID, 코드리뷰, 품질
  설명: 코드 품질 향상과 리팩토링 기법에 관한 문서들...

주제 3: 아키텍처 설계
  문서 수: 156개
  주요 키워드: 아키텍처, 설계, 패턴, 마이크로서비스, DDD
  설명: 소프트웨어 아키텍처 설계 패턴과 원칙들...
```

### 예제 2: 주제 분석 결과 활용

분석 결과를 바탕으로 부족한 주제 파악:

```bash
# 발견된 주제 중 문서가 적은 영역 보강
vis collect "성능 테스트" --top-k 30

# 새로운 주제 영역 탐색
vis search "DevOps 파이프라인" --top-k 20
```

---

## 💻 프로그래밍 API 예제

### 예제 1: 기본 검색 API 사용

```python
#!/usr/bin/env python3
"""
기본 검색 API 사용 예제
"""
import sys
from pathlib import Path

# 프로젝트 루트 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.features.advanced_search import AdvancedSearchEngine
import yaml

def main():
    # 설정 로딩
    with open('config/settings.yaml', 'r') as f:
        config = yaml.safe_load(f)

    # 검색 엔진 초기화
    engine = AdvancedSearchEngine(
        vault_path="/path/to/your/vault",
        cache_dir="cache",
        config=config
    )

    # 하이브리드 검색
    results = engine.hybrid_search("TDD", top_k=5)

    print(f"🔍 '{query}' 검색 결과:")
    for i, result in enumerate(results, 1):
        print(f"{i}. {result.document.title}")
        print(f"   경로: {result.document.path}")
        print(f"   점수: {result.similarity_score:.4f}")
        print()

if __name__ == "__main__":
    main()
```

### 예제 2: 고급 필터링 검색

```python
from src.features.advanced_search import SearchQuery
from datetime import datetime, timedelta

# 복잡한 검색 조건
query = SearchQuery(
    text="아키텍처 패턴",
    min_word_count=200,              # 200단어 이상
    max_word_count=3000,             # 3000단어 이하
    date_from=datetime(2024, 1, 1),  # 2024년 이후
    exclude_paths=["temp/", "backup/"] # 특정 경로 제외
)

results = engine.advanced_search(query)
print(f"필터링된 결과: {len(results)}개")
```

### 예제 3: 중복 감지 API

```python
from src.features.duplicate_detector import DuplicateDetector

detector = DuplicateDetector(engine, config)
analysis = detector.find_duplicates()

print(f"📊 중복 분석 결과:")
print(f"전체 문서: {analysis.total_documents}개")
print(f"중복 그룹: {analysis.get_group_count()}개")
print(f"중복 비율: {analysis.get_duplicate_ratio():.1%}")

# 중복 그룹 상세 처리
for group in analysis.duplicate_groups[:5]:  # 상위 5개 그룹
    print(f"\n그룹 {group.id} (유사도: {group.average_similarity:.4f})")
    for doc in group.documents:
        print(f"  📄 {doc.path} ({doc.word_count}단어)")
```

### 예제 4: 주제 수집 API

```python
from src.features.topic_collector import TopicCollector

collector = TopicCollector(engine, config)

# 기본 수집
basic_collection = collector.collect_topic("TDD", top_k=20)

# 쿼리 확장 수집 🆕
expanded_collection = collector.collect_topic(
    topic="TDD",
    top_k=20,
    threshold=0.3,
    use_expansion=True,
    include_synonyms=True,
    include_hyde=True,
    output_file="collections/tdd_expanded.md"
)

# 선택적 확장 수집
synonym_only_collection = collector.collect_topic(
    topic="리팩토링",
    top_k=15,
    use_expansion=True,
    include_synonyms=True,
    include_hyde=False
)

# 수집 결과 비교
print(f"기본 수집: {basic_collection.metadata.total_documents}개 문서")
print(f"확장 수집: {expanded_collection.metadata.total_documents}개 문서")
print(f"단어 수 차이: {expanded_collection.metadata.total_word_count - basic_collection.metadata.total_word_count:+,}개")

# 여러 주제 일괄 수집 (확장 모드)
topics = ["TDD", "리팩토링", "클린코드", "아키텍처"]
results = {}

for topic in topics:
    print(f"🔍 '{topic}' 확장 수집 중...")
    collection = collector.collect_topic(
        topic=topic,
        top_k=20,
        threshold=0.4,
        use_expansion=True,
        output_file=f"collections/{topic}_expanded.md"
    )
    results[topic] = collection.metadata.total_documents
    print(f"✅ {results[topic]}개 문서 수집")

# 결과 요약
print(f"\n📊 전체 수집 결과:")
for topic, count in results.items():
    print(f"  {topic}: {count}개")
```

### 예제 5: MOC 생성 API (Phase 8) 🆕

```python
#!/usr/bin/env python3
"""
MOC 자동 생성 API 사용 예제
"""
from src.features.moc_generator import MOCGenerator
from src.features.advanced_search import AdvancedSearchEngine
import yaml

def generate_moc_for_topic(topic: str, output_dir: str = "MOCs"):
    """특정 주제에 대한 MOC 생성"""

    # 설정 로딩
    with open('config/settings.yaml', 'r') as f:
        config = yaml.safe_load(f)

    # 엔진 초기화
    engine = AdvancedSearchEngine(
        vault_path="/path/to/vault",
        cache_dir="cache",
        config=config
    )

    # MOC 생성기 초기화
    moc_generator = MOCGenerator(engine, config)

    # MOC 생성
    output_file = f"{output_dir}/MOC-{topic.replace(' ', '-')}.md"
    moc_data = moc_generator.generate_moc(
        topic=topic,
        top_k=50,
        threshold=0.3,
        include_orphans=False,
        use_expansion=True,
        output_file=output_file
    )

    # 결과 분석
    print(f"🎯 {topic} MOC 생성 완료:")
    print(f"  📄 총 문서: {moc_data.total_documents}개")
    print(f"  ⭐ 핵심 문서: {len(moc_data.core_documents)}개")
    print(f"  📂 카테고리: {len(moc_data.categories)}개")
    print(f"  🛤️ 학습 단계: {len(moc_data.learning_path)}단계")
    print(f"  🔗 관련 주제: {len(moc_data.related_topics)}개")

    # 카테고리별 상세 정보
    print(f"\n📋 카테고리별 분포:")
    for category in moc_data.categories:
        print(f"  {category.name}: {len(category.documents)}개")
        # 각 카테고리의 대표 문서 1개씩 표시
        if category.documents:
            sample_doc = category.documents[0]
            print(f"    예: {sample_doc.title}")

    # 학습 경로 정보
    print(f"\n🛤️ 학습 경로 개요:")
    for step in moc_data.learning_path:
        print(f"  {step.step}단계: {step.title}")
        print(f"    난이도: {step.difficulty_level}")
        print(f"    문서 수: {len(step.documents)}개")

    # 관련 주제 (상위 5개)
    if moc_data.related_topics:
        print(f"\n🔗 주요 관련 주제:")
        for topic_name, count in moc_data.related_topics[:5]:
            print(f"  - {topic_name}: {count}개 문서")

    return moc_data

# 사용 예제
if __name__ == "__main__":
    topics = ["TDD", "리팩토링", "클린코드", "DDD"]

    for topic in topics:
        print(f"\n{'='*50}")
        moc_data = generate_moc_for_topic(topic)
        print(f"✅ {topic} MOC 생성 완료")

    print(f"\n🎉 모든 MOC 생성 완료!")
```

### 예제 6: 고급 MOC 생성 및 분석

```python
#!/usr/bin/env python3
"""
고급 MOC 생성 및 품질 분석 예제
"""
from src.features.moc_generator import MOCGenerator, DocumentCategory
from src.features.advanced_search import AdvancedSearchEngine
import yaml
from typing import List

class MOCAnalyzer:
    """MOC 품질 분석기"""

    def __init__(self, moc_generator: MOCGenerator):
        self.moc_generator = moc_generator

    def analyze_moc_quality(self, moc_data) -> dict:
        """MOC 품질 분석"""
        quality_metrics = {}

        # 1. 카테고리 균형도 분석
        category_sizes = [len(cat.documents) for cat in moc_data.categories]
        quality_metrics['category_balance'] = {
            'avg_size': sum(category_sizes) / len(category_sizes),
            'max_size': max(category_sizes),
            'min_size': min(category_sizes),
            'balance_ratio': min(category_sizes) / max(category_sizes) if max(category_sizes) > 0 else 0
        }

        # 2. 학습 경로 완성도
        quality_metrics['learning_path_completeness'] = {
            'total_steps': len(moc_data.learning_path),
            'avg_docs_per_step': sum(len(step.documents) for step in moc_data.learning_path) / len(moc_data.learning_path),
            'difficulty_coverage': len(set(step.difficulty_level for step in moc_data.learning_path))
        }

        # 3. 관련성 점수
        quality_metrics['relatedness_score'] = {
            'total_relationships': len(moc_data.relationships),
            'avg_relationship_strength': sum(rel.strength for rel in moc_data.relationships) / len(moc_data.relationships) if moc_data.relationships else 0,
            'connected_documents_ratio': len(set([rel.source_doc.path for rel in moc_data.relationships] +
                                                [rel.target_doc.path for rel in moc_data.relationships])) / moc_data.total_documents if moc_data.total_documents > 0 else 0
        }

        return quality_metrics

    def suggest_improvements(self, moc_data, quality_metrics: dict) -> List[str]:
        """MOC 개선 제안"""
        suggestions = []

        balance = quality_metrics['category_balance']
        if balance['balance_ratio'] < 0.3:
            suggestions.append(f"📊 카테고리 불균형: 일부 카테고리에 문서가 편중됨 (균형도: {balance['balance_ratio']:.2f})")
            suggestions.append("   → 임계값을 조정하거나 더 많은 문서를 포함해보세요")

        path = quality_metrics['learning_path_completeness']
        if path['avg_docs_per_step'] < 2:
            suggestions.append(f"🛤️ 학습 경로 부족: 단계별 문서가 부족함 (평균 {path['avg_docs_per_step']:.1f}개)")
            suggestions.append("   → --top-k 값을 증가시키거나 threshold를 낮춰보세요")

        relatedness = quality_metrics['relatedness_score']
        if relatedness['connected_documents_ratio'] < 0.5:
            suggestions.append(f"🔗 연결성 부족: 문서 간 관계가 부족함 ({relatedness['connected_documents_ratio']:.1%})")
            suggestions.append("   → 태그를 체계적으로 정리하거나 문서 간 링크를 추가해보세요")

        return suggestions

def advanced_moc_generation_example():
    """고급 MOC 생성 및 분석 예제"""

    # 설정 로딩
    with open('config/settings.yaml', 'r') as f:
        config = yaml.safe_load(f)

    # 엔진 및 생성기 초기화
    engine = AdvancedSearchEngine("/path/to/vault", "cache", config)
    moc_generator = MOCGenerator(engine, config)
    analyzer = MOCAnalyzer(moc_generator)

    topic = "TDD"

    # 1. 기본 MOC 생성
    print(f"🚀 {topic} MOC 생성 중...")
    moc_data = moc_generator.generate_moc(
        topic=topic,
        top_k=30,
        threshold=0.3,
        use_expansion=True,
        output_file=f"MOC-{topic}-basic.md"
    )

    # 2. MOC 품질 분석
    print(f"📊 MOC 품질 분석 중...")
    quality_metrics = analyzer.analyze_moc_quality(moc_data)

    print(f"\n📈 {topic} MOC 품질 분석 결과:")
    print(f"카테고리 균형도: {quality_metrics['category_balance']['balance_ratio']:.2f}")
    print(f"학습 경로 완성도: {quality_metrics['learning_path_completeness']['total_steps']}단계")
    print(f"문서 연결성: {quality_metrics['relatedness_score']['connected_documents_ratio']:.1%}")

    # 3. 개선 제안
    suggestions = analyzer.suggest_improvements(moc_data, quality_metrics)
    if suggestions:
        print(f"\n💡 MOC 개선 제안:")
        for suggestion in suggestions:
            print(f"  {suggestion}")

        # 4. 개선된 MOC 재생성
        print(f"\n🔧 개선된 MOC 재생성 중...")
        improved_moc = moc_generator.generate_moc(
            topic=topic,
            top_k=50,  # 더 많은 문서
            threshold=0.25,  # 낮은 임계값
            include_orphans=True,  # 고립 문서 포함
            use_expansion=True,
            output_file=f"MOC-{topic}-improved.md"
        )

        # 5. 개선 효과 비교
        improved_metrics = analyzer.analyze_moc_quality(improved_moc)
        print(f"\n📊 개선 효과:")
        print(f"문서 수: {moc_data.total_documents} → {improved_moc.total_documents}")
        print(f"카테고리 균형도: {quality_metrics['category_balance']['balance_ratio']:.2f} → {improved_metrics['category_balance']['balance_ratio']:.2f}")
        print(f"연결성: {quality_metrics['relatedness_score']['connected_documents_ratio']:.1%} → {improved_metrics['relatedness_score']['connected_documents_ratio']:.1%}")

if __name__ == "__main__":
    advanced_moc_generation_example()
```

---

## 🔄 배치 처리 예제

### 예제 1: 주제별 일괄 수집 스크립트

```python
#!/usr/bin/env python3
"""
주제별 일괄 수집 스크립트 (batch_collect.py)
"""
import os
import sys
from pathlib import Path

# 수집할 주제 목록
TOPICS = [
    "TDD", "리팩토링", "클린코드", "SOLID",
    "디자인패턴", "아키텍처", "마이크로서비스",
    "Spring Boot", "JPA", "테스트"
]

def batch_collect():
    """주제별 일괄 수집"""
    # 출력 디렉토리 생성
    output_dir = Path("collections")
    output_dir.mkdir(exist_ok=True)

    results = []

    for topic in TOPICS:
        print(f"🔍 주제 '{topic}' 수집 중...")

        # CLI 명령어 실행
        cmd = f'vis collect "{topic}" --top-k 15 --output "collections/{topic}.md"'
        result = os.system(cmd)

        if result == 0:
            print(f"✅ '{topic}' 수집 완료")
            results.append((topic, "성공"))
        else:
            print(f"❌ '{topic}' 수집 실패")
            results.append((topic, "실패"))

    # 결과 요약
    print(f"\n📊 배치 수집 결과:")
    for topic, status in results:
        print(f"  {topic}: {status}")

if __name__ == "__main__":
    batch_collect()
```

### 예제 2: 자동 백업 및 분석 스크립트

```python
#!/usr/bin/env python3
"""
자동 백업 및 분석 스크립트 (daily_analysis.py)
"""
import os
import shutil
from datetime import datetime

def daily_maintenance():
    """일일 유지보수 작업"""
    today = datetime.now().strftime("%Y%m%d")

    print(f"🔄 {today} 일일 유지보수 시작")

    # 1. 중복 감지
    print("1️⃣ 중복 문서 감지...")
    os.system("vis duplicates > reports/duplicates_{today}.txt")

    # 2. 주제 분석
    print("2️⃣ 주제 분석...")
    os.system("vis analyze > reports/topics_{today}.txt")

    # 3. 캐시 백업
    print("3️⃣ 캐시 백업...")
    if os.path.exists("cache"):
        shutil.copytree("cache", f"backups/cache_{today}")

    # 4. 통계 리포트 생성
    print("4️⃣ 통계 리포트...")
    os.system("vis info > reports/stats_{today}.txt")

    print("✅ 일일 유지보수 완료")

if __name__ == "__main__":
    daily_maintenance()
```

### 예제 3: 검색 품질 테스트 스크립트

```python
#!/usr/bin/env python3
"""
검색 품질 테스트 스크립트 (quality_test.py)
"""
import time

# 테스트 쿼리 목록
TEST_QUERIES = [
    ("TDD", 5),
    ("테스트 주도 개발", 10),
    ("리팩토링", 8),
    ("클린 코드", 12),
    ("SOLID principles", 6),
    ("마이크로서비스 아키텍처", 4)
]

def test_search_quality():
    """검색 품질 테스트"""
    print("🧪 검색 품질 테스트 시작")

    results = []

    for query, expected_min in TEST_QUERIES:
        print(f"🔍 테스트: '{query}'")

        start_time = time.time()
        cmd = f'vis search "{query}" --top-k 20'
        result = os.system(cmd)
        duration = time.time() - start_time

        # 간단한 품질 평가 (실제로는 더 정교한 평가 필요)
        status = "✅ 통과" if result == 0 else "❌ 실패"
        results.append((query, status, f"{duration:.2f}s"))

        print(f"  결과: {status} (시간: {duration:.2f}초)")
        print()

    # 결과 요약
    print("📊 테스트 결과 요약:")
    for query, status, time in results:
        print(f"  {query}: {status} ({time})")

if __name__ == "__main__":
    test_search_quality()
```

---

## 🔧 문제 해결 예제

### 예제 1: 검색 결과가 부정확할 때

```bash
# 문제: "TDD" 검색 시 관련 없는 문서들이 나옴

# 해결 1: 임계값 상향 조정
vis search "TDD" --threshold 0.6

# 해결 2: 더 구체적인 쿼리 사용
vis search "테스트 주도 개발 방법론"

# 해결 3: 강제 재인덱싱
vis reindex --force
```

### 예제 2: 인덱싱이 매우 느릴 때

```bash
# 문제: 2,000개 문서 인덱싱에 30분 이상 소요

# 진단: 상세 로그로 병목점 확인
vis reindex --verbose

# 해결 1: 설정 최적화 (config/settings.yaml)
model:
  batch_size: 16  # 32에서 16으로 감소

# 해결 2: 단계별 인덱싱 (큰 디렉토리 제외)
vault:
  excluded_dirs:
    - "LARGE_BACKUP_DIR"  # 임시로 큰 디렉토리 제외
```

### 예제 3: 메모리 부족 오류

```bash
# 문제: "MemoryError: Unable to allocate array"

# 해결 1: 배치 크기 감소
# config/settings.yaml 수정:
model:
  batch_size: 8  # 더 작게 설정

# 해결 2: 제외 디렉토리 추가로 문서 수 감소
vault:
  excluded_dirs:
    - "archive/"
    - "temp/"
    - "backup/"
```

### 예제 4: 캐시 파일 손상

```bash
# 문제: "sqlite3.DatabaseError: database disk image is malformed"

# 해결: 캐시 완전 초기화
rm -rf cache/
vis reindex --force

# 예방: 정기적 백업
cp cache/embeddings.db cache/embeddings_backup_$(date +%Y%m%d).db
```

### 예제 5: 특정 파일 처리 실패

```bash
# 문제: 특정 마크다운 파일이 인덱싱되지 않음

# 진단: 해당 파일 확인
python -c "
from src.core.vault_processor import VaultProcessor
processor = VaultProcessor('/path/to/vault')
doc = processor.process_file('problematic_file.md')
print(doc.content if doc else 'Failed to process')
"

# 해결: 파일 인코딩 또는 형식 문제 해결
# - UTF-8 인코딩 확인
# - 특수문자 제거
# - 파일 권한 확인
```

### 예제 6: 성능 모니터링 스크립트

```python
#!/usr/bin/env python3
"""
성능 모니터링 스크립트 (monitor_performance.py)
"""
import time
import psutil
import os

def monitor_search_performance():
    """검색 성능 모니터링"""
    test_queries = ["TDD", "리팩토링", "아키텍처"]

    print("🔍 성능 모니터링 시작")

    for query in test_queries:
        print(f"\n테스트 쿼리: '{query}'")

        # 시스템 리소스 측정 시작
        process = psutil.Process()
        memory_before = process.memory_info().rss / 1024 / 1024  # MB
        cpu_before = process.cpu_percent()

        start_time = time.time()

        # 검색 실행
        result = os.system(f'vis search "{query}" > /dev/null 2>&1')

        end_time = time.time()
        duration = end_time - start_time

        # 시스템 리소스 측정 종료
        memory_after = process.memory_info().rss / 1024 / 1024  # MB
        memory_used = memory_after - memory_before

        print(f"  ⏱️  실행 시간: {duration:.2f}초")
        print(f"  💾 메모리 사용: {memory_used:.1f}MB")
        print(f"  📊 결과: {'✅ 성공' if result == 0 else '❌ 실패'}")

if __name__ == "__main__":
    monitor_search_performance()
```

---

## 📈 고급 워크플로우 예제

### 예제 1: 책 집필 완전 워크플로우

```bash
#!/bin/bash
# 책 집필 지원 완전 워크플로우 (book_workflow.sh)

echo "📚 책 집필 지원 워크플로우 시작"

# 1단계: 전체 주제 분석으로 구조 파악
echo "1️⃣ 주제 분석..."
vis analyze > book_planning/topic_analysis.txt

# 2단계: 챕터별 자료 수집
chapters=(
    "TDD:TDD 기본 개념과 실습"
    "Refactoring:리팩토링 기법과 패턴"
    "CleanCode:클린 코드 원칙"
    "Architecture:소프트웨어 아키텍처"
    "Testing:테스트 전략과 도구"
)

echo "2️⃣ 챕터별 자료 수집..."
for chapter in "${chapters[@]}"; do
    IFS=':' read -r topic title <<< "$chapter"
    echo "  📖 ${title} 수집 중..."
    vis collect \
        --topic "$title" \
        --top-k 25 \
        --threshold 0.5 \
        --output "book_materials/chapter_${topic,,}.md"
done

# 3단계: 중복 내용 검사
echo "3️⃣ 중복 내용 검사..."
vis duplicates > book_planning/duplicate_check.txt

# 4단계: 부족한 자료 식별
echo "4️⃣ 추가 자료 검색..."
vis search "TDD 실무 적용 사례" --top-k 15 > book_materials/additional_cases.txt

echo "✅ 책 집필 워크플로우 완료"
echo "📁 결과물: book_materials/ 디렉토리 확인"
```

### 예제 2: 지식 정리 및 체계화 워크플로우

```python
#!/usr/bin/env python3
"""
지식 정리 및 체계화 워크플로우 (knowledge_organization.py)
"""
import os
import yaml
from datetime import datetime

class KnowledgeOrganizer:
    def __init__(self):
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    def analyze_knowledge_gaps(self):
        """지식 공백 분석"""
        print("🔍 지식 공백 분석 중...")

        # 주제 분석 실행
        os.system(f"vis analyze > reports/topics_{self.timestamp}.txt")

        # 결과 분석 (간단한 예시)
        expected_topics = [
            "TDD", "리팩토링", "클린코드", "SOLID", "디자인패턴",
            "아키텍처", "마이크로서비스", "DDD", "테스트", "성능"
        ]

        print("📊 예상 주제 대비 분석:")
        for topic in expected_topics:
            # 각 주제별 문서 수 확인
            result = os.popen(f'vis search "{topic}" --top-k 1 2>/dev/null | grep "검색 결과"').read()
            print(f"  {topic}: {result.strip() if result else '자료 부족'}")

    def create_study_plan(self):
        """학습 계획 생성"""
        print("📅 학습 계획 생성 중...")

        study_topics = [
            ("TDD 기초", "TDD 기본 개념", 3),
            ("TDD 실무", "TDD 실무 적용", 5),
            ("리팩토링", "리팩토링 기법", 4),
            ("아키텍처", "소프트웨어 아키텍처", 6)
        ]

        plan_content = "# 학습 계획\n\n"
        plan_content += f"**생성일**: {datetime.now().strftime('%Y-%m-%d')}\n\n"

        for week, (title, topic, days) in enumerate(study_topics, 1):
            plan_content += f"## 주차 {week}: {title} ({days}일)\n"

            # 해당 주제 자료 수집
            os.system(f'vis collect "{topic}" --top-k 10 --output study_materials/{title.replace(" ", "_")}.md')

            plan_content += f"- 자료: study_materials/{title.replace(' ', '_')}.md\n"
            plan_content += f"- 예상 소요: {days}일\n\n"

        # 계획 파일 저장
        with open(f"study_plan_{self.timestamp}.md", "w", encoding="utf-8") as f:
            f.write(plan_content)

        print(f"✅ 학습 계획 생성 완료: study_plan_{self.timestamp}.md")

    def organize_by_difficulty(self):
        """난이도별 자료 정리"""
        print("📚 난이도별 자료 정리 중...")

        difficulty_levels = {
            "기초": ["TDD 기본", "테스트 작성", "리팩토링 기초"],
            "중급": ["SOLID 원칙", "디자인 패턴", "아키텍처 기초"],
            "고급": ["DDD", "마이크로서비스", "성능 최적화"]
        }

        for level, topics in difficulty_levels.items():
            print(f"  📖 {level} 레벨 자료 수집...")
            os.makedirs(f"organized/{level}", exist_ok=True)

            for topic in topics:
                os.system(f'vis collect "{topic}" --top-k 8 --threshold 0.5 --output organized/{level}/{topic.replace(" ", "_")}.md')

if __name__ == "__main__":
    organizer = KnowledgeOrganizer()
    organizer.analyze_knowledge_gaps()
    organizer.create_study_plan()
    organizer.organize_by_difficulty()
```

---

## 🎯 특수 상황별 예제

### 예제 1: 대용량 Vault 처리 (10,000+ 문서)

```bash
# 설정 최적화
cat > config/large_vault_settings.yaml << EOF
model:
  batch_size: 8          # 메모리 절약

vault:
  excluded_dirs:         # 불필요한 디렉토리 제외
    - "archive/"
    - "backup/"
    - "temp/"
    - "old_projects/"

search:
  default_top_k: 50      # 더 많은 결과

duplicates:
  min_word_count: 100    # 짧은 문서 제외로 성능 향상
EOF

# 단계별 처리
vis reindex --config config/large_vault_settings.yaml --verbose
```

### 예제 2: 다국어 문서 처리

```bash
# 한영 혼합 문서 검색
vis search "Machine Learning 머신러닝"

# 영어 기술 문서 검색
vis search "Spring Boot Configuration" --threshold 0.4

# 한국어 개념 설명 문서
vis search "객체지향 프로그래밍 원칙" --top-k 15
```

### 예제 3: 프로젝트별 분리 검색

```python
#!/usr/bin/env python3
"""
프로젝트별 분리 검색 예제 (project_search.py)
"""
from src.features.advanced_search import SearchQuery

def search_by_project():
    """프로젝트별 검색"""

    projects = {
        "ecommerce": ["ecommerce/", "shopping/", "payment/"],
        "blog": ["blog/", "cms/", "content/"],
        "api": ["api/", "backend/", "server/"]
    }

    query_text = "API 설계 패턴"

    for project_name, paths in projects.items():
        print(f"🔍 {project_name} 프로젝트 검색:")

        # 특정 경로만 포함하는 검색 (구현 필요)
        # 현재는 전체 검색 후 결과 필터링
        results = engine.semantic_search(query_text, top_k=20)

        project_results = [
            r for r in results
            if any(path in r.document.path for path in paths)
        ]

        for result in project_results[:5]:
            print(f"  📄 {result.document.title}")
            print(f"     {result.document.path}")
```

---

---

## 🌟 실제 활용 사례

vault-intelligence를 활용한 실제 프로젝트 사례들입니다.

### 사례 1: AI Practice 기법 수집 프로젝트

286개의 AI 관련 문서에서 실용적인 기법들을 체계적으로 추출한 대규모 분석 프로젝트입니다.

**프로젝트 개요**:

- 기간: 2025-01-03 ~ 2026-01-04 (약 1개월)
- 대상: vault의 003-RESOURCES/AI 폴더 286개 문서
- 결과: **1,403개 AI 기법** 추출 (6개 카테고리)

**사용된 워크플로우**:

```bash
# 1. 주제별 문서 검색
vis search "AI 활용 기법" --search-method hybrid --top-k 30

# 2. 배치 처리를 위한 문서 목록 생성
vis collect "AI coding" --top-k 50 --output batch-input.md

# 3. 카테고리별 MOC 생성
vis generate-moc "Prompt Engineering" --top-k 30
vis generate-moc "AI Agent" --top-k 30
```

**핵심 성과**:

- 10개 문서 단위 배치 처리로 토큰 효율성 극대화
- 27개 세션에 걸쳐 체계적 진행
- 6개 카테고리로 분류 (AI-Assisted Development, Prompt Engineering, Agent & Workflow 등)

상세: [AI Practice 요약](../AI-PRACTICE-SUMMARY.md)

---

### 사례 2: AI 한계 분석 MOC 작성

AI의 한계에 대한 종합 분석 MOC 문서를 vault-intelligence로 작성한 사례입니다.

**프로젝트 목표**: AI 기술의 한계점을 체계적으로 분류하고, 대응 전략 도출

**사용된 워크플로우**:

```bash
# 1. 관련 문서 검색
vis search "AI 한계 limitations" --search-method hybrid --rerank --top-k 30

# 2. 주제별 수집
vis collect "AI 환각 hallucination" --top-k 15
vis collect "AI 비결정성 non-deterministic" --top-k 15

# 3. MOC 자동 생성
vis generate-moc "AI limitations" --top-k 50 --output AI-한계-MOC.md
```

**발견된 8가지 한계 영역**:

1. 비결정적 특성 (Non-deterministic)
2. 프롬프트 모호성
3. 내적 동기 부재
4. 환각(Hallucination) 현상
5. 본질적 복잡성 처리 불가
6. 컨텍스트 윈도우 한계
7. 코드 품질 문제
8. 창의성/예술적 한계

**결과물**: vault에 저장된 체계적인 MOC 문서, 관련 문서 30+ 개 연결

---

### 사례 3: 브런치 글 작성 지원

기술 블로그 글 작성을 vault-intelligence로 지원한 사례입니다.

**프로젝트 목표**: "AI 시대, 신입 개발자가 살아남는 법" 브런치 글 작성 지원

**사용된 워크플로우**:

```bash
# 1. 관련 자료 검색
vis search "AI 시대 개발자 역할" --rerank --expand --top-k 20

# 2. MOC로 구조화
vis generate-moc "주니어 개발자 생존" --top-k 30

# 3. 핵심 인용 자료 수집
vis collect "Specification Translation Verification" --top-k 15
```

**워크플로우 특징**:

- **Seed (씨앗)**: 초안 분석 + vault 검색으로 참고자료 제안
- **Skeleton (뼈대)**: MOC로 3-5개 섹션 구조 제안
- **Flesh (살)**: 각 섹션별 체크리스트 + 유도 질문
- **Polish (다듬기)**: 스타일 체크 (1인칭, 구어체, AI 표현 회피)
- **Publish (발행)**: 제목 후보 제안 + 포맷 정리

**결과물**: 체계적인 글 구조와 풍부한 참고자료를 기반으로 작성된 브런치 글

---

### 사례 4: 학습 리뷰 생성

주간/월간 학습 패턴을 분석하고 인사이트를 도출한 사례입니다.

```bash
# 주간 학습 리뷰
vis review --period weekly --output weekly-review.md

# 월간 학습 리뷰 (더 포괄적)
vis review --period monthly --output monthly-review.md

# 특정 주제 집중 리뷰
vis review --period weekly --topic "TDD"
```

**생성되는 인사이트**:

- 가장 많이 다룬 주제
- 학습 패턴 (집중 영역, 공백 영역)
- 관련 문서 클러스터
- 추천 학습 경로

---

**마지막 업데이트**: 2026-01-12
**문서 버전**: V2.2

이 예제들을 참고하여 여러분의 vault에 맞는 최적의 사용법을 찾아보세요! 🚀

