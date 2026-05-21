# Obsidian OFM 규칙 SSOT 단일화 — Design

- **작성일**: 2026-05-21
- **상태**: 설계 승인됨, 구현 계획 대기
- **관련 워크플로우**: brainstorming → (이 문서) → writing-plans → executing-plans

## Goal (testable)

vis CLI와 obsidian agent가 생성하는 모든 vault 문서가 Obsidian Flavored
Markdown(OFM) 규칙을 준수한다. 구체적 검증 기준:

1. `vis collect` / `vis generate-moc` / `vis related` / `vis summarize` 출력의
   wikilink가 vault-relative 경로 형식이다 — `[[997-BOOKS/개발자로 살아남기]]`
   (절대경로 접두사·`.md` 확장자 없음).
2. vis가 생성하는 frontmatter의 timestamp 형식이 일관된다.
3. OFM 규약의 단일 출처(`ofm-rules.md`)가 존재하고, vis 코드와
   obsidian agent 양쪽이 이를 참조한다.
4. `youtube-obsidian-summarizer`의 `created_at` 문법 오류가 수정된다.

## Constraints (non-negotiable)

- **Plugin 파일 수정 금지**: `~/.claude/plugins/`의 `obsidian:obsidian-markdown`
  스킬은 reference로만 사용. SSOT는 `~/.claude/commands/obsidian/` 아래 둔다.
- **Wikilink는 vault-relative 경로 고정**: vis 출력 wikilink는 항상
  `[[folder/basename]]` (vault root 기준 상대경로, `.md` 없음). Obsidian
  `newLinkFormat: "shortest"`는 "유일 식별 최단경로"를 뜻하므로 1000+ 문서
  vault에서 basename 중복(`README`·`TDD` 등) 시 모호한 링크가 된다 →
  경로 고정으로 모호성 0. Obsidian display는 자동으로 basename만 표시한다.
  markdown 링크 아님 (`useMarkdownLinks: false`).
- **범위 비대칭**: vis Python 유틸은 vis가 실제 생성하는 것(wikilink·
  frontmatter)만 다룬다. callout/embed 함수는 만들지 않는다 (YAGNI).
- **런타임 파싱 금지**: Python 코드가 SSOT 마크다운을 런타임에 파싱하지
  않는다. 동기화는 단위테스트로 고정한다.

## Failure Conditions

- vis 출력 wikilink에 절대경로 접두사 또는 `.md` 확장자가 남아 있으면 실패.
- vis 출력 wikilink가 basename만 담아 모호한 링크가 되면 실패.
- SSOT 없이 규칙이 vis 코드와 agent에 각각 흩어져 있으면 실패.
- `ofm.py`에 vis가 생성하지 않는 OFM 요소(callout 등) 함수가 추가되면
  scope 위반.

## 배경: 문제의 본질

증상은 "wikilink 등 OFM 규칙 미준수"지만 근본 원인은 두 가지다:

1. **OFM 규칙의 SSOT 부재** — 규칙이 `shared-rules.md`(summarize 전용),
   각 agent, vis 코드에 흩어져 있다.
2. **소비자가 두 종류** — LLM(프롬프트를 읽음)과 Python 코드(프롬프트를
   못 읽음)가 따로 규칙을 따른다.

`shared-rules.md`는 첫 줄에 "summarize-article/summarize-youtube 공통
참조"라고 자기 범위를 명시한다 → vault 전체 OFM 규약의 SSOT가 될 수 없다.

### 현재 vis 출력의 비표준 사례

`collect-TDD_*.md` 실측:

```
[[/Users/msbaek/DocumentsLocal/msbaek_vault/997-BOOKS/개발자로 살아남기.md]]
```

절대경로 + `.md` 확장자. 표준은 `[[997-BOOKS/개발자로 살아남기]]`.

## 아키텍처

