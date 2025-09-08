# 🧠 Vault Intelligence System V2

**고품질 BGE-M3 임베딩 기반 Obsidian vault 지능형 검색 및 관리 시스템**

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![BGE-M3](https://img.shields.io/badge/BGE--M3-1024dim-green.svg)](https://huggingface.co/BAAI/bge-m3)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## ✨ 주요 특징

- 🔍 **다층 검색**: Dense + Sparse + ColBERT + Cross-encoder Reranking
- 🏷️ **자동 태깅**: BGE-M3 기반 의미적 태그 자동 생성  
- 📚 **문서 요약**: 클러스터링 기반 다중 문서 지능형 요약
- 🕸️ **지식 그래프**: 문서 간 관계 분석 및 추천 시스템
- 📋 **MOC 생성**: 주제별 체계적 목차 자동 생성
- 🇰🇷 **한국어 최적화**: 동의어 확장 및 HyDE 기술
- ⚡ **M1 Pro 최적화**: Metal Performance Shaders 가속

## 🚀 빠른 시작

### 1. 설치
```bash
git clone https://github.com/your-username/vault-intelligence.git
cd vault-intelligence
pip install -r requirements.txt
```

### 2. 시스템 초기화
```bash
python -m src init --vault-path /path/to/your/vault
```

### 3. 기본 사용법
```bash
# 하이브리드 검색 (Dense + BM25, 추천)
python -m src search --query "TDD 테스트 주도 개발" --search-method hybrid

# 고정밀 재순위화 검색 (BGE Reranker V2-M3)
python -m src search --query "clean architecture principles" --rerank

# ColBERT 토큰 수준 검색 (긴 문장에 최적화)
python -m src search --query "refactoring clean code practices" --search-method colbert

# 주제별 문서 수집
python -m src collect --topic "리팩토링"

# 문서 클러스터링 및 요약 (Phase 9)
python -m src summarize --clusters 5

# 학습 리뷰 생성  
python -m src review --period weekly
```

## 📖 문서 가이드

- [📚 사용자 가이드](docs/USER_GUIDE.md) - 완전한 사용법 매뉴얼
- [💡 실전 예제](docs/EXAMPLES.md) - 다양한 활용 사례
- [🔧 문제 해결](docs/TROUBLESHOOTING.md) - 기술 지원 가이드
- [⚙️ 개발자 가이드](CLAUDE.md) - 개발 및 확장 정보
- [📊 샘플 결과](samples/) - 기능별 샘플 출력

## 🎯 주요 기능

| 기능 | 설명 | 명령어 |
|------|------|--------|
| **하이브리드 검색** | Dense + Sparse 결합 검색 (추천) | `search --query "검색어" --search-method hybrid` |
| **ColBERT 검색** | 토큰 수준 정밀 매칭 | `search --query "긴 문장" --search-method colbert` |
| **재순위화** | Cross-encoder로 정확도 향상 | `search --query "검색어" --rerank` ✨ |
| **태깅** | 자동 태그 생성 | `tag "문서경로"` |
| **수집** | 주제별 문서 수집 | `collect --topic "주제"` |
| **요약** | 다중 문서 요약 | `summarize --clusters N` |
| **리뷰** | 학습 패턴 분석 | `review --period weekly` |
| **MOC** | 체계적 목차 생성 | `generate-moc --topic "주제"` |

## 🏗️ 아키텍처

```
Vault Intelligence V2
├── BGE-M3 임베딩 엔진 (1024차원)
├── 다층 검색 시스템
│   ├── Dense Search (의미적)
│   ├── Sparse Search (키워드) 
│   ├── ColBERT Search (토큰 수준)
│   └── Cross-encoder Reranking
├── 지능형 캐싱 (SQLite)
└── 고급 분석 도구
    ├── 지식 그래프 분석
    ├── 자동 클러스터링
    ├── 문서 요약 시스템
    └── 학습 패턴 분석
```

## 🔧 시스템 요구사항

- Python 3.11+
- 8GB+ RAM (대용량 vault용)
- Apple Silicon (M1/M2) 권장 또는 CUDA GPU
- 1GB+ 디스크 공간 (모델 캐시용)

## 📈 성능

- **검색 속도**: 1000개 문서 기준 < 1초
- **인덱싱**: 1000개 문서 기준 10-20분
- **메모리**: 평상시 2-3GB, 인덱싱시 6-8GB
- **정확도**: Cross-encoder 재순위화로 최고 품질

## 🤝 기여하기

1. 이슈 보고: [Issues](https://github.com/your-username/vault-intelligence/issues)
2. 기능 제안: [Discussions](https://github.com/your-username/vault-intelligence/discussions)  
3. 풀 리퀘스트: [CONTRIBUTING.md](CONTRIBUTING.md) 참조

## 🔒 보안

이 프로젝트는 강화된 보안 시스템을 갖추고 있습니다:

### 자동 보안 검사
```bash
# 전체 프로젝트 보안 스캔
./scripts/security-check.sh

# Git 커밋 시 자동 검사 (pre-commit hook 활성화됨)
git commit -m "변경사항"  # 자동으로 민감정보 검사

# Gitleaks로 추가 검사
gitleaks detect --config .gitleaks.toml
```

### 보안 기능들
- ✅ **Pre-commit Hook**: 커밋 시 자동 민감정보 감지
- ✅ **Security Scanner**: 종합 보안 점검 스크립트
- ✅ **Gitleaks 통합**: 업계 표준 비밀정보 스캔
- ✅ **패턴 감지**: API 키, 비밀번호, 토큰 등 자동 감지
- ✅ **환경변수 보호**: .env 파일 추적 방지

### 민감정보 관리
```bash
# 환경변수는 .env.example 템플릿 사용
cp .env.example .env
# .env 파일을 편집하여 실제 API 키 입력 (git 추적 안됨)

# 보안 검사 실행
./scripts/security-check.sh --patterns  # 검사 패턴 확인
```

자세한 내용은 [SECURITY.md](SECURITY.md)를 참조하세요.

## 📄 라이센스

이 프로젝트는 [MIT License](LICENSE) 하에 배포됩니다.

## 🙏 감사

- [BGE-M3](https://huggingface.co/BAAI/bge-m3) - 고품질 다국어 임베딩
- [FlagEmbedding](https://github.com/FlagOpen/FlagEmbedding) - 임베딩 라이브러리
- [Obsidian](https://obsidian.md) - 지식 관리 시스템