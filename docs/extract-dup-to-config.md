# 하드 코딩된 값들을 설정으로 분리하는 작업 계획

## 1. 분석된 하드 코딩 문제점들

### 🔢 숫자 값 하드 코딩 문제
- **임계값들**: 0.1, 0.2, 0.3, 0.7, 0.85, 0.9 등의 유사도/가중치 값들
- **텍스트 길이**: 150자, 200자, 2048자, 500자 등의 다양한 텍스트 길이 제한
- **배치/청크 크기**: 20, 50, 100 등의 처리 단위
- **표시 제한**: 20개, 50개 등의 결과 표시 개수
- **파일 크기**: 1024, 1024*1024 등의 바이트/MB 변환
- **메모리/성능**: 2000 단어, 800 크기 등의 제한값들
- **시각화**: 노드 크기 200-800, 투명도 0.3, 반복 50회 등

### 📁 파일 경로 하드 코딩 문제
- **사용자별 고정 경로**: `/Users/msbaek/DocumentsLocal/msbaek_vault` - CLI 기본값으로 하드 코딩
- **규칙 파일 경로**: `~/dotfiles/.claude/commands/obsidian/add-tag.md` - 태깅 규칙 파일 고정
- **설정 파일 경로**: `config/settings.yaml` - 상대 경로로 고정
- **캐시 디렉토리**: `models/` - 모델 캐시 폴더 하드 코딩
- **파일 확장자**: `.md`, `.json`, `.db`, `.yaml` 등이 여러 곳에 반복

### 📁 영향받는 주요 파일들
- `src/__main__.py`: CLI 인터페이스의 다양한 임계값들 및 기본 vault 경로
- `src/features/advanced_search.py`: 검색 관련 하드 코딩 값들
- `src/features/semantic_tagger.py`: 태깅 관련 설정값들 및 모델 경로
- `src/features/knowledge_graph.py`: 그래프 시각화 관련 값들
- `src/features/colbert_search.py`: ColBERT 검색 설정들
- `src/features/tag_rule_engine.py`: 규칙 파일 경로 하드 코딩
- `src/core/sentence_transformer_engine.py`: 청크 크기, 임베딩 차원 등

## 2. 설정 확장 작업

### ✨ config/settings.yaml에 추가할 새로운 섹션들

```yaml
# 파일 경로 설정
paths:
  default_vault_path: "/Users/msbaek/DocumentsLocal/msbaek_vault"  # 사용자별 조정 가능
  config_dir: "config"
  cache_dir: "cache" 
  models_dir: "models"
  rules_file: "~/dotfiles/.claude/commands/obsidian/add-tag.md"
  temp_dir_prefix: "vault_intelligence_"

# 파일 확장자 및 패턴
file_patterns:
  markdown_extensions: [".md", ".markdown"]
  config_extension: ".yaml"
  cache_db_extension: ".db"
  metadata_extension: ".json"
  search_patterns:
    markdown_glob: "*.md"
    recursive_markdown: "**/*.md"

# 텍스트 처리 설정
text_processing:
  max_snippet_length: 150          # 기본 스니펫 길이
  extended_snippet_length: 200     # 확장 스니펫 길이  
  max_document_preview: 2048       # 문서 미리보기 최대 길이
  max_title_display: 50            # 제목 표시 최대 길이
  chunk_multiplier: 20             # 배치 크기 대비 청크 배수
  max_word_count_analysis: 2000    # 분석용 최대 단어 수

# UI/표시 설정  
display:
  separator_length: 50             # 구분선 길이 ("=" * 50, "-" * 50)
  default_results_count: 20        # 기본 결과 표시 개수
  max_results_display: 50          # 최대 결과 표시 개수
  progress_update_interval: 50     # 진행률 업데이트 간격

# 파일 시스템 설정
file_system:
  bytes_to_kb_divisor: 1024        # KB 변환 제수
  bytes_to_mb_divisor: 1048576     # MB 변환 제수 (1024*1024)

# 신뢰도/품질 설정 (기존 threshold들을 체계화)
thresholds:
  high_confidence: 0.7             # 높은 신뢰도 임계값
  medium_confidence: 0.3           # 중간 신뢰도 임계값 (기본 검색 임계값)
  low_confidence: 0.1              # 낮은 신뢰도 임계값
  weight_decay_factor: 0.1         # 가중치 감소 인수
  min_weight_limit: 0.3           # 최소 가중치 제한

# 그래프 시각화 설정
visualization:
  node_size_min: 200              # 최소 노드 크기
  node_size_max: 800              # 최대 노드 크기
  node_size_multiplier: 100       # 노드 크기 배수
  edge_alpha: 0.3                 # 엣지 투명도
  edge_width: 0.5                 # 엣지 두께
  grid_alpha: 0.3                 # 격자 투명도
  spring_layout_k: 1              # 스프링 레이아웃 K값
  spring_iterations: 50           # 스프링 반복 횟수
  font_size: 14                   # 폰트 크기
  title_pad: 20                   # 제목 패딩

# 배치 처리 설정
batch_processing:
  default_chunk_size: 200         # 기본 청크 크기
  max_candidates: 100             # 최대 후보 수
  initial_candidate_multiplier: 3  # 초기 후보 배수
```

## 3. 코드 리팩토링 작업

### 🔧 수정할 파일들과 작업 내용

#### Phase 1: 설정 파일 및 경로 관련 (우선순위 높음)

