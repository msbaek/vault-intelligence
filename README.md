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

### 3. 기본 검색
```bash
# 의미적 검색
python -m src search --query "TDD"

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
| **검색** | 하이브리드 의미적 검색 | `search --query "검색어"` |
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

## 📄 라이센스

이 프로젝트는 [MIT License](LICENSE) 하에 배포됩니다.

## 🙏 감사

- [BGE-M3](https://huggingface.co/BAAI/bge-m3) - 고품질 다국어 임베딩
- [FlagEmbedding](https://github.com/FlagOpen/FlagEmbedding) - 임베딩 라이브러리
- [Obsidian](https://obsidian.md) - 지식 관리 시스템