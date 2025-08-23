# 📚 Vault Intelligence System V2 사용자 가이드

Obsidian vault를 위한 완전한 지능형 검색 및 분석 시스템 사용법

## 🚀 빠른 시작

### 1. 시스템 초기화
```bash
# 기본 vault 경로로 초기화
python -m src init

# 사용자 정의 vault 경로
python -m src init --vault-path /path/to/your/vault
```

### 2. 시스템 테스트
```bash
python -m src test
```

#### 테스트 결과 해석
```
🧪 시스템 테스트 실행 중...

1️⃣ Sentence Transformer 엔진 테스트
✅ BGE-M3 모델 로딩 성공
✅ 임베딩 생성 테스트 (1024차원)
✅ 유사도 계산 검증

2️⃣ 임베딩 캐시 테스트
✅ SQLite 데이터베이스 연결
✅ 캐시 저장/로드 테스트
✅ 중복 캐시 방지 검증

3️⃣ Vault 프로세서 테스트
✅ 마크다운 파일 파싱
✅ 메타데이터 추출 (태그, 제목)
✅ 파일 필터링 검증

📊 테스트 결과: 3/3 통과
```

#### 개별 모듈 테스트
```bash
# Phase 5/6 고급 기능 개별 테스트
python -c "from src.features.reranker import test_reranker; test_reranker()"
python -c "from src.features.colbert_search import test_colbert_search; test_colbert_search()"
python -c "from src.features.query_expansion import test_query_expansion; test_query_expansion()"
python -c "from src.features.knowledge_graph import test_knowledge_graph; test_knowledge_graph()"
```

### 3. 첫 검색 (자동 인덱싱)
```bash
python -m src search --query "TDD"
```

## 🔍 검색 기능

### 기본 검색 모드
```bash
# 1. 기본 하이브리드 검색 (빠르고 균형잡힌 결과)
python -m src search --query "테스트 주도 개발"

# 2. 의미적 검색 (개념 중심)
python -m src search --query "TDD" --search-method semantic

# 3. 키워드 검색 (정확한 매칭)
python -m src search --query "리팩토링" --search-method keyword

# 4. ColBERT 토큰 수준 검색 (세밀한 매칭)
python -m src search --query "클린 코드" --search-method colbert
```

### 🎯 고급 검색 기능 (Phase 5)

#### 1️⃣ **재순위화 검색** (`--rerank`) - 최고 정확도
```bash
python -m src search --query "TDD" --rerank

# 작동 방식:
# 1. 하이브리드 검색으로 상위 30개 후보 추출
# 2. Cross-encoder (BAAI/bge-reranker-v2-m3)로 정밀 재순위화
# 3. 최고 관련성 문서가 상위로 재배치
```

#### 2️⃣ **쿼리 확장 검색** (`--expand`) - 최대 포괄성
```bash
python -m src search --query "TDD" --expand

# 작동 방식:
# 1. 동의어 확장: TDD → "테스트 주도 개발", "Test Driven Development"
# 2. HyDE 생성: 161자 분량의 가상 문서 생성
# 3. 6개 쿼리로 병렬 검색 후 결과 통합
```

#### 3️⃣ **동의어만 확장** (`--expand --no-hyde`)
```bash
python -m src search --query "TDD" --expand --no-hyde

# 한국어↔영어 동의어만 사용
# 빠른 확장 검색, 용어 중심
```

#### 4️⃣ **HyDE만 활용** (`--expand --no-synonyms`)
```bash
python -m src search --query "TDD" --expand --no-synonyms

# 가상 문서로 맥락 확장
# 개념적 유사성 포착
```

#### 5️⃣ **최고 성능 모드** (`--rerank --expand`)
```bash
python -m src search --query "TDD" --rerank --expand

# 모든 기능 결합:
# 1. 쿼리 확장 (동의어 + HyDE)
# 2. 다중 검색 및 통합
# 3. Cross-encoder 재순위화
# 최고 품질, 3-5초 소요
```

### 검색 옵션 조합
```bash
# 상위 20개, 높은 정확도, 재순위화
python -m src search \
  --query "SOLID principles" \
  --top-k 20 \
  --threshold 0.5 \
  --rerank

# 포괄적 검색, 동의어만 사용
python -m src search \
  --query "마이크로서비스" \
  --expand \
  --no-hyde \
  --top-k 30
```

### 검색 결과 해석
```
📄 검색 결과 (3개):
--------------------------------------------------------------------------------
1. Clean Architecture 책 정리        # 1위 결과
   경로: 997-BOOKS/clean-architecture.md
   유사도: 2.8542                     # 높을수록 관련성 높음
   타입: hybrid_expanded_reranked     # 확장 + 재순위화
   키워드: solid, principles          # 매칭된 키워드
   내용: SOLID 원칙은 객체지향...      # 미리보기 스니펫
```

#### 검색 타입 설명
- **`semantic`**: 의미적 검색 (개념 기반)
- **`keyword`**: 키워드 검색 (정확한 단어 매칭)
- **`hybrid`**: 하이브리드 검색 (의미적 + 키워드)
- **`colbert`**: ColBERT 토큰 수준 검색
- **`*_reranked`**: Cross-encoder로 재순위화된 결과
- **`*_expanded_*`**: 쿼리 확장이 적용된 결과
  - `*_original`**: 원본 쿼리 결과
  - `*_synonym`**: 동의어 확장 결과  
  - `*_hyde`**: HyDE 가상 문서 결과

## 🕸️ 지식 그래프 기능 (Phase 6)

### 관련 문서 추천

특정 문서와 관련된 문서들을 스마트하게 추천받을 수 있습니다.

```bash
# 기본 관련 문서 추천
python -m src related --file "클린 애자일(Back to Basics)" --top-k 5

# 전체 경로로 지정
python -m src related --file "/full/path/to/document.md" --top-k 10

# 더 많은 추천 결과
python -m src related --file "TDD 가이드" --top-k 20

# 관련성 임계값 조정
python -m src related --file "클린코드" --similarity-threshold 0.5 --top-k 15

# 낮은 임계값으로 포괄적 추천
python -m src related --file "리팩토링" --similarity-threshold 0.2 --top-k 30

# 상세 로그와 함께
python -m src related --file "DDD" --verbose --top-k 10
```

#### 관련성 임계값 가이드
| 임계값 | 추천 특성 | 사용 상황 |
|--------|-----------|----------|
| 0.1 ~ 0.2 | 매우 포괄적, 약간의 연관성도 포함 | 브레인스토밍, 아이디어 발굴 |
| 0.3 ~ 0.4 | 균형잡힌 추천 (기본값) | 일반적인 관련 문서 찾기 |
| 0.5 ~ 0.7 | 높은 관련성, 엄선된 결과 | 정확한 참조 문서 필요 |
| 0.7+ | 매우 유사한 문서만 | 중복 문서나 동일 주제 변형 찾기 |

