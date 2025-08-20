# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 프로젝트 개요

Vault Intelligence System V2는 BGE-M3 기반 Obsidian vault 지능형 검색 시스템입니다. Smart Connections 플러그인에서 완전히 독립하여 더 높은 차원의 임베딩(1024차원)과 하이브리드 검색(Dense + Sparse) 기능을 제공합니다.

## 개발 환경 설정

### 의존성 설치
```bash
pip install -r requirements.txt
```

### 시스템 테스트
```bash
python -m src test
```

### 시스템 초기화
```bash
python -m src init --vault-path /Users/msbaek/DocumentsLocal/msbaek_vault
```

## 주요 명령어

### 검색 기능
```bash
# 하이브리드 검색 (의미적 + 키워드)
python -m src search --query "TDD" --top-k 10

# 유사도 임계값 조정
python -m src search --query "리팩토링" --threshold 0.3
```

### 중복 문서 감지
```bash
python -m src duplicates
```

### 주제별 문서 수집
```bash
# 주제별 문서 수집
python -m src collect --topic "TDD" --output results.md

# 상위 K개 결과만 수집
python -m src collect --topic "클린코드" --top-k 20
```

### 주제 분석 및 클러스터링
```bash
python -m src analyze
```

### 전체 재인덱싱
```bash
# 일반 재인덱싱
python -m src reindex

# 강제 재인덱싱 (기존 캐시 무시)
python -m src reindex --force
```

### 시스템 정보
```bash
python -m src info
```

## 아키텍처 구조

### 핵심 모듈 구조
```
src/
├── core/                           # 핵심 엔진
│   ├── sentence_transformer_engine.py  # BGE-M3 기반 고품질 임베딩 엔진
│   ├── embedding_cache.py              # SQLite 기반 임베딩 캐싱
│   └── vault_processor.py              # Obsidian 마크다운 파일 처리
├── features/                       # 기능 모듈
│   ├── advanced_search.py              # 의미적/키워드/하이브리드 검색
│   ├── duplicate_detector.py           # 중복 문서 감지
│   ├── topic_collector.py              # 주제별 문서 수집
│   ├── topic_analyzer.py               # 주제 분석 및 클러스터링
│   └── knowledge_graph.py              # 지식 그래프 (계획)
└── __main__.py                     # CLI 엔트리 포인트
```

### 데이터 계층
- **SQLite 캐시**: `cache/embeddings.db` - 임베딩 벡터 영구 저장
- **메타데이터**: `cache/metadata.json` - 문서 메타데이터 캐싱
- **설정**: `config/settings.yaml` - 시스템 전역 설정
- **모델**: `models/` - 다운로드된 BGE-M3 모델

## 프로그래밍 방식 사용

### 검색 엔진 초기화
```python
from src.features.advanced_search import AdvancedSearchEngine

# 검색 엔진 초기화
engine = AdvancedSearchEngine(
    vault_path="/path/to/vault",
    cache_dir="cache",
    config=config
)

# 인덱스 구축 (처음 실행 시)
engine.build_index()
```

### 하이브리드 검색
```python
# 하이브리드 검색 (의미적 + 키워드)
results = engine.hybrid_search("TDD", top_k=10)

# 의미적 검색만
results = engine.semantic_search("테스트 주도 개발", top_k=5)

# 키워드 검색만  
results = engine.keyword_search("refactoring", top_k=10)
```

### 중복 문서 감지
```python
from src.features.duplicate_detector import DuplicateDetector

detector = DuplicateDetector(engine, config)
analysis = detector.find_duplicates()

print(f"중복 그룹: {analysis.get_group_count()}개")
print(f"중복 비율: {analysis.get_duplicate_ratio():.1%}")
```

### 주제별 문서 수집
```python
from src.features.topic_collector import TopicCollector

collector = TopicCollector(engine, config)
collection = collector.collect_topic("TDD", top_k=20)

# 결과를 마크다운으로 저장
collector.save_collection(collection, "tdd_collection.md")
```

## 설정 관리

### 주요 설정 (`config/settings.yaml`)

**모델 설정**
- `model.name`: BGE 모델명 (기본: BAAI/bge-m3)
- `model.dimension`: 임베딩 차원 (1024)
- `model.batch_size`: 배치 크기 (12)
- `model.use_fp16`: FP16 정밀도 사용 여부 (true)

**검색 설정**
- `search.similarity_threshold`: 유사도 임계값 (0.3)
- `search.text_weight`: 키워드 검색 가중치 (0.3)
- `search.semantic_weight`: 의미적 검색 가중치 (0.7)

**중복 감지 설정**
- `duplicates.similarity_threshold`: 중복 판정 임계값 (0.85)
- `duplicates.min_word_count`: 최소 단어 수 (50)

## 테스트

