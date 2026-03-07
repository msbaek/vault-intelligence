# Vault Intelligence - Semantic Search for Obsidian

Obsidian vault를 위한 로컬 시맨틱 검색 엔진. BGE-M3 임베딩 기반으로 Dense, Sparse, ColBERT, Cross-encoder Reranking을 결합한 다층 하이브리드 검색을 제공합니다. 한국어 최적화 포함.

변경 이력은 [CHANGELOG](CHANGELOG.md)에서 확인할 수 있습니다.

## Quick Start

```bash
# 설치 (pipx 권장)
pipx install -e ~/git/vault-intelligence

# Vault 초기화 및 인덱싱
vis init --vault-path ~/my-vault
vis reindex

# 검색
vis search "TDD"                              # 하이브리드 검색 (기본)
vis search "TDD" --search-method semantic     # 의미적 검색
vis search "TDD" --search-method keyword      # 키워드 검색
vis search "TDD" --search-method colbert      # ColBERT 토큰 검색
vis search "TDD" --rerank                     # Cross-encoder 재순위화 (최고 품질)
vis search "TDD" --rerank --expand            # 재순위화 + 쿼리 확장 (최대 포괄)

# 관련 문서 찾기
vis related "문서명.md" --top-k 10

# 자동 태깅
vis tag "문서명.md"
vis tag "폴더명/" --recursive

# MOC(Map of Content) 생성
vis generate-moc "TDD" --top-k 50

# 주제별 문서 수집
vis collect "TDD" --output collection.md

# 주제별 문서 연결 (MOC + 관련 문서 링크 삽입)
vis connect-topic "TDD" --dry-run    # 미리보기
vis connect-topic "TDD"              # 실행
```

### 검색 옵션

```bash
# 결과 수 및 임계값 조정
vis search "TDD" --top-k 20 --threshold 0.5

# 쿼리 확장 (동의어 + HyDE)
vis search "TDD" --expand                    # 동의어 + HyDE
vis search "TDD" --expand --no-hyde          # 동의어만
vis search "TDD" --expand --no-synonyms      # HyDE만

# 중심성 점수 반영
vis search "TDD" --with-centrality

# 결과 파일로 저장
vis search "TDD" --output results.md
```

### 분석 도구

```bash
# 지식 공백 분석
vis analyze-gaps --top-k 20

# 태그 분석
vis list-tags

# 연결 상태 확인
vis connect-status

# 고립 태그 정리
vis clean-tags --dry-run
vis clean-tags

# 인덱스 관리
vis reindex                    # 증분 재인덱싱
vis reindex --with-colbert     # ColBERT 포함
vis reindex --force            # 강제 전체 재인덱싱
```

## Architecture

![img.png](attachments/search-pipeline.png)

### Module Structure

![img.png](attachments/module-diagram.png)

## 시스템 요구사항

- Python 3.11+
- 8GB+ RAM (대용량 vault의 경우)
- Apple Silicon (M1/M2) 권장 또는 CUDA GPU
- 1GB+ 디스크 (모델 캐시)

## 문서

- [5분 빠른 시작](docs/QUICK_START.md) — 설치부터 첫 검색까지
- [사용자 가이드](docs/USER_GUIDE.md) — 전체 기능 매뉴얼
- [실전 예제](docs/EXAMPLES.md) — 상황별 활용 사례
- [문제 해결](docs/TROUBLESHOOTING.md) — FAQ 및 디버깅
- [개발자 가이드](CLAUDE.md) — CLI 참조, API, 아키텍처 상세
- [기여 가이드](CONTRIBUTING.md) — PR 프로세스, 코딩 표준
- [변경 이력](CHANGELOG.md) — 버전별 변경사항

## License

[PolyForm Noncommercial License 1.0.0](LICENSE) — 비영리 목적 자유 사용, 영리 목적 별도 문의.