#### 결과 해석
```
📄 관련 문서 (5개):
--------------------------------------------------------------------------------
1. 소프트웨어장인
   경로: /Users/msbaek/DocumentsLocal/msbaek_vault/997-BOOKS/소프트웨어장인.md
   관련도: 0.9041                    # 높을수록 관련성 높음
   타입: related_semantic            # 관련성 타입
   태그: source/book, topic/career/software-artisan, topic/professional-development
   내용: 소프트웨어장인이란 개발에 대한 프로다운 자세와...
```

#### 관련성 계산 방식
- **의미적 유사도** (50%): BGE-M3 임베딩 기반 문서 내용 유사성
- **태그 유사도** (30%): 공통 태그 기반 주제 연관성  
- **중심성 점수** (20%): 지식 그래프에서의 문서 중요도

### 중심성 기반 검색 랭킹

문서의 중요도(중심성)를 검색 결과에 반영하여 핵심 문서를 우선 노출합니다.

```bash
# 중심성 점수 반영 검색
python -m src search --query "TDD" --with-centrality --top-k 10

# 일반 검색과 비교
python -m src search --query "TDD" --top-k 10
```

#### 중심성 점수란?
- **PageRank**: 다른 문서들과 얼마나 많이 연결되어 있는가
- **근접 중심성**: 전체 지식 네트워크에서 얼마나 중심에 위치하는가  
- **매개 중심성**: 다른 문서들 사이의 연결 다리 역할을 하는가

### 지식 공백 분석

vault 내에서 고립되거나 연결이 약한 문서들을 찾아 지식 체계를 개선할 수 있습니다.

```bash
# 기본 지식 공백 분석
python -m src analyze-gaps --top-k 10

# 더 상세한 분석
python -m src analyze-gaps --top-k 20

# 연결 기준 조정 (더 엄격한 고립 판정)
python -m src analyze-gaps --min-connections 5 --top-k 15

# 유사도 임계값 조정
python -m src analyze-gaps --similarity-threshold 0.4 --min-connections 3

# 결과를 파일로 저장
python -m src analyze-gaps --output knowledge_gaps.json --top-k 50

# 상세 분석 로그
python -m src analyze-gaps --verbose --top-k 30
```

#### 분석 매개변수 가이드

**최소 연결 수 (`--min-connections`)**
- `1-2`: 관대한 기준, 더 많은 약한 연결 문서 감지
- `3-4`: 기본 기준, 균형잡힌 분석
- `5+`: 엄격한 기준, 진짜 고립된 문서만 감지

**유사도 임계값 (`--similarity-threshold`)**
- `0.2-0.3`: 약한 연관성도 연결로 인정
- `0.3-0.4`: 기본 기준, 의미있는 연관성만 인정
- `0.4+`: 강한 연관성만 연결로 인정

#### 분석 결과 해석
```
📊 지식 공백 분석 결과:
--------------------------------------------------
전체 문서: 2291개
고립 문서: 45개                    # 다른 문서와 연결이 약한 문서
약한 연결 문서: 128개               # 연결은 있지만 충분하지 않은 문서
고립 태그: 892개                   # 사용 빈도가 낮은 태그
고립률: 7.5%                      # 전체 대비 고립 문서 비율

🏷️ 고립된 태그들 (상위 10개):
  - philosophy/kent-beck: useful.questions
  - principles/abstraction: useful.questions  
  - project/ai-assisted-research: useful.questions

📈 주요 태그 분포:
  - topic/code-review: 184개 문서
  - status/active: 171개 문서
  - technology/java: 169개 문서
```

#### 개선 방안
- **고립 문서**: 관련 태그 추가, 다른 문서와 연결점 생성
- **고립 태그**: 태그 체계 정리, 유사 태그 통합
- **약한 연결**: 문서 간 참조 링크 추가, 내용 보강

### 지식 그래프 시각화 (향후 기능)

현재는 CLI 기반 분석을 제공하며, 향후 웹 인터페이스에서 시각적 그래프를 제공할 예정입니다.

## 🔎 중복 문서 감지

### 기본 중복 감지
```bash
python -m src duplicates
```

### 결과 해석
```
📊 중복 분석 결과:
--------------------------------------------------
전체 문서: 2,407개
중복 그룹: 15개                      # 중복된 그룹 수
중복 문서: 45개                      # 중복된 총 문서 수
고유 문서: 2,362개                   # 고유한 문서 수
중복 비율: 1.9%                      # 전체 대비 중복 비율

📋 중복 그룹 상세:
그룹 dup_001:
  문서 수: 3개
  평균 유사도: 0.9123              # 그룹 내 평균 유사도
    - 003-RESOURCES/TDD/basic.md (120단어)
    - 997-BOOKS/tdd-summary.md (150단어)
    - INBOX/tdd-notes.md (95단어)
```

## 📚 주제별 문서 수집

### 기본 수집
```bash
# 주제별 문서 자동 수집
python -m src collect --topic "리팩토링"

# 파일로 저장
python -m src collect --topic "TDD" --output tdd_collection.md

# 고품질 문서만 (높은 임계값)
python -m src collect --topic "클린 코드" --threshold 0.6 --top-k 20
```

### 쿼리 확장 수집 🆕

쿼리 확장을 통해 더 포괄적이고 정확한 문서 수집이 가능합니다.

```bash
# 기본 확장 수집 (동의어 + HyDE)
python -m src collect --topic "TDD" --expand

# 동의어만 확장 (HyDE 제외)
python -m src collect --topic "리팩토링" --expand --no-hyde

# HyDE만 활용 (동의어 제외)
python -m src collect --topic "아키텍처" --expand --no-synonyms

# 확장 + 낮은 임계값으로 포괄적 수집
python -m src collect --topic "도메인 모델링" --expand --threshold 0.1 --top-k 30

# 확장 + 결과 파일 저장
python -m src collect --topic "클린 코드" --expand --output clean_code_expanded.md
```

#### 확장 검색 비교 예시

**"TDD" 주제 수집 결과 비교:**

| 방법 | 문서 수 | 단어 수 | 주요 특징 |
|------|---------|---------|-----------|
| 기본 수집 | 5개 | 22,032개 | clean-coders 시리즈 중심 |
| 확장 수집 | 5개 | 24,042개 | 더 다양한 TDD 리소스 포함 |

#### 확장 기능 설명
- **동의어 확장**: 한국어 동의어 사전을 활용하여 관련 용어로 검색 범위 확대
- **HyDE (Hypothetical Document Embeddings)**: AI가 가상 문서를 생성하여 의미적 검색 정확도 향상
- **하이브리드 융합**: Dense + Sparse + 확장 쿼리를 RRF(Reciprocal Rank Fusion)로 최적 결합

