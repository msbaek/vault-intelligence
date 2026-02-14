# 검색 방법별 비교 분석

동일한 쿼리 "TDD"로 4가지 검색 방법과 다양한 옵션 조합을 실험하고, 각 결과의 차이와 원인을 분석한 문서입니다.

## 목차

1. [Keyword 검색](#keyword)
   - [--rerank - bad (짧은 쿼리에서 역효과)](#--rerank---bad)
   - [--expand - meaningful (동의어+HyDE 효과)](#--expand---meaningful)
   - [--with-centrality - meaningful](#--with-centrality---meaningful)
2. [Semantic 검색](#semantic)
   - [--rerank - meaningful (노이즈 제거 효과)](#--rerank---meaningful)
   - [Reranker 효과 분석](#reranker-효과-분석)
   - [--expand - 다국어 환경에선 유의미](#--expand---다국어-환경에선-유의미-가능)
   - [--expand --rerank](#--expand---rerank)
   - [--with-centrality](#--with-centrality)
3. [Hybrid 검색](#hybrid)
   - [--rerank (차이 적음)](#--rerank)
   - [Hybrid + Rerank 효과 분석](#hybrid--rerank-효과-분석)
   - [검색 방법별 rerank 효과 차이](#검색-방법별-rerank-효과-차이)
   - [권장 조합](#권장-조합)
4. [ColBERT 검색](#colbert)
   - [핵심 원리 (토큰별 독립 매칭)](#핵심-원리)
5. [검색 방법별 최적 쿼리 길이](#검색-방법별-최적-쿼리-길이)

---

## Keyword

- TDD

1. Clean Code Course by Uncle Bob
   유사도: 5.0000
2. Example - Book Management
   유사도: 5.0000
3. Unity Catalog - 데이터 관리 및 거버넌스 Labs
   유사도: 5.0000
4. 소프트웨어장인
   유사도: 5.0000
5. 클린 애자일(Back to Basics)
   유사도: 5.0000

### --rerank - bad

Cross-encoder의 판단

Reranker(cross-encoder)는 **"이 문서가 쿼리 'TDD'와 얼마나 관련 있는가?"**를 평가합니다.

- A 일기장: 짧은 글에서 TDD가 자주 나오니까 → "이 문서는 TDD 이야기로 가득하네" → 높은 점수
- B 교과서: 길고 다양한 내용 속에 TDD가 섞여 있으니까 → "TDD도 있지만 다른 얘기도 많네" → 상대적으로 낮은 점수

한 마디로, 진짜 TDD 전문 문서보다 TDD를 잠깐 언급한 짧은 메모가 더 높은 점수를 받는 역전 현상이 발생합니다.

해당 daily note 파일들은 실제로 "TDD"를 포함하고 있어 키워드 매칭 자체는 정확합니다.
| 파일 | TDD 언급 횟수 | 단어 수 | 예시 내용 |
|---|---|---|---|
| 2025-11-01.md | 5회 | 179 | "vault-intelligence: TDD 절차 블로그 콘텐츠 작성" |
| 2025-12-09.md | 3회 | 175 | (작업 로그에서 TDD 언급) |
| 2025-10-31.md | 5회 | 154 | (작업 로그에서 TDD 언급) |
이 파일들은 TDD를 주제로 다루는 문서가 아니라, 작업 로그에서 TDD 관련 활동을 간략히 기록한 문서입니다.

2단계(reranker)에서 과대평가되는 원인

BGE-reranker-v2-m3의 cross-encoder가 (query="TDD", document_content) 쌍의 관련도를 평가할 때:

- Daily note (179단어 중 TDD 5회) → TDD 밀도 약 2.8%
- Clean Code Course (TDD 전문 문서) → TDD가 다른 개념들 사이에서 설명됨

Cross-encoder는 "TDD"가 짧은 쿼리이기 때문에, 짧은 문서에서 TDD가 반복 등장하면 오히려 관련도를 높게 평가합니다.
즉: 짧은 문서 + 높은 키워드 밀도 = 과대평가

\_prepare_document_text가 2048자로 잘라내므로(line 234), 긴 TDD 전문 문서는 내용이 잘리는 반면, 짧은 daily note는 전체가
그대로 reranker에 전달되어 상대적으로 유리합니다.

요약
| 단계 | 동작 | 문제 |
|---|---|---|
| keyword 검색 | "TDD" 포함 문서 정상 매칭 | 없음 (정상) |
| reranker | cross-encoder 관련도 평가 | 짧은 daily note가 높은 키워드 밀도로 과대평가 |
근본 원인: Reranker가 "TDD에 관한 문서"와 "TDD를 잠깐 언급한 문서"를 구별하지 못합니다. 이는 cross-encoder의 한계이자, 짧은 쿼리의 한계입니다.

### --expand - meaningful

```zsh
INFO:src.features.query_expansion:동의어 발견: 3개
INFO:src.features.query_expansion:HyDE 문서 생성 완료: 161자
INFO:src.features.query_expansion:쿼리 확장 완료: 4개 용어, 방법: synonyms+hyde
INFO:src.features.advanced_search:쿼리 확장 완료: synonyms+hyde
INFO:src.features.advanced_search:확장 검색 완료: 6개 쿼리로 5개 결과
```

1. 켄트 백의 아규먼티드 코딩: TDD와 AI를 활용한 작동하는 깔끔한 코드
   유사도: 52.7118
2. TDD-Theme & Variations
   유사도: 43.6235
3. TDD, Where Did It All Go Wrong (Ian Cooper)
   유사도: 42.6706
4. 클린 코더스 강의 7. TDD 1
   유사도: 41.7529
5. 테스트 주도적 사고로 두뇌 재배선하기 - C++ TDD 완전 가이드
   유사도: 41.2941

### --with-centrality - meaningful

1. Clean Code Course by Uncle Bob
   유사도: 5.0000
2. Example - Book Management
   유사도: 5.0000
3. Unity Catalog - 데이터 관리 및 거버넌스 Labs
   유사도: 5.0000
4. 소프트웨어장인
   유사도: 5.0000
5. 클린 애자일(Back to Basics)
   유사도: 5.0000

## semantic

- Test Driven Development Red Green Refactor

1. TDD
   유사도: 0.6124
2. 개발 문화
   유사도: 0.6079
3. TDD + AI 통합 워크플로우
   유사도: 0.6065
4. Test Driven TDD and Acceptance TDD for java Developers - Manning.pdf
   유사도: 0.6029
5. Test-Driven Development: It's easier than you think
   유사도: 0.6021

### --rerank - meaningful

1. Test-Driven Generation: Adopting TDD With GenAI
   유사도: 3.1543
2. TDD와 리팩토링의 원칙 및 기법
   유사도: 2.4980
3. TDD + AI 통합 워크플로우
   유사도: 1.9248
4. TDD와 리팩토링 워크숍 목차 (2일, 14시간)
   유사도: 1.4434
5. 마틴 파울러-리팩토링의 중요성 feat.테스트 코드를 짜는 이유
   유사도: 0.7041

#### Reranker 효과 분석

--rerank가 keyword보다 semantic에서 좋은 결과가 나오는 것이 보다 일반적인 현상입니다.

**Reranker의 효과는 1단계 후보 풀의 품질에 달려 있습니다.** Reranker는 주어진 후보를 재정렬만 합니다. 새 문서를 찾아오지는 못합니다.

**Keyword + Rerank**

1단계: "TDD" 포함 문서만 수집 (좁은 그물)
→ TDD 언급 daily note ✓
→ "테스트 주도 개발"만 쓴 문서 ✗ (탈락)
→ "Red Green Refactor" 문서 ✗ (탈락)

2단계: Reranker가 재정렬
→ 이미 빠진 문서는 복구 불가

**Semantic + Rerank**

1단계: 의미적으로 유사한 문서 수집 (넓은 그물)
→ TDD 언급 문서 ✓
→ "테스트 주도 개발" 문서 ✓
→ "Red Green Refactor" 문서 ✓
→ 장거리 라이딩 같은 노이즈도 ✓ (섞임)

2단계: Reranker가 재정렬
→ 노이즈 제거, 진짜 관련 문서를 상위로

핵심
| | 1단계 역할 | Reranker 역할 |
|---|---|---|
| **Keyword** | 정확하지만 좁은 후보 | 이미 좁은 풀 안에서 재정렬 (개선 여지 적음) |
| **Semantic** | 넓지만 노이즈 섞인 후보 | 노이즈 제거 + 정밀 순위 조정 (개선 여지 큼) |

Semantic 검색은 recall(재현율)이 높고 precision(정밀도)이 낮은 특성이 있고, reranker는 precision을 높이는 도구입니다. 서로 약점을 보완하는 조합이라 효과가 좋습니다.

이것은 정보 검색(IR) 분야에서 **"retrieve and rerank"**라고 불리는 표준 패턴이고, semantic retrieval + cross-encoder
reranking 조합이 가장 좋은 성능을 보인다는 것이 일반적인 결론입니다.

### --expand - 다국어 환경에선 유의미 가능

1. TDD
   유사도: 0.6124
2. 개발 문화
   유사도: 0.6079
3. TDD + AI 통합 워크플로우
   유사도: 0.6065
4. Test Driven TDD and Acceptance TDD for java Developers - Manning.pdf
   유사도: 0.6029
5. Test-Driven Development: It's easier than you think
   유사도: 0.6021

### --expand --rerank

1. TDD
   유사도: 0.6124
2. 개발 문화
   유사도: 0.6079
3. TDD + AI 통합 워크플로우
   유사도: 0.6065
4. Test Driven TDD and Acceptance TDD for java Developers - Manning.pdf
   유사도: 0.6029
5. Test-Driven Development: It's easier than you think
   유사도: 0.6021

### --with-centrality

1. TDD
   유사도: 0.6124
2. 개발 문화
   유사도: 0.6079
3. TDD + AI 통합 워크플로우
   유사도: 0.6065
4. Test Driven TDD and Acceptance TDD for java Developers - Manning.pdf
   유사도: 0.6029
5. Test-Driven Development: It's easier than you think
   유사도: 0.6021

## hybrid

- TDD Red Green Refactor 사이클

1. 클린 코더스 강의 7. TDD 1
   유사도: 6.6000
2. TDD와 리팩토링의 원칙 및 기법
   유사도: 6.6000
3. Claude Code에 Superpowers를 부여하다: AI를 노련한 시니어 엔지니어로 변화시킨 방법
   유사도: 6.6000
4. AI-vs-TDD
   유사도: 6.3000
5. TDD, Where Did It All Go Wrong (Ian Cooper)
   유사도: 6.1106

### --rerank

1. 클린 코더스 강의 7. TDD 1
   유사도: 4.1836
2. TDD와 리팩토링 워크숍 목차 (2일, 14시간)
   유사도: 4.0391
3. TDD가 AI 지원 개발 워크플로우에서 가지는 의미
   유사도: 3.4902
4. Claude Code에 Superpowers를 부여하다: AI를 노련한 시니어 엔지니어로 변화시킨 방법
   유사도: 2.2266
5. How to fall in love with TDD
   유사도: 2.1719

#### Hybrid + Rerank 효과 분석

hybrid + rerank에서 차이가 적은 건 충분히 예상 가능한 현상입니다.

Hybrid 검색은 이미 "자체 검증"이 내장되어 있습니다.

Hybrid = BM25(keyword) × 0.3 + Dense(semantic) × 0.7

- keyword에서 높고 semantic에서 낮은 문서 → 점수 희석
- semantic에서 높고 keyword에서 낮은 문서 → 점수 희석
- 둘 다 높은 문서만 상위에 올라감 → 이미 노이즈가 걸러진 상태

반면 reranker의 주 역할은 노이즈 필터링입니다. 이미 깨끗한 결과에 reranker를 적용하면 순서를 약간 조정할 뿐 큰 변화가
없습니다.

#### 검색 방법별 rerank 효과 차이

| 검색 방법     | 초기 노이즈 수준           | rerank 효과           |
| ------------- | -------------------------- | --------------------- |
| semantic 단독 | 높음 (짧은 쿼리 시 특히)   | 큼 - 노이즈 제거 효과 |
| keyword 단독  | 중간 (키워드 빈도 편향)    | 중간                  |
| hybrid        | 낮음 (두 신호가 상호 검증) | 작음 - 이미 깨끗      |

비유

- semantic + rerank = 넓게 그물을 던진 뒤 수작업으로 골라내기 (효과 큼)
- hybrid + rerank = 이미 정밀 그물로 잡은 것을 다시 골라내기 (효과 작음)

#### 권장 조합

hybrid 검색에서는 --rerank를 생략해도 품질이 거의 동일하면서 속도가 빠릅니다. rerank는 cross-encoder 추론이 추가되므로
불필요한 비용입니다.

권장 조합:

- 일반 검색: hybrid (기본값, 빠르고 충분히 정확)
- 정밀 검색: semantic --rerank (넓은 후보 + 정밀 필터링)
- 정확한 용어: keyword (고유명사, 파일명 등)

## ColBERT

- Kent Beck TDD Red Green Refactor 리팩토링 설계 개선

1. X-Additionals
   유사도: 0.6869
2. TDD, Where Did It All Go Wrong (Ian Cooper)
   유사도: 0.6536
3. TDD
   유사도: 0.6525
4. TDD와 Refactoring 관련 리소스 모음
   유사도: 0.6428
5. TDD, Where Did It All Go Wrong (Ian Cooper)
   유사도: 0.6370

### 핵심 원리

Semantic: Query → [하나의 벡터] ↔ Doc → [하나의 벡터]
"여러 개념이 하나로 뭉개짐"

ColBERT: Query → [토큰1][토큰2][토큰3]...
Doc → [토큰A][토큰B][토큰C]...
각 쿼리 토큰이 가장 가까운 문서 토큰과 매칭
"개념별로 독립 매칭 → 합산"

요약: ColBERT에는 **"이것도 포함하고 저것도 포함하고 그것도 포함된 문서"**를 찾는 체크리스트형 쿼리가 가장 효과적입니다.

## 검색 방법별 최적 쿼리 길이

| 검색 방법 | 최적 쿼리                                                       | 비유                             |
| --------- | --------------------------------------------------------------- | -------------------------------- |
| keyword   | TDD, Clean Code                                                 | 사전에서 단어 찾기               |
| semantic  | 테스트 주도 개발 방법론과 설계 개선 (10-15단어)                 | 사서에게 주제 설명하기           |
| colbert   | Kent Beck TDD Red Green Refactor 리팩토링 설계 개선 (15-25단어) | 사서에게 체크리스트 주기         |
| hybrid    | 중간 길이 (10-15단어)                                           | 사서에게 주제 + 키워드 함께 전달 |