```
            ┌─────────────────────────────┐
            │  ofm-rules.md  (신규 SSOT)   │
            │  OFM 전체 규약 + vis 적용범위 │
            └──────────┬───────────┬──────┘
         텍스트로 참조  │           │  코드로 구현 (직접 못 읽음)
                       ▼           ▼
       경로 B: obsidian agents   경로 A: vis Python
       + shared-rules.md         src/utils/ofm.py
       (OFM 전체 적용)            (wikilink+frontmatter만)
```

- **경로 B (LLM 소비자)**: agent·skill이 `ofm-rules.md`를 텍스트 지침으로
  참조한다.
- **경로 A (코드 소비자)**: Python은 마크다운을 못 읽으므로 `ofm.py`
  유틸이 SSOT 규칙을 코드로 구현하고, docstring에 SSOT 경로를 인용 +
  단위테스트로 고정한다.

## 컴포넌트

### ① `~/.claude/commands/obsidian/ofm-rules.md` (신규 SSOT)

- OFM 전체 규약: wikilink `[[folder/basename]]`, frontmatter(properties),
  callout `> [!type]`, embed `![[...]]`, 태그, 헤딩, 블록 ID.
- **"vis 적용 범위" 표** 포함 — vis가 실제 생성하는 OFM 요소(wikilink·
  frontmatter)만 명시. Python ↔ SSOT 동기화의 기준점.
- **"일시 파일 면제" 범주 정의** — `*-progress.md`, WIP 산출물 등 임시
  파일은 frontmatter 의무에서 면제.

### ② vis Python: `src/utils/ofm.py` (신규 모듈)

- `to_wikilink(path, alias=None)` — 입력 `path`는 절대경로 또는
  vault-relative 경로. vault root 접두사와 `.md` 확장자를 제거해
  vault-relative 경로로 정규화 → `[[folder/basename]]` 또는
  `[[folder/basename|alias]]`. basename 추출·충돌 검사 로직 없음.
- frontmatter 직렬화 헬퍼 — timestamp 형식 통일.
- **범위 비대칭**: vis가 생성하지 않는 callout/embed 함수는 만들지 않음.
- 호출처 교체 (현재 wikilink/markdown을 emit하는 곳):
  - `features/topic_collector.py` `_export_as_markdown()` (L423 부근)
  - `features/moc_generator.py` `_format_as_markdown()` (L608/628/657/682/695)
  - `features/related_docs_finder.py` `format_related_section()` (L136 —
    현재 `doc.title` 사용 → `doc.path`로 전환)
  - `__main__.py` `save_clustering_results()` (L1256 — 현재 `doc.title` +
    대괄호 제거 hack으로 `[[title]]` emit → `doc.path` 기반
    `ofm.to_wikilink()`로 전환, hack 제거)
  - `features/topic_connector.py` `_write_progress_file()` (frontmatter 면제 확인)
- **검증 완료**: `save_learning_review()`와 `vis search --output`은 wikilink를
  emit하지 않아 변경 대상 아님. 향후 마크다운을 emit하는 신규 코드는 반드시
  `ofm.to_wikilink()`를 경유한다.

### ③ obsidian agents 통일

- 6개 agent + `shared-rules.md`에 `ofm-rules.md` 참조 추가:
  - `youtube-obsidian-summarizer`, `article-obsidian-summarizer`
  - `obsidian-forward-related-injector`, `obsidian-related-notes-injector`
  - `obsidian-file-organizer`, `obsidian-tagger`
- `youtube-obsidian-summarizer`의 `created_at: [[YYYY-MM-DD HH:mm]]`
  문법 오류 수정 → 평문 `created_at: YYYY-MM-DD HH:MM`.

## 데이터 흐름

- **vis collect / generate-moc / related / summarize**: 문서 path →
  `ofm.to_wikilink()` → vault-relative wikilink → 마크다운 출력.
- **agent 문서 생성**: agent가 `ofm-rules.md` 규칙을 읽고 OFM 전체를
  준수한 문서를 생성.

