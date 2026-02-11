# 🧠 Vault Intelligence System V2

**고품질 BGE-M3 임베딩 기반 Obsidian vault 지능형 검색 및 관리 시스템**

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![BGE-M3](https://img.shields.io/badge/BGE--M3-1024dim-green.svg)](https://huggingface.co/BAAI/bge-m3)
[![License: PolyForm Noncommercial](https://img.shields.io/badge/License-PolyForm%20Noncommercial-blue.svg)](https://polyformproject.org/licenses/noncommercial/1.0.0/)

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

#### 방법 A: pipx 설치 (권장 - 어디서든 실행 가능)
```bash
pipx install -e ~/git/vault-intelligence
# 이후 어디서든 vault-intel 명령어 사용 가능
```

#### 방법 B: 소스에서 직접 실행
```bash
git clone https://github.com/your-username/vault-intelligence.git
cd vault-intelligence
pip install -r requirements.txt
```

### 2. 시스템 초기화
```bash
vault-intel init --vault-path /path/to/your/vault
# 또는: python -m src init --vault-path /path/to/your/vault
```

### 3. 기본 사용법

#### 💬 Claude Code에서 사용 (권장)

Claude Code 세션에서 자연어로 요청하세요:

- "TDD 관련 문서 찾아줘"
- "리팩토링 MOC 만들어줘"
- "최근 학습 내용 요약해줘"
- "이 문서와 관련된 다른 문서 찾아줘"

Claude가 vault-intelligence를 자동으로 활용하여 결과를 제공합니다.

#### 🖥️ CLI 직접 사용

```bash
# 하이브리드 검색 (Dense + BM25, 추천)
vault-intel search --query "TDD 테스트 주도 개발" --search-method hybrid

# 고정밀 재순위화 검색 (BGE Reranker V2-M3)
vault-intel search --query "clean architecture principles" --rerank

# ColBERT 토큰 수준 검색 (긴 문장에 최적화)
vault-intel search --query "refactoring clean code practices" --search-method colbert

# 주제별 문서 수집
vault-intel collect --topic "리팩토링"

# 문서 클러스터링 및 요약 (Phase 9)
vault-intel summarize --clusters 5

# 학습 리뷰 생성
vault-intel review --period weekly
```

> **참고:** `vault-intel` 대신 기존 `python -m src` 방식도 프로젝트 디렉토리에서 동일하게 사용 가능합니다.

## 📖 문서 인덱스

### 사용자 가이드

- **[5분 빠른 시작](docs/user/QUICK_START.md)**
  pipx 설치부터 첫 검색까지 5분 안에 시작하는 최소 가이드.
  설치, 초기화, 검색 실행, 주요 옵션 맛보기를 단계별로 안내.

- **[전체 사용자 가이드](docs/user/USER_GUIDE.md)**
  모든 기능을 상세히 설명하는 완전한 매뉴얼(1,672라인).
  기본/고급 검색, 재순위화, 쿼리 확장, 태깅, MOC 생성, 클러스터링 등 전 기능 커버.

- **[실전 예제](docs/user/EXAMPLES.md)**
  Claude Code 대화형 사용과 CLI 직접 사용의 구체적 예제 모음.
  문서 검색, MOC 생성, 분석/리뷰, 글쓰기 지원 등 실제 워크플로우 시나리오 제공.

- **[문제 해결](docs/user/TROUBLESHOOTING.md)**
  사용 중 발생 가능한 문제와 해결 방법을 정리한 기술 지원 가이드.
  한글 폰트 깨짐, 임베딩 캐시 오류, 메모리 부족, 느린 처리 속도 등의 해결책 제공.

### 개발자 참고

- **[개발자 가이드 (CLAUDE.md)](CLAUDE.md)**
  Claude Code가 참조하는 CLI 빠른 참조 및 시스템 아키텍처 문서.
  모듈 구조, 주요 API, 확장 가이드, 디버깅 방법, 성능 튜닝 가이드 포함.

- **[개발 히스토리](DEVELOPMENT.md)**
  Phase 1(Sentence Transformers 도입)부터 Phase 9(다중 문서 요약)까지의 개발 과정 기록.
  Claude Code 활용 패턴, 실제 활용 사례(AI Practice 기법 수집 등), 핵심 교훈 정리.

- **[변경 이력](CHANGELOG.md)**
  프로젝트의 모든 변경 사항을 시간순으로 기록한 변경 로그.
  pipx 설치 지원(2026-02-11)부터 Phase 1-9 개발 과정까지의 상세 업데이트 내역.

- **[기여 가이드](CONTRIBUTING.md)**
  오픈소스 기여자를 위한 종합 가이드.
  개발 환경 설정, 코딩 표준, 테스트 가이드, PR 프로세스, 커밋 메시지 규칙 설명.

- **[보안 정책](SECURITY.md)**
  민감정보 관리 및 보안 가이드라인.
  환경변수 관리, 자동 보안 검사(pre-commit hook, Gitleaks), 사고 대응 절차 포함.

### 설계 문서

- **[문서 인덱스](docs/README.md)**
  docs 디렉토리의 전체 문서 목록과 사용 상황별 안내를 제공하는 인덱스 문서.

- **[Phase 9 PRD](docs/dev/multi-document-summarization-prd.md)**
  다중 문서 요약 시스템의 제품 요구사항 문서.
  의미적 클러스터링, Claude Code LLM 요약, 학습 리뷰 생성 등의 기능 요구사항 정의.

- **[Phase 9 구현 계획](docs/dev/phase9-implementation-plan.md)**
  Phase 9의 4단계 상세 구현 계획.
  문서 클러스터링, LLM 요약, 학습 리뷰 통합, 테스트 최적화 단계별 체크리스트 제공.

- **[임베딩 업그레이드 계획](docs/dev/embedding-upgrade-plan.md)**
  TF-IDF에서 BGE-M3로의 업그레이드 설계 문서.
  Hybrid Search(Dense+Sparse+ColBERT) 아키텍처 설계, Reranking Layer 추가 계획 포함.

- **[문서 감사 리포트](docs/DOCUMENTATION_AUDIT_REPORT.md)**
  33개 마크다운 문서의 품질 감사 결과 리포트.
  CLI 옵션 정확도 100%, 최신성 완벽 반영 등을 확인하여 5/5점 최상위 평가 부여.

### 산출물

- **[AI Practice 요약](docs/AI-PRACTICE-SUMMARY.md)**
  vault-intelligence로 286개 AI 문서에서 1,403개 실용 기법을 추출한 프로젝트 요약.
  AI-Assisted Development(574개), Prompt Engineering(272개) 등 6개 카테고리별 핵심 기법 정리.

- **[배치별 상세 결과](archive/ai-practice/)**
  AI Practice 수집 프로젝트의 29개 배치별 원본 분석 결과 아카이브.

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

이 프로젝트는 [PolyForm Noncommercial License 1.0.0](LICENSE) 하에 배포됩니다.

- **비영리 목적**: 자유롭게 사용 가능 (연구, 교육, 개인 학습, 취미 등)
- **영리 목적**: 별도 상업 라이센스 필요 (문의 요망)

## 🙏 감사

- [BGE-M3](https://huggingface.co/BAAI/bge-m3) - 고품질 다국어 임베딩
- [FlagEmbedding](https://github.com/FlagOpen/FlagEmbedding) - 임베딩 라이브러리
- [Obsidian](https://obsidian.md) - 지식 관리 시스템