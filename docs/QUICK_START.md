# 🚀 5분 빠른 시작 가이드

Vault Intelligence System V2를 빠르게 시작하여 첫 검색까지 실행해보세요!

## 📋 준비 사항

- Python 3.11 이상
- 4GB+ RAM
- Obsidian vault (마크다운 파일들)

## ⚡ 설치 및 실행

### 1단계: 설치

```bash
git clone https://github.com/msbaek/vault-intelligence.git ~/git/vault-intelligence
cd ~/git/vault-intelligence
pip install -r requirements.txt
```

#### pipx 전역 설치 (권장 - 어디서든 `vis` 명령어 사용 가능)
```bash
pipx install -e ~/git/vault-intelligence
```

### 2단계: 시스템 초기화
```bash
# pipx 설치 시
vis init --vault-path /path/to/your/vault

# 소스 실행 시
vis init --vault-path /path/to/your/vault
```

### 3단계: 첫 검색 실행
```bash
# 기본 검색
vis search "관심 주제"

# 예시: TDD 관련 검색
vis search "TDD"
```

## ✅ 설치 확인

```bash
# 시스템 정보 확인
vis info

# 간단한 테스트
vis test
```

**예상 출력:**
```
✅ NumPy: 2.3.2
✅ Scikit-learn: 1.7.1  
✅ PyYAML 사용 가능
✅ 모든 의존성이 설치되었습니다!
```

## 🎯 첫 번째 기능들

### 1. 의미적 검색
```bash
vis search "리팩토링" --top-k 5
```

### 2. 주제별 문서 수집
```bash
vis collect "클린코드" --top-k 10
```

### 3. 자동 태깅
```bash
vis tag "문서경로.md" --dry-run
```

### 4. MOC 자동 생성 (체계적 목차)
```bash
vis generate-moc "TDD"
```

### 5. 문서 클러스터링 및 요약 (Phase 9)
```bash
vis summarize --clusters 3
```

### 6. 학습 리뷰 생성
```bash
vis review --period weekly
```

## 🎛️ 주요 옵션들

### 검색 고급화
```bash
# 재순위화 (최고 품질)
vis search "TDD" --rerank

# 쿼리 확장 (최대 포괄성)  
vis search "TDD" --expand
```

### 유사도 임계값 조정
```bash
# 더 넓은 결과
vis search "TDD" --threshold 0.1

# 더 정확한 결과
vis search "TDD" --threshold 0.5
```

## 🔧 문제 해결

### 메모리 부족 시
```yaml
# config/settings.yaml 수정
model:
  batch_size: 4  # 기본값 8에서 감소
  num_workers: 4  # 기본값 6에서 감소
```

### 검색 결과가 없을 때
```bash
# 임계값 낮추기
vis search "검색어" --threshold 0.1

# 강제 재인덱싱
vis reindex --force
```

### 느린 처리 속도
```bash
# 샘플링 모드로 빠른 테스트
vis search "검색어" --sample-size 100
```

## 📚 다음 단계

축하합니다! 기본 사용법을 익혔습니다. 이제 더 자세한 가이드들을 확인해보세요:

- **[📖 사용자 가이드](USER_GUIDE.md)** - 모든 기능의 완전한 설명
- **[💡 실전 예제](EXAMPLES.md)** - 다양한 상황별 활용법
- **[🔧 문제 해결](TROUBLESHOOTING.md)** - 일반적인 문제들의 해결책
- **[⚙️ 개발자 가이드](../CLAUDE.md)** - 시스템 내부 구조와 확장 방법

## 💬 도움이 필요하시면

- [GitHub Issues](https://github.com/your-username/vault-intelligence/issues) - 버그 리포트나 기능 요청
- [Discussions](https://github.com/your-username/vault-intelligence/discussions) - 질문이나 아이디어 공유

**즐거운 지식 탐험 되세요! 🧠✨**