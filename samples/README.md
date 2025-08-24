# Sample Output Files

이 디렉토리는 Vault Intelligence System V2의 다양한 기능들의 실제 출력 예시를 담고 있습니다.

## 📂 파일 구성

### 🔍 클러스터링 결과
- `clustering-*.md` - 문서 클러스터링 결과 (Phase 9)
- `clustering-TDD-*.md` - 주제별 클러스터링 예시

### 📚 학습 리뷰 
- `learning-review-weekly-*.md` - 주간 학습 활동 분석 결과
- `learning-review-monthly-*.md` - 월간 학습 진전도 리포트

### 📋 MOC (Map of Content)
- `MOC-*.md` - 자동 생성된 주제별 체계적 목차

### 🎯 주제별 분석
- `tdd-*.md` - TDD 관련 문서 수집 및 분석 결과
- `TDD-*.md` - TDD 주제별 정리 문서

### 📊 분석 리포트
- `vault_analysis_report.md` - Vault 전체 분석 리포트
- `improved_analysis_*.md` - 클러스터링 기반 상세 분석

### 🔄 워크플로우
- `vault-intelligence-*.md` - 주제별 정리 워크플로우 예시

### 📝 구현 기록
- `IMPLEMENTATION-SUMMARY.md` - 구현 완료 요약
- `IMPLEMENTATION_REPORT.md` - 상세 구현 보고서
- `SENTENCE-TRANSFORMERS-CONTEXT.md` - BGE-M3 구현 컨텍스트

## 🔒 개인정보 처리

⚠️ **주의**: 이 파일들은 실제 개인 vault에서 생성된 결과이므로 개인적인 학습 내용과 문서 제목들이 포함되어 있습니다. 

공개 레포지토리에서는 이러한 파일들을 제외하거나 익명화하여 사용하는 것을 권장합니다.

## 🎯 활용 방법

### 기능 이해하기
각 파일을 통해 시스템의 출력 형식과 분석 깊이를 확인할 수 있습니다.

### 테스트 데이터로 활용
새로운 기능 개발 시 예상 출력 형식의 참고 자료로 활용 가능합니다.

### 벤치마크 기준
시스템 성능과 분석 품질의 기준점으로 활용할 수 있습니다.

## 🚀 직접 생성해보기

본인의 vault에서 유사한 결과를 생성하려면:

```bash
# 문서 클러스터링
python -m src summarize --clusters 5

# 학습 리뷰 생성  
python -m src review --period weekly

# MOC 생성
python -m src generate-moc --topic "관심주제"

# 주제별 문서 수집
python -m src collect --topic "학습주제"
```