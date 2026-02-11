# CLI Help 개선 설계: argparse subparsers 전환

## 목표

`vis` CLI의 help 시스템을 개선하여:
- `vis --help` → 커맨드 목록 + 간단한 설명
- `vis <command> --help` → 해당 커맨드 전용 옵션만 표시
- 필수 인자를 positional argument로 전환하여 타이핑 감소

## 현재 문제

- 단일 parser에 모든 옵션(40+개)이 flat하게 추가됨
- 어떤 옵션이 어떤 커맨드에 속하는지 구분 불가
- `vis search --help` 불가
- 필수 인자도 `--query`, `--topic` 등 옵션 형태

## 구현 계획

### Step 1: parser 구성 리팩토링 (1745~2037행)

부모 parser + subparsers 구조로 전면 재작성:

```python
def main():
    parser = argparse.ArgumentParser(
        prog="vis",
        description="Vault Intelligence System - Sentence Transformers 기반 지능형 검색 시스템"
    )

    # 공통 옵션
    parser.add_argument("--data-dir", help="데이터 디렉토리 경로")
    parser.add_argument("--vault-path", help="Vault 경로")
    parser.add_argument("--config", help="설정 파일 경로")
    parser.add_argument("--verbose", action="store_true", help="상세 로그 출력")

    subparsers = parser.add_subparsers(dest="command", title="commands")

    # 각 커맨드별 subparser + 전용 옵션
```

### Step 2: 커맨드별 subparser 정의

| 커맨드 | positional | 전용 옵션 |
|--------|-----------|----------|
| `search` | `query` | `--top-k`, `--threshold`, `--rerank`, `--search-method`, `--expand`, `--no-synonyms`, `--no-hyde`, `--with-centrality`, `--centrality-weight`, `--sample-size`, `--output` |
| `related` | `file` | `--top-k`, `--similarity-threshold` |
| `collect` | `topic` | `--top-k`, `--threshold`, `--output`, `--expand`, `--no-synonyms`, `--no-hyde` |
| `analyze` | (없음) | `--output` |
| `analyze-gaps` | (없음) | `--top-k`, `--output`, `--similarity-threshold`, `--min-connections` |
| `reindex` | (없음) | `--force`, `--sample-size`, `--include-folders`, `--exclude-folders`, `--with-colbert`, `--colbert-only` |
| `tag` | `target` | `--recursive`, `--dry-run`, `--tag-force`, `--batch-size` |
| `clean-tags` | (없음) | `--dry-run`, `--top-k` |
| `generate-moc` | `topic` | `--top-k`, `--threshold`, `--output`, `--include-orphans`, `--expand` |
| `summarize` | (없음) | `--topic`, `--clusters`, `--algorithm`, `--since`, `--max-docs`, `--output`, `--sample-size` |
| `review` | (없음) | `--period`, `--from`/`--to`, `--topic`, `--output` |
| `add-related-docs` | `file`(nargs='?') | `--batch`, `--pattern`, `--top-k`, `--threshold`, `--update-existing`, `--no-update-existing`, `--backup`, `--dry-run`, `--format-style` |
| `init` | (없음) | (없음) |
| `test` | (없음) | (없음) |
| `info` | (없음) | (없음) |

### Step 3: 디스패치 영역 최소 수정 (2062~2396행)

- 필수값 검증 로직 제거 (`if not args.query:` 등) → argparse가 자동 처리
- `tag` 커맨드의 `args.query` fallback 로직 제거
- 나머지 `args.*` 접근은 이름이 동일하므로 변경 없음

### Step 4: 검증

- `vis --help` → 커맨드 목록 확인
- `vis search --help` → search 전용 옵션 확인
- `vis search "TDD"` → 기존 기능 동작 확인
- `vis tag "문서.md"` → positional 동작 확인
- 모든 커맨드 help 확인

## 변경하지 않는 것

- 각 `run_*` 함수들 (인터페이스 동일)
- import, config, 초기화 로직
- 커맨드 실행 결과 출력 형태

## 특이사항

- `add-related-docs`의 `file`은 `nargs='?'` (배치 모드에서는 불필요)
- `summarize`, `review`는 positional 없음 (모든 인자가 optional)