## 동기화 메커니즘

Python 코드와 SSOT가 어긋나지 않게 하는 장치:

- `ofm.py` docstring에 SSOT 경로 + 핵심 규칙(wikilink 형식)을 인용.
- `tests/test_ofm.py`가 변환 결과를 고정 — 절대경로→vault-relative 경로,
  `.md` 확장자 제거, alias 형식, 특수문자 처리.
- SSOT 마크다운을 런타임 파싱하지 **않음** (과결합 회피). SSOT의
  "vis 동작 예시" 표와 `test_ofm.py` 케이스를 사람이 일치하도록 관리.

**Accepted risk — cross-repo SSOT 위치**: SSOT(`ofm-rules.md`)는
user-global(`~/.claude/commands/obsidian/`)에, Python 코드는 repo
(`vault-intelligence/`)에 있다. 두 위치를 자동 동기화하는 트리거는 없다 —
SSOT 규칙이 바뀌면 `ofm.py`/`test_ofm.py`를 사람이 따라 고쳐야 한다.
규칙 변경 빈도가 낮아 수용 가능한 위험으로 본다.

## 에러 처리 / 엣지 케이스

- **특수문자**: 경로에 `[ ] | # ^`가 있으면 wikilink가 깨진다 →
  alias 형식으로 회피하거나 경고. (`997-BOOKS/개발자로 살아남기` 같은
  일반 경로는 문제 없음.)
- **`related_docs_finder` / `save_clustering_results`**: 현재 `doc.title`을
  wikilink 텍스트로 사용 → title에 특수문자가 있으면 깨지고 vault에서
  식별 불가 → `doc.path` 기반 vault-relative 경로로 전환.
- **basename 충돌**: vault-relative 경로 고정으로 원천 차단 — `to_wikilink`에
  충돌 검사 로직 불필요.
- **기존 WIP/ 출력물**: 소급 수정하지 않음. 새로 생성되는 문서부터 적용.

## 테스트 / 검증 한계

- **vis 측**: `tests/test_ofm.py` 단위테스트로 자동 검증.
  - `to_wikilink` — 절대경로 입력, 확장자 제거, alias, 특수문자.
- **agent 측**: LLM이 SSOT를 실제로 따르는지는 **자동 검증 불가**.
  - 정적 참조 존재 확인(agent 파일이 `ofm-rules.md`를 명시하는가) +
    생성 샘플 1~2건 수동 리뷰가 검증의 한계.

## 결정 기록

- **SSOT 위치**: `shared-rules.md`에 절 추가가 아닌 별도 `ofm-rules.md`
  신설. 이유 — `shared-rules.md`는 summarize 전용 책임을 가지며, vault
  전체 OFM 규약과 책임을 섞으면 단일 책임 위반.
- **범위 비대칭 채택**: vis 측 유틸을 OFM 전체로 만들지 않고 vis가 실제
  생성하는 것으로 한정. 이유 — 사용하지 않을 callout/embed 함수는
  유지보수 부담만 늘림(YAGNI).
- **런타임 파싱 배제**: SSOT-코드 동기화를 마크다운 파싱이 아닌
  단위테스트로 고정. 이유 — 마크다운 파싱은 SSOT 문서 형식에 코드가
  결합되어 깨지기 쉬움.
- **Wikilink는 vault-relative 경로 고정**: `[[basename]]`(Obsidian
  "shortest" 기본값 모방)이 아닌 `[[folder/basename]]`로 고정. 이유 —
  "shortest"는 "유일 식별 최단경로"이므로 1000+ 문서 vault에서 basename
  중복 시 모호한 링크가 생긴다. 경로 고정은 모호성 0 + 충돌 검사 로직
  불필요. Obsidian이 display에서 basename만 보여주므로 가독성 손실 없음.
  trade-off — 소스 텍스트가 길어짐(수용).