1. **src/__main__.py**
   - Line 907: 기본 vault 경로 하드 코딩 제거 → `config.get('paths', {}).get('default_vault_path')`
   - Line 42: config 파일 경로 설정화
   - Line 938, 1028: CLI 기본값 0.3 → `config.get('thresholds', {}).get('medium_confidence', 0.3)`
   - Line 845: 신뢰도 0.7 → `config.get('thresholds', {}).get('high_confidence', 0.7)`
   - 구분선 길이들 → `config.get('display', {}).get('separator_length', 50)`

2. **src/features/tag_rule_engine.py**
   - Line 31: 규칙 파일 경로 하드 코딩 제거 → `config.get('paths', {}).get('rules_file')`

#### Phase 2: 핵심 엔진 모듈 (우선순위 높음)

3. **src/core/sentence_transformer_engine.py**
   - Line 156: 청크 크기 계산의 20 배수 → `config.get('text_processing', {}).get('chunk_multiplier', 20)`
   - Line 99: 임베딩 차원 1024 → `config.get('model', {}).get('dimension', 1024)`
   - 가중치 0.7, 0.3 → config 값 사용

4. **src/features/semantic_tagger.py**
   - Line 73: 'models/' 캐시 폴더 → `config.get('paths', {}).get('models_dir', 'models/')`
   - Line 165: max_words=20 → `config.get('text_processing', {}).get('max_key_words', 20)`
   - Line 256, 262: 신뢰도 임계값들 → config 값 사용
   - Line 244: 임베딩 차원 1024 → config 값 사용

5. **src/features/advanced_search.py**  
   - Line 660: 스니펫 길이 150 → `config.get('text_processing', {}).get('max_snippet_length', 150)`
   - Line 485, 486: 가중치 0.7, 0.3 → config 값
   - Line 837: 최대 문서 수 50 → `config.get('batch_processing', {}).get('max_documents', 50)`
   - Line 917, 918: 가중치 계산의 0.1, 0.3 → config 값

#### Phase 3: 시각화 및 분석 모듈 (우선순위 중간)

6. **src/features/knowledge_graph.py**
   - Line 613: 노드 크기 200, 800, 100 → config 값들
   - Line 623: 투명도 0.3, 너비 0.5 → config 값들
   - Line 582: 스프링 레이아웃 k=1, iterations=50 → config 값들
   - Line 666: 폰트 크기 14, 패딩 20 → config 값들

7. **src/features/colbert_search.py**
   - Line 185: 임베딩 차원 (10, 1024) → config 값
   - Line 371, 395: 텍스트 길이 200 → config 값

#### Phase 4: 기타 모듈들

8. **src/features/topic_collector.py**
   - Line 205: 상위 20개 → `config.get('display', {}).get('default_results_count', 20)`
   - Line 720, 721: top_k=20, threshold=0.1 → config 값들

9. **src/features/duplicate_detector.py**
   - Line 89, 92: 임계값들 → config 값 사용 (이미 일부 적용됨)

## 4. 구현 우선순위

### Phase 1: 설정 파일 확장 ⭐⭐⭐
- config/settings.yaml에 새로운 섹션 추가
- 기존 하드 코딩된 값들의 기본값으로 설정

### Phase 2: 경로 설정 분리 ⭐⭐⭐ 
- CLI 기본 경로들 config화 (특히 vault 경로, 규칙 파일)
- 사용자별 환경 대응 가능하게

### Phase 3: 핵심 모듈 리팩토링 ⭐⭐⭐
- sentence_transformer_engine.py
- advanced_search.py  
- semantic_tagger.py

### Phase 4: UI/시각화 모듈 ⭐⭐
- knowledge_graph.py
- __main__.py의 출력 포맷 관련

### Phase 5: 테스트 및 검증 ⭐⭐⭐
- 모든 기능 정상 작동 확인
- 기존 동작과의 호환성 검증
- 다양한 사용자 환경에서 테스트

## 5. 구현 시 주의사항

### ⚠️ 하위 호환성 보장
- 모든 config 값에 기존 하드 코딩 값을 기본값으로 설정
- 설정이 없어도 기존과 동일하게 작동하도록
- `.get()` 메서드 사용으로 안전한 fallback 구현

### 🔒 보안 및 안정성
- 파일 경로 설정 시 경로 검증 추가
- 상대 경로/절대 경로 처리 주의
- 사용자 입력 값 검증 강화

### 📊 성능 고려사항
- config 로딩 횟수 최소화 (한 번만 로딩하여 재사용)
- 중요한 경로에서는 config 조회 오버헤드 고려

### 🧪 테스트 전략
- 각 Phase 완료 후 기본 기능 테스트
- 다양한 config 값으로 동작 검증
- 기존 사용자 워크플로우 호환성 확인

## 6. 예상 효과

### 🎯 즉시 효과
- **개인화**: 각 사용자가 자신의 vault 경로, 규칙 파일 위치 설정 가능
- **유연성**: 임계값, 표시 개수 등을 필요에 따라 조정 가능
- **일관성**: 전체 시스템에서 통일된 값 사용

### 🚀 장기 효과  
- **배포 용이성**: 다른 사용자 환경에 쉽게 적용 가능
- **유지보수성**: 설정만 변경하면 동작 조정 가능
- **확장성**: 새로운 설정 추가가 용이
- **디버깅**: 설정 값 추적으로 문제 원인 파악 용이

## 7. 향후 개선 방향

### 🔮 추가 개선 아이디어
- 환경 변수를 통한 설정 오버라이드 기능
- 사용자별 프로파일 설정 지원
- 설정 값 검증 및 추천 기능
- GUI를 통한 설정 관리 인터페이스

---

이 계획을 단계별로 실행하여 시스템의 유연성과 사용성을 크게 향상시킬 수 있습니다.