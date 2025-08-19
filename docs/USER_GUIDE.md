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

### 3. 첫 검색 (자동 인덱싱)
```bash
python -m src search --query "TDD"
```

## 🔍 검색 기능

### 기본 검색
```bash
# 기본 하이브리드 검색 (추천)
python -m src search --query "테스트 주도 개발"

# 상위 5개 결과만
python -m src search --query "리팩토링" --top-k 5

# 높은 정확도 (임계값 상향)
python -m src search --query "클린 코드" --threshold 0.5
```

### 고급 검색 옵션
```bash
# 다양한 옵션 조합
python -m src search \
  --query "SOLID principles" \
  --top-k 10 \
  --threshold 0.3 \
  --verbose
```

### 검색 결과 해석
```
📄 검색 결과 (3개):
--------------------------------------------------------------------------------
1. Clean Architecture 책 정리        # 1위 결과
   경로: 997-BOOKS/clean-architecture.md
   유사도: 0.8542                     # 높을수록 관련성 높음 (0~1)
   타입: hybrid                       # 검색 방식
   키워드: solid, principles          # 매칭된 키워드
   내용: SOLID 원칙은 객체지향...      # 미리보기 스니펫
```

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

## 🔄 인덱싱 관리

### 자동 인덱싱 (추천)
```bash
# 첫 검색 시 자동으로 인덱싱됩니다
python -m src search --query "첫 검색"
```

### 수동 재인덱싱
```bash
# 스마트 재인덱싱 (변경된 파일만)
python -m src reindex

# 강제 전체 재인덱싱 (모든 캐시 무시)
python -m src reindex --force
```

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
  name: "paraphrase-multilingual-mpnet-base-v2"
  dimension: 5000
  batch_size: 32
  device: null  # null: 자동선택, "cpu", "cuda"

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
  batch_size: 16  # 기본값 32에서 16으로 감소
```

#### 4. 캐시 파일 손상
```bash
# 캐시 디렉토리 삭제 후 재인덱싱
rm -rf cache/
python -m src reindex --force
```

### 로그 확인
```bash
# 상세 로그로 실행
python -m src search --query "TDD" --verbose

# 로그 파일로 저장
python -m src reindex --verbose 2>&1 | tee reindex.log
```

## 📊 성능 최적화

### 권장 설정

#### 소규모 vault (< 1,000 문서)
```yaml
model:
  batch_size: 16
search:
  default_top_k: 10
```

#### 중규모 vault (1,000 ~ 5,000 문서)
```yaml
model:
  batch_size: 32
search:
  default_top_k: 20
```

#### 대규모 vault (> 5,000 문서)
```yaml
model:
  batch_size: 64
search:
  default_top_k: 50
duplicates:
  min_word_count: 100  # 짧은 문서 제외로 성능 향상
```

### 성능 모니터링
```bash
# 시스템 통계 확인
python -m src info

# 검색 성능 테스트
time python -m src search --query "performance test"
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

# 2. 주제별 상세 수집
python -m src collect --topic "아키텍처" --threshold 0.5

# 3. 중복 파일 정리
python -m src duplicates
```

### 3. 연구 자료 관리
```bash
# 1. 키워드별 관련 자료 검색
python -m src search --query "마이크로서비스" --top-k 20

# 2. 시계열 분석을 위한 날짜 필터링 (프로그래밍 방식)
# SearchQuery로 date_from, date_to 설정

# 3. 주제별 자료집 생성
python -m src collect --topic "클라우드 아키텍처" --output research/cloud.md
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

**최종 업데이트**: 2025-08-19  
**버전**: V2.1 (Phase 2 완료)