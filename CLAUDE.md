# Developer Guide - Vault Intelligence System V2

이 문서는 Claude Code에서 이 레포지토리 작업 시 참조하는 개발자 가이드입니다.

## 📖 문서 구조

- **[README.md](README.md)** - 프로젝트 개요 및 빠른 시작
- **[사용자 가이드](docs/USER_GUIDE.md)** - 완전한 사용법 매뉴얼  
- **[실전 예제](docs/EXAMPLES.md)** - 다양한 활용 사례
- **[문제 해결](docs/TROUBLESHOOTING.md)** - 기술 지원 가이드
- **이 문서** - 개발자 및 기여자를 위한 상세 가이드

## 🏗️ 시스템 아키텍처

### 핵심 모듈 구조
```
src/
├── core/                           # 핵심 엔진
│   ├── sentence_transformer_engine.py  # BGE-M3 임베딩 엔진
│   ├── embedding_cache.py              # SQLite 캐싱 시스템
│   └── vault_processor.py              # Vault 파일 처리
├── features/                       # 기능 모듈
│   ├── advanced_search.py              # 다층 검색 엔진
│   ├── reranker.py                     # Cross-encoder 재순위화
│   ├── colbert_search.py               # ColBERT 토큰 검색
│   ├── query_expansion.py              # 쿼리 확장 (동의어 + HyDE)
│   ├── semantic_tagger.py              # 자동 태깅 시스템
│   ├── content_clusterer.py            # 문서 클러스터링 (Phase 9)
│   ├── document_summarizer.py          # 문서 요약 시스템 (Phase 9)  
│   ├── learning_reviewer.py            # 학습 리뷰 시스템 (Phase 9)
│   ├── knowledge_graph.py              # 지식 그래프 분석
│   ├── moc_generator.py                # MOC 자동 생성
│   ├── topic_collector.py              # 주제별 문서 수집
│   └── duplicate_detector.py           # 중복 문서 감지
├── utils/                          # 유틸리티
│   └── claude_code_integration.py      # Claude Code LLM 통합
└── __main__.py                     # CLI 엔트리 포인트
```

### 데이터 계층
- **SQLite 캐시**: `cache/embeddings.db` - 임베딩 벡터 영구 저장
- **메타데이터**: `cache/metadata.json` - 문서 메타데이터 캐싱  
- **설정**: `config/settings.yaml` - 시스템 전역 설정
- **모델**: `models/` - 다운로드된 BGE-M3 모델

## 🚀 개발 환경 설정

### 1. 개발 의존성 설치
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt  # 개발용 추가 도구들
```

### 2. 개발용 설정
```bash
# 테스트 vault 설정 (개발용)
python -m src init --vault-path ./test-vault

# 시스템 상태 확인
python -m src info

# 전체 시스템 테스트
python -m src test
```

### 3. 개발 워크플로우
```bash
# 새 기능 개발 시
1. 기능별 브랜치 생성: git checkout -b feature/new-feature
2. 단위 테스트 작성: tests/test_new_feature.py
3. 기능 구현: src/features/new_feature.py  
4. CLI 통합: src/__main__.py에 명령어 추가
5. 문서 업데이트: 이 파일 및 사용자 가이드 업데이트
```

## 🧪 테스트 및 검증

### 단위 테스트
```bash
# 전체 시스템 테스트
python -m src test

# 개별 모듈 테스트
python -c "from src.core.sentence_transformer_engine import test_engine; test_engine()"
python -c "from src.features.advanced_search import test_search_engine; test_search_engine()"
```

### 성능 벤치마크
```bash
# 검색 성능 테스트 (1000개 문서 기준)
python -m src search --query "test" --benchmark

# 인덱싱 성능 테스트
time python -m src reindex --force

# 메모리 사용량 모니터링
python -c "
import psutil, os
process = psutil.Process(os.getpid())
print(f'Memory: {process.memory_info().rss / 1024 / 1024:.1f}MB')
"
```

## ⚙️ 설정 시스템

### config/settings.yaml 구조
```yaml
# 모델 설정
model:
  name: "BAAI/bge-m3"
  dimension: 1024
  batch_size: 8          # 안정적 설정
  max_length: 4096       # 토큰 길이 제한
  use_fp16: false        # M1 호환성
  num_workers: 6         # 병렬 처리 워커 수

# 검색 설정  
search:
  similarity_threshold: 0.3
  text_weight: 0.3       # BM25 가중치
  semantic_weight: 0.7   # Dense 가중치

# 캐싱 설정
caching:
  enable_dense: true
  enable_colbert: true
  enable_metadata: true

# Phase 9 설정
clustering:
  default_algorithm: "kmeans"
  max_clusters: 10
  silhouette_threshold: 0.3

document_summarization:
  default_style: "detailed" 
  max_cluster_size: 100

learning_review:
  default_period: "weekly"
  min_activity_threshold: 1
```

### 성능 튜닝 가이드

**안정적 설정 (기본값)**:
- batch_size: 4-8
- max_length: 4096  
- num_workers: 6
- 소요시간: 40-60분 (1000개 문서)

**고성능 설정**:
- batch_size: 8-12
- max_length: 8192
- num_workers: 8
- 소요시간: 25-35분 (50-70% 향상)
- ⚠️ 메모리 사용량 증가

## 🔧 주요 API

### 1. 검색 엔진 (AdvancedSearchEngine)
```python
from src.features.advanced_search import AdvancedSearchEngine

# 초기화
engine = AdvancedSearchEngine(
    vault_path="/path/to/vault",
    cache_dir="cache", 
    config=config
)

# 인덱스 구축
engine.build_index()