### 수집 결과
```
📊 수집 결과:
--------------------------------------------------
주제: 리팩토링
수집 문서: 12개
총 단어수: 25,420개
총 크기: 247.3KB

🏷️ 태그 분포:                      # 수집된 문서의 태그 분석
  refactoring/techniques: 5개
  clean-code/principles: 3개
  testing/tdd: 2개

📁 디렉토리 분포:                    # 문서 위치 분석
  003-RESOURCES/: 8개
  997-BOOKS/: 3개
  SLIPBOX/: 1개
```

## 📊 주제 분석 및 클러스터링

### 전체 vault 주제 분석
```bash
python -m src analyze
```

### 분석 결과
```
📊 주제 분석 결과:
--------------------------------------------------
분석 문서: 2,407개
발견 주제: 25개
클러스터링 방법: K-means

🏷️ 주요 주제들:
주제 1: 소프트웨어 개발 방법론
  문서 수: 342개
  주요 키워드: TDD, 애자일, 스크럼, 개발프로세스, 방법론
  설명: 테스트 주도 개발과 애자일 방법론 관련 문서들...

주제 2: 코드 품질 및 리팩토링
  문서 수: 198개
  주요 키워드: 리팩토링, 클린코드, SOLID, 디자인패턴
```

## 📚 MOC(Map of Content) 자동 생성 (Phase 8) 🆕

### 개요
MOC(Map of Content)는 특정 주제에 대한 체계적인 탐색 가이드로, 관련 문서들을 카테고리별로 분류하고 학습 경로를 제공합니다. Obsidian vault에서 지식을 효과적으로 탐색할 수 있도록 구조화된 목차 문서를 자동으로 생성합니다.

### 주요 특징
- **6가지 카테고리 자동 분류**: 입문/기초, 개념/이론, 실습/예제, 도구/기술, 심화/고급, 참고자료
- **학습 경로 생성**: 난이도와 선후 관계를 고려한 단계별 가이드
- **핵심 문서 선정**: 중요도 점수 기반 주제별 필수 문서 추천
- **관련 주제 추출**: 태그와 내용 분석을 통한 연관 주제 발견
- **Obsidian 최적화**: 즉시 사용 가능한 마크다운 형식 출력

### 기본 사용법

#### 기본 MOC 생성
```bash
python -m src generate-moc --topic "TDD"
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
문서 관계: 0개

📋 카테고리별 문서 분포:
  입문/기초: 5개 문서
  개념/이론: 6개 문서
  실습/예제: 9개 문서
  도구/기술: 9개 문서
  심화/고급: 7개 문서
  참고자료: 7개 문서

💾 MOC 파일이 MOC-TDD.md에 저장되었습니다.
```

#### 고급 옵션
```bash
# 사용자 정의 출력 파일
python -m src generate-moc --topic "TDD" --output "TDD-완전정리.md"

# 더 많은 문서 포함
python -m src generate-moc --topic "리팩토링" --top-k 50

# 연결되지 않은 문서도 포함
python -m src generate-moc --topic "아키텍처" --include-orphans

# 임계값 조정 (더 포괄적인 수집)
python -m src generate-moc --topic "클린코드" --threshold 0.2 --top-k 30
```

### MOC 문서 구조

생성되는 MOC 문서는 다음과 같은 구조를 가집니다:

```markdown
# 📚 TDD Map of Content

## 🎯 개요
- 총 문서 수, 단어 수, 주요 태그 등 통계 정보

## 🌟 핵심 문서 (Top 5)
- 가장 중요하고 핵심적인 문서들
- 단어 수와 주요 태그 표시

## 📖 카테고리별 분류
### 입문/기초
- 주제에 대한 첫 걸음과 기본 개념

### 개념/이론
- 핵심 개념과 이론적 배경

### 실습/예제
- 실제 적용 사례와 연습 문제

### 도구/기술
- 관련 도구와 기술 스택

### 심화/고급
- 전문적이고 깊이 있는 내용

### 참고자료
- 추가 학습을 위한 참고 자료

## 🛤️ 추천 학습 경로
- 체계적인 학습을 위한 단계별 가이드
- 각 단계별 난이도와 추천 문서

## 🔗 관련 주제
- 이 주제와 연관된 다른 주제들

## 📅 최근 업데이트
- 최근 30일 이내 업데이트된 문서들

## 📊 문서 관계도
- 주요 문서들 간의 관련성 시각화

## 📈 통계
- 상세한 문서 및 관계 통계
```

### 카테고리 분류 시스템

MOC는 다음 키워드를 기반으로 문서를 자동 분류합니다:

#### 1. **입문/기초** 카테고리
- **키워드**: 입문, 시작, 기초, 기본, 소개, 개요, introduction, basic, fundamental
- **용도**: 주제에 처음 접근하는 사용자를 위한 문서

#### 2. **개념/이론** 카테고리  
- **키워드**: 개념, 이론, 원리, 정의, concept, theory, principle, definition
- **용도**: 핵심 개념과 이론적 배경을 다루는 문서

#### 3. **실습/예제** 카테고리
- **키워드**: 실습, 예제, 연습, 실전, 구현, practice, example, exercise
- **용도**: 실제 적용 사례와 연습 문제를 다루는 문서

#### 4. **도구/기술** 카테고리
- **키워드**: 도구, 툴, 기술, 방법, tool, technique, method, framework
- **용도**: 관련 도구와 기술 스택을 다루는 문서

#### 5. **심화/고급** 카테고리
- **키워드**: 심화, 고급, 전문, 상세, advanced, deep, expert, detailed
- **용도**: 전문적이고 깊이 있는 내용을 다루는 문서

#### 6. **참고자료** 카테고리
- **키워드**: 참고, 자료, 리소스, 문서, reference, resource, documentation
- **용도**: 추가 학습을 위한 참고 자료

### 활용 팁

#### 주제 선택 가이드
```bash
# ✅ 좋은 주제 예시 (구체적이고 명확한 주제)
python -m src generate-moc --topic "TDD"
python -m src generate-moc --topic "리팩토링"
python -m src generate-moc --topic "Spring Boot"
python -m src generate-moc --topic "도메인 주도 설계"

# ❌ 피해야 할 주제 예시 (너무 광범위하거나 모호한 주제)
python -m src generate-moc --topic "프로그래밍"  # 너무 광범위
python -m src generate-moc --topic "공부"        # 너무 모호
```

#### 임계값 조정 가이드
- **0.1-0.2**: 매우 포괄적 (관련성이 낮아도 포함)
- **0.3**: 기본값 (균형잡힌 수집)
- **0.4-0.5**: 엄격한 기준 (매우 관련성 높은 문서만)

#### 문서 수 가이드
- **--top-k 10-20**: 핵심만 간추린 MOC
- **--top-k 30-50**: 표준적인 MOC (권장)
- **--top-k 100+**: 매우 포괄적인 MOC

### 설정 옵션 (config/settings.yaml)

