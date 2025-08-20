# Vault Intelligence 주제별 정리 워크플로우

**목적**: Vault Intelligence System V2를 사용하여 특정 주제에 대한 문서들을 수집하고 체계적으로 정리하는 절차

**작업 일자**: 2025-08-20  
**예제 주제**: TDD (Test Driven Development)

## 📋 사전 준비사항

### 1. 시스템 요구사항
- Python 3.11+
- Vault Intelligence System V2 설치
- Obsidian vault 경로 설정

### 2. 필수 의존성 확인
```bash
pip install -r requirements.txt
```

### 3. Vault 경로 설정
```bash
# vault 경로를 사용자 환경에 맞게 수정
export VAULT_PATH="/Users/msbaek/DocumentsLocal/msbaek_vault"
```

## 🔄 단계별 워크플로우

### Phase 1: 시스템 초기화 및 상태 확인

#### 1-1. 시스템 정보 확인
```bash
cd /Users/msbaek/git/vault-intelligence
python -m src info
```

**목적**: 현재 시스템 상태, 설정, 기능 확인

#### 1-2. Vault 초기화 (필요시)
```bash
python -m src init --vault-path /Users/msbaek/DocumentsLocal/msbaek_vault
```

**결과**: 
- 의존성 확인 완료
- TF-IDF 엔진 훈련
- 캐시 시스템 초기화
- Vault 프로세서 초기화

**예상 출력**: `✅ 시스템 초기화 완료!`

### Phase 2: 기본 주제 문서 수집

#### 2-1. 주제별 문서 수집 실행
```bash
python -m src collect --topic "[주제명]" --output [주제명]-topics.md
```

**예제**:
```bash
python -m src collect --topic "TDD" --output tdd-topics.md
```

**결과 예시**:
- 수집 문서: 10개
- 총 단어수: 25,009개
- 태그 분포 및 디렉토리 분포 제공
- 자동 생성된 마크다운 컬렉션

#### 2-2. 수집 결과 검토
```bash
# 생성된 파일 확인
cat [주제명]-topics.md | head -20
```

### Phase 3: 확장 검색 및 관련 주제 탐색

#### 3-1. 확장 키워드 검색
```bash
# 영문 확장 검색
python -m src search --query "[English Topic Name]" --top-k 15

# 관련 키워드 검색  
python -m src search --query "[관련 키워드]" --top-k 10
```

**예제**:
```bash
python -m src search --query "Test Driven Development" --top-k 15
python -m src search --query "unit test" --top-k 10
python -m src search --query "refactoring" --top-k 10
```

#### 3-2. 검색 결과 분석
- 유사도 점수 확인
- 매치 타입 (semantic/keyword/hybrid) 분석
- 추가 관련 문서 식별

### Phase 4: 체계적 주제별 정리 문서 작성

#### 4-1. 주제 분류 체계 수립
**기본 구조**:
1. 기본 개념 및 원리
2. 실습 및 워크샵
3. 일반적인 오해와 문제점
4. 관련 방법론 (BDD, DDD 등)
5. 통합 접근법
6. 도구와 기법
7. 아키텍처 관점
8. 현대적 접근법

#### 4-2. 종합 정리 문서 작성
```bash
# 수동으로 종합 분석 문서 작성
# 파일명: [주제명]-주제별-정리.md
```

**포함 내용**:
- 주요 주제 분류 (8-10개 카테고리)
- 각 주제별 핵심 문서 링크
- 학습 로드맵 제시
- 통계 정보
- 추천 학습 자료

## 🛠️ 고급 활용 기법

### 중복 문서 제거
```bash
python -m src duplicates
```

### 주제 분석 및 클러스터링
```bash
python -m src analyze
```

### 전체 재인덱싱 (필요시)
```bash
python -m src reindex --force
```

## 📝 문서 작성 템플릿

### 기본 구조
```markdown
# [주제명] 주제별 정리

**생성일**: YYYY-MM-DD
**총 수집 문서**: N개
**주요 키워드**: keyword1, keyword2, keyword3

## 📚 주요 주제 분류

### 1. [분류명 1]
#### [세부 주제]
- **핵심 개념**: 설명
- **주요 참고 문서**: 경로와 설명

### 2. [분류명 2]
...

## 🎯 [주제명] 학습 로드맵

### 초급 단계
### 중급 단계  
### 고급 단계

## 📊 통계 정보
## 🔗 추가 학습 자료
```