# 다양한 검색 방법
results = engine.hybrid_search("query", top_k=10)
results = engine.semantic_search("query", top_k=5)  
results = engine.colbert_search("query", top_k=10)

# 재순위화 적용
from src.features.reranker import Reranker
reranker = Reranker(config)
reranked = reranker.rerank(results, "query")
```

### 2. 문서 클러스터링 (Phase 9)
```python
from src.features.content_clusterer import ContentClusterer

clusterer = ContentClusterer(engine.engine, engine.cache, config)
result = clusterer.cluster_documents(
    documents=documents,
    algorithm='kmeans',    # kmeans, dbscan, agglomerative
    n_clusters=5
)

# 결과 분석
print(f"실루엣 점수: {result.silhouette_score}")
for i, cluster in enumerate(result.clusters):
    print(f"클러스터 {i}: {len(cluster.documents)}개 문서")
    print(f"키워드: {cluster.keywords}")
```

### 3. 문서 요약 (Phase 9)
```python  
from src.features.document_summarizer import DocumentSummarizer

summarizer = DocumentSummarizer(engine.cache, config)
summary = summarizer.summarize_clustering_result(
    clustering_result,
    style='detailed',     # brief, detailed, technical, conceptual
    topic='TDD'
)

# Claude Code LLM 통합 (목 구현)
from src.utils.claude_code_integration import ClaudeCodeLLM
llm = ClaudeCodeLLM(config)
response = llm.summarize_documents(content, cluster_info, style='detailed')
```

### 4. 학습 리뷰 (Phase 9)
```python
from src.features.learning_reviewer import LearningReviewer

reviewer = LearningReviewer(engine, config) 
review = reviewer.generate_review(
    period='weekly',      # weekly, monthly, quarterly
    topic=None,           # 특정 주제 필터링
    start_date=None,      # 커스텀 기간
    end_date=None
)

# 인사이트 분석
insights = review.insights
for insight in insights:
    print(f"{insight.type}: {insight.content}")
```

## 🎯 확장 가이드

### 새로운 검색 방법 추가
1. `src/features/`에 새 모듈 생성
2. `AdvancedSearchEngine`에 메서드 추가
3. `__main__.py`에 CLI 옵션 추가
4. 테스트 함수 구현

### 새로운 클러스터링 알고리즘 추가
```python
# src/features/content_clusterer.py에 추가
def _cluster_custom_algorithm(self, embeddings, **kwargs):
    """커스텀 클러스터링 알고리즘"""
    # 알고리즘 구현
    labels = your_clustering_algorithm(embeddings, **kwargs)
    return labels
```

### 새로운 요약 스타일 추가
```python  
# src/features/document_summarizer.py에 추가
def _get_style_prompt(self, style: str) -> str:
    """요약 스타일별 프롬프트"""
    style_prompts = {
        "custom": "커스텀 요약 스타일 프롬프트...",
        # 기존 스타일들...
    }
    return style_prompts.get(style, style_prompts["detailed"])
```

## 🐛 디버깅 및 로깅

### 로깅 설정
```python
import logging
logging.basicConfig(level=logging.DEBUG)

# 모듈별 로깅
logger = logging.getLogger(__name__)
logger.debug("디버그 메시지")
logger.info("정보 메시지") 
logger.warning("경고 메시지")
logger.error("오류 메시지")
```

### 일반적인 문제 해결
- **메모리 부족**: batch_size 감소, FP16 비활성화
- **검색 결과 없음**: similarity_threshold 조정 (기본: 0.3)  
- **인덱싱 실패**: 캐시 디렉토리 권한 확인, 강제 재인덱싱
- **모델 로딩 실패**: 네트워크 연결 확인, HuggingFace 캐시 확인

### 성능 프로파일링
```python
import cProfile
import pstats

# 함수 성능 측정
profiler = cProfile.Profile() 
profiler.enable()
# 코드 실행
profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(10)
```

## 🔄 최신 개발 현황

### ✅ 완료된 Phase들 (Phase 1-9)
- **Phase 1-4**: 기본 BGE-M3 검색 시스템
- **Phase 5**: 고급 검색 (Reranking, ColBERT, 쿼리 확장)
- **Phase 6**: 지식 그래프 및 관련성 분석  
- **Phase 7**: 자동 태깅 시스템
- **Phase 8**: MOC 자동 생성
- **Phase 9**: 다중 문서 요약 시스템 ✨

### 🎯 향후 개발 방향 (Phase 10+)
- 웹 인터페이스 (FastAPI + React)
- 실시간 모니터링 대시보드
- 플러그인 시스템 아키텍처
- 다중 언어 지원 확장

## 📊 코드 품질

### 코딩 스타일
- PEP 8 준수
- Type hints 적극 활용
- Docstring 필수 (Google style)
- 함수는 단일 책임 원칙 준수

### 코드 리뷰 체크리스트
- [ ] 단위 테스트 작성
- [ ] 타입 힌트 추가
- [ ] 문서화 (docstring + 주석)
- [ ] 에러 처리 구현
- [ ] 성능 고려 (메모리, 속도)
- [ ] 설정 가능성 (하드코딩 방지)

## 🤝 기여 가이드

1. **이슈 먼저**: 새 기능 개발 전 Issue 생성
2. **브랜치 전략**: `feature/feature-name` 브랜치 사용
3. **커밋 메시지**: Conventional Commits 형식 준수
4. **테스트**: 새 코드는 반드시 테스트 포함
5. **문서화**: README, 이 문서, 사용자 가이드 업데이트

자세한 내용은 [CONTRIBUTING.md](CONTRIBUTING.md)를 참조하세요.