```yaml
moc:
  max_core_documents: 5      # 핵심 문서 최대 수
  max_category_documents: 10 # 카테고리별 최대 문서 수
  recent_days: 30           # 최근 업데이트 기준 일수
  min_similarity_threshold: 0.3  # 최소 유사도 임계값
  relationship_threshold: 0.6    # 관계 판정 임계값
```

### 프로그래밍 방식 사용

```python
from src.features.moc_generator import MOCGenerator
from src.features.advanced_search import AdvancedSearchEngine

# MOC 생성기 초기화
engine = AdvancedSearchEngine(vault_path, cache_dir, config)
moc_generator = MOCGenerator(engine, config)

# MOC 생성
moc_data = moc_generator.generate_moc(
    topic="TDD",
    top_k=50,
    threshold=0.3,
    include_orphans=False,
    use_expansion=True,
    output_file="TDD-MOC.md"
)

# 결과 접근
print(f"총 문서: {len(moc_data.documents)}")
print(f"카테고리: {len(moc_data.categories)}")
print(f"학습 단계: {len(moc_data.learning_path)}")
```

### 문제 해결

#### MOC 생성이 안 될 때
```bash
# 1. 임계값을 낮춰서 다시 시도
python -m src generate-moc --topic "TDD" --threshold 0.2

# 2. 더 많은 문서 포함
python -m src generate-moc --topic "TDD" --top-k 100

# 3. 연결되지 않은 문서도 포함
python -m src generate-moc --topic "TDD" --include-orphans
```

#### 문서가 잘못 분류될 때
- 문서 제목과 내용에 카테고리 키워드를 명확히 포함
- 태그를 체계적으로 활용 (`#topic/tdd/basic`, `#type/tutorial` 등)

#### MOC가 너무 클 때
```bash
# 임계값 높이기
python -m src generate-moc --topic "TDD" --threshold 0.4

# 문서 수 제한
python -m src generate-moc --topic "TDD" --top-k 20
```

## 🏷️ 자동 태깅 시스템 (Phase 7)

### 개요

Phase 7에서 새로 추가된 BGE-M3 기반 지능형 태깅 시스템입니다. 기존 vault의 태그 패턴을 학습하여 일관성 있는 태그를 자동으로 생성합니다.

### 주요 특징
- **BGE-M3 의미 분석**: 1024차원 임베딩으로 문서 내용 이해
- **기존 태그 학습**: Vault의 기존 태그 패턴을 분석하여 일관된 태그 생성
- **계층적 구조**: `/` 구분자를 사용한 체계적 태그 구조
- **5대 카테고리**: Topic, Document Type, Source, Patterns, Frameworks
- **폴더별 처리**: 대용량 vault의 점진적 태깅 지원

### 기본 사용법

#### 단일 문서 태깅
```bash
# 절대 경로로 태깅
python -m src tag "/full/path/to/document.md"

# Vault 상대 경로로 태깅
python -m src tag "997-BOOKS/clean-code.md"

# 파일명만으로 태깅 (자동 검색)
python -m src tag "clean-code.md"

# Dry-run 모드 (실제 적용하지 않고 미리보기)
python -m src tag "document.md" --dry-run
```

#### 폴더별 일괄 태깅
```bash
# 특정 폴더 일괄 태깅
python -m src tag "997-BOOKS/"

# 여러 폴더 동시 태깅
python -m src tag "997-BOOKS/" "003-RESOURCES/" "000-SLIPBOX/"

# 대용량 폴더 점진적 처리 (배치 단위)
python -m src tag "large-folder/" --batch-size 50
```

#### 고급 옵션
```bash
# 기존 태그 무시하고 완전히 새로 생성
python -m src tag "document.md" --replace-existing

# 상세 진행률 표시
python -m src tag "folder/" --verbose

# 특정 카테고리만 태깅
python -m src tag "document.md" --categories "topic,source"

# 태그 수 제한
python -m src tag "document.md" --max-tags-per-category 3
```

### 태깅 규칙 체계

시스템은 `~/dotfiles/.claude/commands/obsidian/add-tag.md`의 규칙을 따라 다음 5개 카테고리로 태그를 생성합니다:

#### 1. **Topic** 카테고리
```
topic/programming/tdd
topic/architecture/clean-architecture
topic/career/software-craftsmanship
```

#### 2. **Document Type** 카테고리
```
type/book
type/article
type/note
type/tutorial
```

#### 3. **Source** 카테고리
```
source/book
source/blog
source/course
source/personal
```

#### 4. **Patterns** 카테고리
```
patterns/design-patterns
patterns/refactoring-patterns
patterns/architectural-patterns
```

#### 5. **Frameworks** 카테고리
```
frameworks/spring
frameworks/react
frameworks/testing-frameworks
```

### 태깅 결과 예시

#### 입력 문서
```markdown
---
title: Clean Code 책 정리
---

# Clean Code 정리

로버트 마틴의 Clean Code 책을 읽고 정리한 내용입니다.
SOLID 원칙과 리팩토링 기법에 대해 다룹니다.
```

#### 생성된 태그
```yaml
---
title: Clean Code 책 정리
tags:
  - topic/programming/clean-code
  - topic/principles/solid
  - topic/code-quality/refactoring
  - type/book-summary
  - source/book
  - patterns/refactoring-patterns
---
```

### 설정 옵션 (config/settings.yaml)

```yaml
semantic_tagging:
  # 모델 설정
  model:
    name: "BAAI/bge-m3"
    dimension: 1024
    batch_size: 4
    max_length: 4096
    use_fp16: true
    device: null

  # 기존 태그 학습 설정
  existing_tags:
    enable_learning: true
    similarity_threshold: 0.7
    min_tag_frequency: 2
    max_suggestions_per_category: 5

  # 태그 정규화 규칙
  normalization:
    convert_to_lowercase: true
    replace_spaces_with_dashes: true
    remove_special_chars: true
    max_tag_length: 50

  # 카테고리별 제한
  categories:
    topic:
      max_tags: 5
      min_confidence: 0.3
    type:
      max_tags: 2
      min_confidence: 0.4
    source:
      max_tags: 1
      min_confidence: 0.5
    patterns:
      max_tags: 3
      min_confidence: 0.3
    frameworks:
      max_tags: 3
      min_confidence: 0.3

  # 처리 설정
  processing:
    batch_size: 50
    progress_report_interval: 10
    dry_run_by_default: false
    replace_existing_tags: false
    backup_original_frontmatter: true
```

### 성능 및 사용 팁

#### 처음 사용 시 권장 순서
1. **Dry-run 테스트**: 몇 개 문서로 결과 확인
2. **소규모 폴더**: 중요하지 않은 폴더부터 시작
3. **점진적 확장**: 만족스러우면 전체 vault로 확장