### 단위 테스트 실행
```bash
python -m src test
```

개별 모듈 테스트 함수:
- `src.core.sentence_transformer_engine.test_engine()`
- `src.core.embedding_cache.test_cache()`
- `src.core.vault_processor.test_processor()`

## 성능 최적화

### 캐싱 시스템
- SQLite 기반 영구 캐싱으로 재처리 방지
- 문서 내용 해시 기반 캐시 무효화
- 배치 처리로 대량 임베딩 최적화

### 메모리 관리
- BGE-M3 모델 캐싱 및 재사용
- 대용량 vault 처리를 위한 배치 단위 처리
- 진행률 표시로 사용자 경험 개선
- GPU/CPU 자동 감지 및 최적화

## 프로젝트 관리 방식

### 문서화 전략
- **계획 문서**: `docs/embedding-upgrade-plan.md`에 전체 구현 계획 관리
- **TODO 추적**: `docs/todo-embedding-upgrade.md`에 체크리스트 형식으로 진행 상황 관리
- **커밋 전략**: 각 기능 완성 시점에 의미 있는 커밋 메시지와 함께 커밋
- **태깅**: 주요 마일스톤 달성 시 Git 태그로 버전 관리

### 개발 워크플로우
1. TODO 문서에서 다음 작업 항목 선택
2. 해당 항목을 '진행 중'으로 표시
3. 기능 구현 완료 후 '완료'로 표시
4. 관련 문서 업데이트 (README, CLAUDE.md)
5. 적절한 커밋 메시지와 함께 변경사항 커밋

### 품질 관리
- 각 단계별 테스트 실행 필수
- 성능 벤치마크 측정 및 기록
- 코드 리뷰 및 리팩토링 지속 수행
- 문서화 동기화 유지

## 현재 구현 상태

### ✅ 완료된 작업 (Phase 1-3)
- BGE-M3 기반 고품질 임베딩 시스템 구현 완료
- Dense Embeddings (1024차원) 의미적 검색
- Sparse Embeddings (BM25) 키워드 검색  
- Hybrid Search (RRF 기반 Dense + Sparse 융합)
- 고급 검색 엔진 (의미적/키워드/하이브리드)
- 중복 문서 감지 및 그룹화
- 주제별 클러스터링 (K-means, DBSCAN)
- 문서 수집 및 통합 시스템
- 통합 CLI 인터페이스
- 전체 시스템 통합 테스트 완료

### 🎯 향후 개선 사항 (Phase 4)
- Cross-encoder 기반 Reranking 시스템
- Obsidian 특화 기능 (링크 그래프, 메타데이터 활용)
- ColBERT 임베딩 활용
- GPU 가속 최적화

## 문제 해결

### 일반적인 문제들

**임베딩 생성 실패**
- 의존성 확인: `python -m src test`
- 캐시 초기화: `rm -rf cache/` 후 재실행

**검색 결과 없음**
- 인덱스 재구축: `python -m src reindex --force`
- 유사도 임계값 조정: `--threshold 0.1`

**메모리 부족**
- 배치 크기 감소: `config/settings.yaml`에서 `model.batch_size` 조정 (기본: 12)
- FP16 비활성화: `model.use_fp16: false`로 설정

### 로그 및 디버깅
- 상세 로그: `--verbose` 플래그 사용
- 로그 레벨 조정: `config/settings.yaml`의 `logging.level` 설정

## 데이터 구조

### Document 클래스
- `path`: 문서 경로
- `title`: 문서 제목
- `content`: 문서 내용
- `tags`: 추출된 태그
- `word_count`: 단어 수
- `created_date`, `modified_date`: 생성/수정일

### SearchResult 클래스
- `document`: Document 객체
- `similarity_score`: 유사도 점수
- `match_type`: 매치 타입 (semantic/keyword/hybrid)
- `matched_keywords`: 매칭된 키워드
- `snippet`: 문서 발췌

이 시스템은 BGE-M3 모델을 활용하여 대규모 Obsidian vault에서 효율적인 하이브리드 검색과 문서 분석을 제공하며, 특히 "AI 시대의 TDD 활용" 책 저술을 위한 고품질 지능형 검색 지원을 목표로 합니다.

## 기술 스택

### 핵심 기술
- **임베딩 모델**: BAAI/bge-m3 (1024차원, 다국어 지원)
- **하이브리드 검색**: Dense + Sparse (BM25) + RRF 융합
- **캐싱**: SQLite 기반 영구 임베딩 캐시
- **언어**: Python 3.11+, PyTorch 기반

### 주요 라이브러리
- **FlagEmbedding**: BGE-M3 모델 구동
- **rank-bm25**: 키워드 기반 sparse retrieval
- **networkx**: 그래프 분석 (향후 확장)
- **scikit-learn**: 클러스터링 및 유사도 계산