## ⚡ 자동화 스크립트 (선택사항)

### 전체 워크플로우 자동화
```bash
#!/bin/bash
# topic-analysis-workflow.sh

TOPIC=$1
OUTPUT_DIR="./analysis-results"

if [ -z "$TOPIC" ]; then
    echo "사용법: $0 <주제명>"
    exit 1
fi

echo "📋 $TOPIC 주제 분석 시작..."

# 1. 기본 수집
echo "1️⃣ 기본 문서 수집..."
python -m src collect --topic "$TOPIC" --output "$OUTPUT_DIR/${TOPIC}-topics.md"

# 2. 확장 검색
echo "2️⃣ 확장 검색 실행..."
python -m src search --query "$TOPIC" --top-k 15 > "$OUTPUT_DIR/${TOPIC}-search-results.txt"

# 3. 영문 검색 (필요시)
echo "3️⃣ 영문 검색 실행..."
python -m src search --query "$TOPIC english equivalent" --top-k 10 >> "$OUTPUT_DIR/${TOPIC}-search-results.txt"

echo "✅ $TOPIC 주제 분석 완료!"
echo "📁 결과 파일: $OUTPUT_DIR/${TOPIC}-topics.md"
echo "📄 검색 결과: $OUTPUT_DIR/${TOPIC}-search-results.txt"
```

### 사용법
```bash
chmod +x topic-analysis-workflow.sh
./topic-analysis-workflow.sh "TDD"
./topic-analysis-workflow.sh "Clean Architecture"
./topic-analysis-workflow.sh "리팩토링"
```

## 🔍 품질 확인 체크리스트

### 수집 단계 체크리스트
- [ ] 시스템 초기화 완료
- [ ] Vault 경로 올바른 설정
- [ ] 기본 문서 수집 (10개 이상)
- [ ] 태그 분포 분석 완료
- [ ] 디렉토리 분포 확인

### 확장 검색 체크리스트
- [ ] 영문 키워드 검색 완료
- [ ] 관련 키워드 검색 완료 (unit test, refactoring 등)
- [ ] 유사도 점수 분석
- [ ] 추가 관련 문서 식별

### 문서 작성 체크리스트
- [ ] 8-10개 주요 카테고리 분류
- [ ] 각 카테고리별 대표 문서 링크
- [ ] 학습 로드맵 제시
- [ ] 통계 정보 포함
- [ ] 추가 학습 자료 제안

## 🚨 주의사항 및 트러블슈팅

### 일반적인 문제들

**임베딩 생성 실패**
```bash
# 해결책: 의존성 확인 및 캐시 초기화
python -m src test
rm -rf cache/
python -m src init --vault-path [VAULT_PATH]
```

**검색 결과 없음**
```bash
# 해결책: 유사도 임계값 조정
python -m src search --query "[주제]" --threshold 0.1
```

**메모리 부족**
- config/settings.yaml에서 batch_size 감소
- max_features 값 조정

### 성능 최적화
- 대용량 vault의 경우 청크 단위 처리
- GPU 사용 가능시 enable_gpu: true 설정
- 진행률 표시로 사용자 경험 개선

## 📈 확장 가능한 활용방안

### 1. 정기적 주제 분석
- 월별 주제 트렌드 분석
- 새로운 문서 추가 시 자동 재분석

### 2. 다중 주제 비교 분석
```bash
./topic-analysis-workflow.sh "TDD"
./topic-analysis-workflow.sh "BDD" 
./topic-analysis-workflow.sh "DDD"
# 이후 주제간 연관성 분석
```

### 3. 지식 그래프 구축
- 주제별 문서 네트워크 시각화
- 연관 주제 자동 추천

---

**작성일**: 2025-08-20  
**버전**: 1.0  
**기반 시스템**: Vault Intelligence System V2  
**테스트 주제**: TDD (Test Driven Development)

이 워크플로우는 지속적으로 개선되며, 새로운 기능이 추가될 때마다 업데이트됩니다.