#### 배치 크기 가이드
- **소규모** (< 100 문서): `--batch-size 20`
- **중규모** (100~1000 문서): `--batch-size 50` (기본값)
- **대규모** (> 1000 문서): `--batch-size 100`

#### 태그 품질 향상 팁
```bash
# 1. 기존 태그가 많은 문서들 먼저 처리 (학습 데이터 증가)
python -m src tag "well-tagged-folder/" --verbose

# 2. 유사한 문서들을 그룹으로 처리
python -m src tag "997-BOOKS/" --batch-size 30

# 3. 결과 확인 후 설정 조정
python -m src tag "sample-doc.md" --dry-run --verbose
```

### 문제 해결

#### 태그가 부정확할 때
```bash
# 기존 태그 학습 비율 높이기
# config/settings.yaml에서 existing_tags.similarity_threshold 낮추기 (0.7 → 0.5)

# 더 많은 기존 태그를 학습에 활용
# config/settings.yaml에서 existing_tags.min_tag_frequency 낮추기 (2 → 1)
```

#### 태그가 너무 많을 때
```bash
# 카테고리별 태그 수 제한
# config/settings.yaml에서 categories.*.max_tags 조정

# 신뢰도 임계값 높이기
# config/settings.yaml에서 categories.*.min_confidence 높이기
```

#### 처리 속도가 느릴 때
```bash
# 배치 크기 증가
python -m src tag "folder/" --batch-size 100

# FP16 비활성화로 속도 향상 (정확도 약간 감소)
# config/settings.yaml에서 model.use_fp16: false
```

### 통계 및 분석

태깅 완료 후 생성되는 통계 정보:

```
🏷️ 태깅 완료 통계:
--------------------------------------------------
처리된 문서: 847개
성공: 823개 (97.2%)
실패: 24개 (2.8%)
평균 처리 시간: 1.2초/문서

📊 생성된 태그 분포:
- topic: 2,341개 (평균 2.8개/문서)
- type: 823개 (평균 1.0개/문서)  
- source: 756개 (평균 0.9개/문서)
- patterns: 445개 (평균 0.5개/문서)
- frameworks: 234개 (평균 0.3개/문서)

🎯 신뢰도 분포:
- 높음 (>0.7): 567개 문서 (68.9%)
- 중간 (0.4-0.7): 201개 문서 (24.4%)
- 낮음 (<0.4): 55개 문서 (6.7%)
```

## 🔄 인덱싱 관리

### 자동 인덱싱 (추천)
```bash
# 첫 검색 시 자동으로 인덱싱됩니다
python -m src search --query "첫 검색"
```

### 수동 재인덱싱
```bash
# 🆕 ColBERT 포함 통합 인덱싱 (권장!)
python -m src reindex --with-colbert

# ColBERT만 재인덱싱 (Dense 임베딩 제외)
python -m src reindex --colbert-only

# ColBERT 강제 재인덱싱
python -m src reindex --with-colbert --force

# 기본 재인덱싱 (Dense 임베딩만)
python -m src reindex

# 강제 전체 재인덱싱 (모든 캐시 무시)
python -m src reindex --force

# 샘플링 재인덱싱 (대규모 vault 성능 최적화)
python -m src reindex --sample-size 1000

# 폴더별 점진적 재인덱싱
python -m src reindex --include-folders "003-RESOURCES" "997-BOOKS"
python -m src reindex --exclude-folders "ATTACHMENTS" "temp"

# 상세 진행률 표시
python -m src reindex --force --verbose
```

### 폴더별 점진적 색인

### 🎯 ColBERT 증분 캐싱 시스템 (신규!)

#### 주요 장점
- **전체 문서 지원**: max_documents 제한 제거로 vault 전체에서 ColBERT 검색
- **영구 캐싱**: SQLite 기반으로 재계산 불필요 
- **증분 처리**: 변경된 문서만 자동 감지하여 재인덱싱
- **빠른 검색**: 캐시 활용으로 즉시 검색 결과 제공

#### 성능 비교
- **첫 인덱싱**: 1-2시간 (전체 vault, 1회만)
- **이후 검색**: 즉시 (캐시 활용)
- **증분 업데이트**: 변경된 파일만 처리

#### 캐시 상태 확인
```bash
python -m src info  # Dense + ColBERT 캐시 통계 포함
```

### 폴더별 점진적 색인

대규모 vault의 경우 특정 폴더만 선별적으로 인덱싱할 수 있습니다.

#### 특정 폴더만 포함
```bash
# 중요한 폴더들만 먼저 인덱싱
python -m src reindex --include-folders "003-RESOURCES" "000-SLIPBOX" "997-BOOKS"

# 개발 관련 문서만 인덱싱
python -m src reindex --include-folders "programming" "projects"
```

#### 특정 폴더 제외
```bash
# 임시 파일과 첨부 파일 제외
python -m src reindex --exclude-folders "ATTACHMENTS" "temp" "WIP"

# 아카이브 폴더 제외
python -m src reindex --exclude-folders "archive" "old"
```

#### 샘플링 기반 처리

매우 큰 vault의 경우 성능 최적화를 위해 샘플링을 사용할 수 있습니다.

```bash
# 1000개 문서만 샘플링하여 빠른 테스트
python -m src reindex --sample-size 1000

# 검색도 샘플링 모드로
python -m src search --query "TDD" --sample-size 500
```

**샘플링 모드 특징:**
- 전체 vault에서 균등하게 문서를 선택
- 폴더별 비율을 유지하여 편향 최소화
- 샘플링 메타데이터는 캐시에 저장되어 재사용
- 빠른 프로토타이핑과 시스템 테스트에 유용

### 언제 재인덱싱이 필요한가?

#### 자동으로 처리되는 경우:
- ✅ 새 파일 추가
- ✅ 기존 파일 수정
- ✅ 파일 삭제

#### 수동 재인덱싱이 필요한 경우:
- 🔧 설정 파일 변경
- 🐛 검색 품질 문제
- 💾 캐시 파일 손상
- 🔄 대량 파일 이동/이름 변경

## ⚙️ 설정 옵션

