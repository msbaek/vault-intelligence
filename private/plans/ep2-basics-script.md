# 핵심 기능 완전 정복

## 설치 & 셋업

```bash
# 1. 저장소 클론
git clone https://github.com/msbaek/vault-intelligence
cd vault-intelligence

# 2. 의존성 설치
pip install -r requirements.txt

# 3. Vault 경로 설정
python -m src init --vault-path ~/your-vault-path // 자신의 Obsidian Vault
경로로 변경

# 4. 시스템 정보 확인
python -m src info
```

### [화면에 보이는 것]

```
📁 사용 중인 Vault 경로: /Users/msbaek/DocumentsLocal/msbaek_vault
ℹ️ Vault Intelligence System V2
==================================================
프로젝트 경로: /Users/msbaek/git/vault-intelligence
Python 버전: 3.11.7
PyTorch 장치: MPS (Metal)

💾 캐시 상태:
- Dense 임베딩: 3,505개
- ColBERT 임베딩: 2,410개
- 캐시 DB 크기: 12911.2MB

⚡ 기본 명령어:
  python -m src search --query 'TDD'
  python -m src collect --topic '리팩토링'
```

현재 Vault에는 3,505개의 문서가 인덱싱되어 있음.
처음 인덱싱에는 시간이 좀 걸리지만, 한 번 만들어두면 캐시로 저장돼서 다음부터는 빠름

### 문서가 많을 때는 폴더별로 나눠서 인덱싱

이런 방법은 현 repo를 clone하고 그 폴더에서 claude code를 실행 한 후 물어보면 됨

```bash
# 1단계: 초기 설정만 (인덱싱 없음)

python -m src init --vault-path /Users/username/DocumentsLocal/msbaek_vault

# 2단계: 폴더별 순차 인덱싱

python -m src reindex --include-folders 003-RESOURCES
python -m src reindex --include-folders work-log notes
python -m src reindex --include-folders 997-BOOKS 001-INBOX
python -m src reindex --include-folders 998-PRIVATE writerside coffee-time STUDY 000-SLIPBOX WIP
105-PROJECTS
```

## 4가지 검색 방법 비교

### 1: Semantic 검색 (의미 기반)

```bash
python -m src search --query "TDD" --search-method semantic --top-k 5
```

**Semantic 검색**은 의미 기반으로 찾음. BGE-M3라는 최신 임베딩 모델을 사용하는데, 재미있는 건 "TDD"라는 단어가 직접 들어있지 않아도 관련된 내용을 찾아냄.

`--rerank` 옵션을 주면 더 정확해짐

**장점**: 개념적 검색에 강함
**단점**: 정확한 용어 매칭이 필요할 때는 부족할 수 있음

### 2: Keyword 검색 (정확한 용어)

```bash
python -m src search --query "TDD" --search-method keyword --top-k 5
```

**Keyword 검색**은 정확히 "TDD"라는 단어가 들어간 문서만 찾음. BM25라는 검색 알고리즘을 사용

`--expand`, `--with-centrality` 옵션과 함께 쓰면 더 강력해짐

**장점**: 정확한 용어 검색, 빠른 속도
**단점**: 동의어나 유사 개념은 놓칠 수 있음

### 3: Hybrid 검색 (균형잡힌 최강자)

```bash
python -m src search --query "TDD" --search-method hybrid --top-k 5
```

**Hybrid 검색**은 semantic과 keyword를 섞은 것. 기본 가중치는 semantic 70%, keyword 30%.

실전에서는 대부분 이 hybrid 검색을 추천함. **가장 밸런스가 좋음**

**권장**: 일반적인 모든 검색에 사용
**속도**: 빠름 ⚡⚡⚡
**정확도**: 높음 ⭐⭐⭐⭐

### 4: ColBERT 검색 (토큰 단위 정밀 검색)

문서를 토큰 단위로 쪼개서 각각 임베딩을 만듦. 그래서 긴 문장이나 복잡한 개념을 검색할 때 더 정확

```bash
python -m src search --query "TDD" --search-method colbert --top-k 5
```

ColBERT는 처음 실행할 때 인덱싱 시간이 좀 걸림. 왜냐하면 모든 문서의 모든 토큰을 임베딩함. 하지만 한 번 만들어두면 증분 캐싱이 되므로, 다음부터는 빠름.

**사용 상황**: 긴 문장, 복합 개념 검색
**속도**: 느림 ⚡⚡ (하지만 캐싱으로 개선)
**정확도**: 매우 높음 ⭐⭐⭐⭐

## 고급 검색 옵션 3종 세트

### 옵션 1: --rerank (재순위화로 정확도 UP)

```bash
python -m src search --query "TDD" --rerank --top-k 5
```

**--rerank** 옵션은 BGE Reranker V2-M3라는 Cross-encoder 모델을 사용합니다.

프로세스는 다음과 같음:

1. 먼저 hybrid 검색으로 30개 후보를 찾음
2. 그 후보들을 Reranker로 다시 채점
3. 최종 5개를 선택

**추천**: 정확도가 중요한 검색
**단점**: 시간이 조금 더 걸림

### 옵션 2: --expand (쿼리 확장으로 포괄성 UP)

```bash
python -m src search --query "TDD" --expand --top-k 5
```

```
📝 쿼리 확장 모드 활성화
   확장 기능: 동의어, HyDE

📄 검색 결과 (5개):
--------------------------------------------------------------------------------
1. 켄트 백의 아규먼티드 코딩: TDD와 AI를 활용한 작동하는 깔끔한 코드 (유사도: 15.8135)
   타입: hybrid_expanded_hyde
   키워드: 테스트, 주도, 개발, tdd, 소프트웨어, 개발, 방법론...

2. TDD-Theme & Variations (유사도: 13.0871)
   키워드: 테스트, 주도, 개발, tdd, red, green, refactor...
```

**--expand** 옵션은 두 가지를 합니다:

1. **동의어 확장**: "TDD" → "테스트 주도 개발", "Test Driven Development"
2. **HyDE (Hypothetical Document Embeddings)**: "TDD가 뭔지 설명하는 가상의 문서"를 만들어서 검색

결과를 보면 키워드가 엄청 많음. "테스트", "주도", "개발", "red", "green", "refactor" 등등... 이게 다 동의어와 HyDE로 확장된 검색어들임.

유사도 점수도 15.8135로 엄청 높은데, 이건 여러 쿼리의 점수를 합쳤기 때문.

**추천**: 포괄적인 검색이 필요할 때
**단점**: 속도가 느림 (여러 번 검색하니까)

### 옵션 3: --with-centrality (중심성 점수 반영)

```bash
python -m src search --query "TDD" --with-centrality --top-k 5
```

```
🎯 중심성 부스팅 활성화 (가중치: 0.2)

📄 검색 결과 (5개):
--------------------------------------------------------------------------------
1. Test And Test Doubles (유사도: 1.7987)

2. 클린 애자일(Back to Basics) (유사도: 1.7945)
```

**--with-centrality** 옵션은 문서의 "중요도"를 고려함

중요도는 다른 문서들과 얼마나 많이 연결되어 있는지로 판단. Obsidian의 백링크, 태그, 내용 유사도 등을 종합해서 계산.

**추천**: 핵심 문서를 찾고 싶을 때
**가중치**: 기본 0.2 (20%)

## 관련 문서 탐색 & 자동 태깅

### 관련 문서 찾기

```bash
python -m src related --file "TDD-Theme & Variations.md" --top-k 10
```

**related** 명령은 특정 문서와 관련된 다른 문서를 찾아줌

"TDD-Theme & Variations"라는 노트를 읽고 있는데, "이거랑 비슷한 내용 더 없었나?" 싶을 때 사용.

**활용 시나리오**:

- 새로 작성한 노트와 관련된 기존 노트 찾기
- 읽고 있는 문서의 참고 자료 추천받기
- 비슷한 주제의 문서들 한 번에 모으기

### 자동 태깅

```bash
# 단일 파일 태깅
python -m src tag "새로운-문서.md"

# 폴더 전체 재귀적 태깅
python -m src tag "INBOX/" --recursive
```

**tag** 명령은 문서 내용을 분석해서 자동으로 태그를 달아줌.

Obsidian을 쓰면서 가장 귀찮은 것 중 하나가 새 노트 만들 때마다 태그 고민하는 것. "이건 #TDD인가 #testing인가?" 같은 고민들...

이제는 그냥 내용만 쓰고, 이 명령 한 번 돌리면 끝. AI가 내용 분석해서 적절한 계층적 태그를 자동으로 붙여줌.

예를 들면:

```yaml
---
tags:
  - topic/software-engineering/tdd
  - topic/testing/unit-testing
  - source/book
  - type/note
---
```

**활용 시나리오**:

- 새로 작성한 노트에 태그 자동 부여
- 기존 노트의 태그 개선 (--recursive로 전체 vault 정리)
- 일관된 태그 체계 유지

## 부록: CLI 명령어 치트시트

### 기본 검색

```bash
python -m src search --query "TDD" --search-method [semantic|keyword|hybrid|colbert]
```

### 고급 검색

```bash
python -m src search --query "TDD" --rerank
python -m src search --query "TDD" --expand
python -m src search --query "TDD" --with-centrality
python -m src search --query "TDD" --rerank --expand  # 최고 품질
```

### 관련 문서 & 유틸리티

```bash
python -m src related --file "문서명.md" --top-k 10
python -m src tag "문서명.md"
python -m src tag "폴더명/" --recursive
python -m src info  # 시스템 정보
```

### 인덱싱

```bash
python -m src reindex                 # 기본 재인덱싱
python -m src reindex --with-colbert  # ColBERT 포함
python -m src reindex --force         # 강제 전체 재인덱싱
```