### config/settings.yaml 설정
```yaml
# 모델 설정
model:
  name: "BAAI/bge-m3"              # BGE-M3 임베딩 모델
  dimension: 1024                   # 임베딩 차원 (BGE-M3)
  batch_size: 12                    # 배치 크기
  max_length: 4096                  # 최대 토큰 길이
  use_fp16: true                    # FP16 정밀도 사용
  device: null                      # null: 자동선택, "cpu", "cuda", "mps"

# Phase 5: 고급 검색 품질 향상 설정
reranker:
  model_name: "BAAI/bge-reranker-v2-m3"  # Cross-encoder 재순위화 모델
  use_fp16: true
  batch_size: 4
  cache_folder: "models"

colbert:
  batch_size: 4
  max_length: 4096
  max_documents: 20                 # ColBERT 처리 문서 수 제한 (성능 최적화)

query_expansion:
  use_synonyms: true
  use_hyde: true
  hyde_templates: 3
  max_expanded_queries: 6

# Phase 6: 지식 그래프 및 관련성 분석 설정
knowledge_graph:
  similarity_threshold: 0.4      # 문서 간 연결 임계값
  min_word_count: 50            # 분석 대상 최소 단어 수
  centrality_weight: 0.2        # 중심성 점수 가중치
  max_connections_per_doc: 50   # 문서당 최대 연결 수
  enable_tag_nodes: true        # 태그 노드 포함 여부
  community_algorithm: "louvain" # 커뮤니티 감지 알고리즘

related_docs:
  similarity_threshold: 0.3     # 관련성 최소 임계값
  tag_similarity_weight: 0.3    # 태그 유사도 가중치
  semantic_similarity_weight: 0.5 # 의미적 유사도 가중치
  centrality_boost_weight: 0.2  # 중심성 가중치
  max_candidates: 100           # 최대 후보 문서 수

gap_analysis:
  min_connections: 3            # 고립 판정 최소 연결 수
  centrality_threshold: 0.1     # 중심성 최소 임계값
  isolation_threshold: 0.2      # 고립도 임계값

# 검색 설정
search:
  similarity_threshold: 0.3
  default_top_k: 10

# 중복 감지 설정
duplicates:
  similarity_threshold: 0.85    # 중복 판정 임계값
  min_word_count: 50           # 최소 단어 수
  group_threshold: 0.9         # 그룹핑 임계값

# Vault 설정
vault:
  excluded_dirs:               # 제외할 디렉토리
    - ".obsidian"
    - ".trash"
    - "ATTACHMENTS"
    - ".git"
    - "__pycache__"
    - ".DS_Store"
    - "cursor-img"
    - ".swarm"
  excluded_files:              # 제외할 파일 패턴 (glob 지원)
    - ".DS_Store"
    - "*.tmp"
    - "*.backup"
    - "**/temp/**/*"
    - "**/.obsidian/**/*"
  file_extensions:             # 처리할 파일 확장자
    - ".md"
    - ".markdown"

# 수집 설정
collection:
  min_documents: 3             # 최소 문서 수
  group_by_tags: true          # 태그별 그룹화
  include_statistics: true     # 통계 포함
  output_format: "markdown"    # 출력 형식
```

### 사용자 정의 설정으로 실행
```bash
python -m src search --config custom_config.yaml --query "TDD"
```

## 🛠️ 고급 사용법

### 1. 프로그래밍 방식 사용

#### 검색 엔진 직접 사용
```python
from src.features.advanced_search import AdvancedSearchEngine, SearchQuery
from datetime import datetime, timedelta

# 검색 엔진 초기화
engine = AdvancedSearchEngine(
    vault_path="/path/to/vault",
    cache_dir="cache",
    config={}
)

# 1. 기본 검색
results = engine.hybrid_search("TDD", top_k=10)

# 2. 고급 검색 (필터링)
query = SearchQuery(
    text="아키텍처 설계",
    min_word_count=100,
    max_word_count=2000,
    date_from=datetime.now() - timedelta(days=30),
    exclude_paths=["ATTACHMENTS/", "temp/"]
)
filtered_results = engine.advanced_search(query)

# 3. 검색 타입별 사용
semantic_results = engine.semantic_search("코드 품질", top_k=5)
keyword_results = engine.keyword_search("TDD 테스트", top_k=5)
hybrid_results = engine.hybrid_search(
    "클린 코드", 
    semantic_weight=0.8,  # 의미적 검색 80%
    keyword_weight=0.2    # 키워드 검색 20%
)
```

#### 중복 감지 직접 사용
```python
from src.features.duplicate_detector import DuplicateDetector

detector = DuplicateDetector(search_engine, config)
analysis = detector.find_duplicates()

print(f"중복 그룹: {analysis.get_group_count()}개")
print(f"중복 비율: {analysis.get_duplicate_ratio():.1%}")

# 중복 그룹별 처리
for group in analysis.duplicate_groups:
    print(f"그룹 {group.id}: {group.get_document_count()}개 문서")
    for doc in group.documents:
        print(f"  - {doc.path} ({doc.word_count}단어)")
```

#### 주제 수집 직접 사용
```python
from src.features.topic_collector import TopicCollector

collector = TopicCollector(search_engine, config)
collection = collector.collect_topic(
    topic="리팩토링",
    top_k=50,
    threshold=0.4,
    output_file="refactoring_docs.md"
)

print(f"수집된 문서: {collection.metadata.total_documents}개")
print(f"총 단어수: {collection.metadata.total_word_count:,}개")
```

#### MOC 생성 직접 사용 (Phase 8) 🆕
```python
from src.features.moc_generator import MOCGenerator

moc_generator = MOCGenerator(search_engine, config)
moc_data = moc_generator.generate_moc(
    topic="TDD",
    top_k=50,
    threshold=0.3,
    include_orphans=False,
    use_expansion=True,
    output_file="TDD-MOC.md"
)

print(f"MOC 생성 완료:")
print(f"- 총 문서: {moc_data.total_documents}개")
print(f"- 카테고리: {len(moc_data.categories)}개")
print(f"- 핵심 문서: {len(moc_data.core_documents)}개")
print(f"- 학습 단계: {len(moc_data.learning_path)}개")

# 카테고리별 분포 확인
for category in moc_data.categories:
    print(f"- {category.name}: {len(category.documents)}개")
```

#### 지식 그래프 직접 사용 (Phase 6)
```python
# 1. 관련 문서 추천
related_docs = search_engine.get_related_documents(
    document_path="클린 애자일(Back to Basics)",
    top_k=5,
    include_centrality_boost=True,
    similarity_threshold=0.3
)

print(f"관련 문서 {len(related_docs)}개 발견:")
for i, doc in enumerate(related_docs, 1):
    print(f"{i}. {doc.document.title} (관련도: {doc.similarity_score:.3f})")

# 2. 중심성 기반 검색
centrality_results = search_engine.search_with_centrality_boost(
    query="TDD",
    top_k=10,
    centrality_weight=0.2
)

print(f"중심성 반영 검색 결과 {len(centrality_results)}개:")
for result in centrality_results:
    print(f"- {result.document.title} (점수: {result.similarity_score:.3f})")

# 3. 지식 공백 분석
gaps = search_engine.analyze_knowledge_gaps(
    min_connections=3,
    centrality_threshold=0.1
)

print(f"고립 문서: {gaps['isolated_documents']}개")
print(f"고립 태그: {gaps['isolated_tags']}개")
print(f"전체 고립률: {gaps['isolation_ratio']:.1%}")
```

### 2. 배치 처리 스크립트

#### 여러 주제 일괄 수집
```python
#!/usr/bin/env python3
"""
여러 주제 일괄 수집 스크립트
"""
topics = ["TDD", "리팩토링", "클린코드", "아키텍처", "디자인패턴"]

for topic in topics:
    print(f"🔍 '{topic}' 주제 수집 중...")
    collection = collector.collect_topic(
        topic=topic,
        top_k=20,
        threshold=0.4,
        output_file=f"collections/{topic}_collection.md"
    )
    print(f"✅ {collection.metadata.total_documents}개 문서 수집 완료")
```

## 🔧 문제 해결

### 일반적인 문제들

#### 1. 검색 결과가 부정확할 때
```bash
# 임계값을 높여서 정확도 향상
python -m src search --query "TDD" --threshold 0.6

# 강제 재인덱싱으로 인덱스 새로고침
python -m src reindex --force
```

#### 2. 인덱싱이 느릴 때
```bash
# 진행률 확인 (verbose 모드)
python -m src reindex --verbose

# 설정에서 batch_size 조정
# config/settings.yaml에서 model.batch_size 값 변경
```

#### 3. 메모리 부족 에러
```yaml
# config/settings.yaml
model:
  batch_size: 8   # 기본값 12에서 8로 감소
  use_fp16: false # FP16 비활성화로 메모리 절약

reranker:
  batch_size: 2   # 재순위화 배치 크기 감소

colbert:
  batch_size: 2
  max_documents: 10  # ColBERT 처리 문서 수 감소
```

#### 4. 캐시 파일 손상
```bash
# 캐시 디렉토리 삭제 후 재인덱싱
rm -rf cache/
python -m src reindex --force
```

### 로그 확인 및 Verbose 모드

#### 모든 명령어에서 Verbose 옵션 사용
```bash
# 검색 시 상세 로그
python -m src search --query "TDD" --verbose

# 재인덱싱 시 진행률 상세 표시
python -m src reindex --force --verbose

# 중복 감지 시 상세 분석 과정
python -m src duplicates --verbose

# 관련 문서 찾기 시 계산 과정 표시
python -m src related --file "문서명" --verbose

# 지식 공백 분석 시 상세 통계
python -m src analyze-gaps --verbose
```

#### 로그 파일 저장
```bash
# 로그를 파일로 저장 (Linux/Mac)
python -m src reindex --verbose 2>&1 | tee reindex.log

# 검색 로그 저장
python -m src search --query "TDD" --rerank --expand --verbose > search.log 2>&1

# 시스템 테스트 로그 저장
python -m src test --verbose > test_results.log 2>&1
```

#### Verbose 모드에서 확인할 수 있는 정보
- **모델 로딩 시간**: BGE-M3, Reranker 모델 초기화 소요 시간
- **임베딩 생성 진행률**: 문서별 처리 상황 및 배치 단위 진행률
- **검색 단계별 시간**: 초기 검색 → 재순위화 → 결과 통합 시간
- **캐시 활용률**: 기존 캐시 사용 vs 새로 생성한 임베딩 비율
- **메모리 사용량**: 피크 메모리 사용량 및 모델별 메모리 점유율
- **지식 그래프 구축**: 노드/엣지 생성, 중심성 계산 진행률

## 📊 성능 최적화

### 권장 설정

#### 소규모 vault (< 1,000 문서)
```yaml
model:
  batch_size: 8
search:
  default_top_k: 10
reranker:
  batch_size: 4
colbert:
  max_documents: 20
```

#### 중규모 vault (1,000 ~ 5,000 문서)
```yaml
model:
  batch_size: 12
search:
  default_top_k: 20
reranker:
  batch_size: 4
colbert:
  max_documents: 20
```

#### 대규모 vault (> 5,000 문서)
```yaml
model:
  batch_size: 16
search:
  default_top_k: 50
duplicates:
  min_word_count: 100  # 짧은 문서 제외로 성능 향상
reranker:
  batch_size: 6
colbert:
  max_documents: 30
```

### Phase 5 성능 가이드

#### 검색 방법별 성능 비교
| 검색 방법 | 속도 | 정확도 | 메모리 사용 | 권장 사용처 |
|-----------|------|--------|-------------|-------------|
| `hybrid` | ⚡⚡⚡ | ⭐⭐⭐ | 💾 | 일반적 검색 |
| `--rerank` | ⚡⚡ | ⭐⭐⭐⭐⭐ | 💾💾 | 고정확도 필요 |
| `--expand` | ⚡ | ⭐⭐⭐⭐ | 💾💾 | 포괄적 검색 |
| `colbert` | ⚡ | ⭐⭐⭐⭐ | 💾💾💾 | 토큰 수준 매칭 |
| `--rerank --expand` | ⚡ | ⭐⭐⭐⭐⭐ | 💾💾💾 | 최고 품질 |

### Phase 6 성능 가이드

#### 지식 그래프 기능별 성능 특성

| 기능 | 속도 | 메모리 사용 | 정확도 | 권장 사용처 |
|------|------|-------------|--------|-------------|
| `related` | ⚡⚡ | 💾💾 | ⭐⭐⭐⭐⭐ | 관련 문서 탐색 |
| `--with-centrality` | ⚡⚡ | 💾💾 | ⭐⭐⭐⭐ | 중요도 기반 검색 |
| `analyze-gaps` | ⚡ | 💾💾💾 | ⭐⭐⭐⭐⭐ | vault 구조 분석 |

#### Phase 6 기능 성능 최적화 팁

**관련 문서 추천 (`related`)**
```bash
# 빠른 추천 (기본 설정)
python -m src related --file "문서명" --top-k 5

# 정확한 추천 (높은 임계값)
python -m src related --file "문서명" --similarity-threshold 0.5 --top-k 10

# 포괄적 추천 (낮은 임계값)
python -m src related --file "문서명" --similarity-threshold 0.2 --top-k 20
```

**지식 공백 분석 (`analyze-gaps`)**
```bash
# 빠른 분석 (기본 설정)
python -m src analyze-gaps

# 정밀 분석 (더 엄격한 기준)
python -m src analyze-gaps --min-connections 5 --similarity-threshold 0.4

# 관대한 분석 (더 많은 연결 허용)
python -m src analyze-gaps --min-connections 1 --similarity-threshold 0.2
```

**중심성 기반 검색**
- 지식 그래프 구축: 처음 1회만 수행 (약 30초-2분)
- 이후 검색: 일반 검색과 동일한 속도
- 중심성 가중치 조정으로 성능/품질 균형 조절

#### 성능 최적화 팁
```bash
# 빠른 탐색용
python -m src search --query "TDD"

# 정확도 우선
python -m src search --query "TDD" --rerank

# 포괄성 우선  
python -m src search --query "TDD" --expand --no-hyde

# 최고 품질 (시간 소요)
python -m src search --query "TDD" --rerank --expand
```

### 🖥️ 시스템 정보 및 모니터링

#### 시스템 정보 확인
```bash
# 시스템 전체 정보 확인
python -m src info
```

#### 시스템 정보 결과 해석
```
ℹ️ Vault Intelligence System V2
==================================================
프로젝트 경로: /Users/msbaek/git/vault-intelligence
Python 버전: 3.11.7 (main, Dec  4 2023, 18:10:11) [Clang 15.0.0 (clang-1500.1.0.2.5)]
PyTorch 장치: MPS                    # M1/M2 Mac의 Metal Performance Shaders
GPU 메모리: 24.0GB                   # 통합 메모리

📋 완료된 기능 (Phase 6):
- BGE-M3 기반 1024차원 임베딩
- 다층 하이브리드 검색 (Dense + Sparse + ColBERT + Reranking)
- 지식 그래프 분석 (관련성, 중심성, 공백 분석)
- 쿼리 확장 (동의어 + HyDE)
- SQLite 기반 영구 캐싱

📚 문서:
- 사용자 가이드: docs/USER_GUIDE.md
- 실전 예제: docs/EXAMPLES.md

⚡ 빠른 시작:
  python -m src search --query 'TDD'
  python -m src related --file '클린 애자일'
  python -m src analyze-gaps
```

### 성능 모니터링
```bash
# 시스템 통계 확인
python -m src info

# 검색 성능 테스트
time python -m src search --query "performance test"

# 개별 모듈 테스트
python -c "from src.features.reranker import test_reranker; test_reranker()"
python -c "from src.features.colbert_search import test_colbert_search; test_colbert_search()"
python -c "from src.features.query_expansion import test_query_expansion; test_query_expansion()"
```

## 🎯 실제 사용 사례

### 1. 책 집필 지원
```bash
# 1. 주제별 자료 수집
python -m src collect --topic "TDD" --output book/chapter1_tdd.md
python -m src collect --topic "리팩토링" --output book/chapter2_refactor.md

# 2. 중복 내용 확인
python -m src duplicates

# 3. 누락된 주제 발견
python -m src analyze
```

### 2. 지식 정리 및 체계화
```bash
# 1. 전체 주제 분석으로 구조 파악
python -m src analyze

# 2. 지식 공백 분석으로 개선점 발견 (Phase 6)
python -m src analyze-gaps --top-k 20

# 3. 주제별 상세 수집
python -m src collect --topic "아키텍처" --threshold 0.5

# 4. 중복 파일 정리
python -m src duplicates

# 5. 핵심 문서 중심성 분석 (Phase 6)
python -m src search --query "중요한 개념" --with-centrality --top-k 15
```

### 3. 연구 자료 관리
```bash
# 1. 키워드별 관련 자료 검색
python -m src search --query "마이크로서비스" --top-k 20

# 2. 특정 문서 기반 관련 자료 발굴 (Phase 6)
python -m src related --file "마이크로서비스 아키텍처 패턴" --top-k 15

# 3. 시계열 분석을 위한 날짜 필터링 (프로그래밍 방식)
# SearchQuery로 date_from, date_to 설정

# 4. 주제별 자료집 생성
python -m src collect --topic "클라우드 아키텍처" --output research/cloud.md

# 5. 연구 공백 분석으로 누락 영역 발견 (Phase 6)
python -m src analyze-gaps --top-k 10
```

## 📝 팁과 요령

### 효과적인 검색 쿼리 작성

#### ✅ 좋은 예시
```bash
# 구체적인 개념
python -m src search --query "테스트 주도 개발"

# 영어/한글 혼용
python -m src search --query "SOLID principles"

# 복합 개념
python -m src search --query "마이크로서비스 아키텍처 패턴"
```

#### ❌ 피해야 할 예시
```bash
# 너무 짧은 쿼리
python -m src search --query "TDD"  # 대신 "TDD 방법론" 권장

# 너무 일반적인 단어
python -m src search --query "개발"  # 대신 "소프트웨어 개발" 권장
```

### 임계값 조정 가이드

| 임계값 | 결과 특성 | 사용 상황 |
|--------|-----------|-----------|
| 0.1 ~ 0.3 | 많은 결과, 낮은 정확도 | 탐색적 검색 |
| 0.3 ~ 0.5 | 균형잡힌 결과 | 일반적 사용 |
| 0.5 ~ 0.7 | 적은 결과, 높은 정확도 | 정확한 정보 필요 |
| 0.7 ~ 1.0 | 매우 적은 결과, 매우 높은 정확도 | 특정 문서 찾기 |

### 주제 수집 최적화

#### 주제별 권장 임계값
- **일반적 주제** (TDD, 리팩토링): 0.3~0.4
- **전문적 주제** (DDD, 마이크로서비스): 0.4~0.6  
- **매우 구체적 주제** (특정 디자인패턴): 0.6~0.8

#### 수집 문서 수 가이드
- **개요 파악**: top-k=10~20
- **상세 분석**: top-k=30~50
- **완전한 수집**: top-k=100+

---

## 📞 지원 및 문의

- **GitHub Issues**: 버그 리포트 및 기능 요청
- **문서 업데이트**: 사용 중 발견한 개선사항 공유
- **성능 이슈**: 로그 파일과 함께 문의

---

**최종 업데이트**: 2025-08-21  
**버전**: V2.7 (Phase 7 완료 - 자동 태깅 시스템)

### 주요 업데이트 (V2.7)
- 🏷️ **Semantic Tagging**: BGE-M3 기반 지능형 자동 태깅 시스템
- 🧠 **Tag Learning**: 기존 vault 태그 패턴 학습 및 일관성 유지
- 📁 **Batch Processing**: 폴더별 대용량 문서 일괄 태깅 지원
- 🎯 **Rule-based Categorization**: 5대 카테고리 체계적 태그 분류
- ⚙️ **CLI Integration**: `tag` 서브커맨드 및 다양한 옵션 지원

### 이전 업데이트 (V2.6)
- 🕸️ **Knowledge Graph**: NetworkX 기반 문서 관계 분석 및 중심성 점수 계산
- 🔗 **Related Documents**: 의미적 + 태그 + 중심성 기반 관련 문서 추천
- 📊 **Centrality Ranking**: PageRank 등 중심성 점수를 활용한 검색 랭킹 향상
- 🔍 **Knowledge Gap Analysis**: 고립된 문서 및 지식 공백 분석
- ⚙️ **CLI Extensions**: `related`, `analyze-gaps`, `--with-centrality` 명령어 추가

### 이전 업데이트 (V2.5)
- 🎯 **Cross-encoder Reranking**: BGE Reranker V2-M3 기반 정밀 재순위화
- 🔍 **ColBERT Search**: 토큰 수준 late interaction 검색
- 🔄 **Query Expansion**: 한영 동의어 확장 + HyDE 가상 문서 생성
- ⚙️ **File Exclusion**: glob 패턴 기반 파일 제외 기능
- 📊 **Performance Optimization**: 다양한 검색 모드별 성능 최적화