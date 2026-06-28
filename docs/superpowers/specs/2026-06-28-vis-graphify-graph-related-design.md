---
title: vis × graphify — `vis graph-related` walking skeleton (Tier 1)
date: 2026-06-28
status: approved
scope: graphify 개념 그래프(graph.json)를 정적 sidecar로 읽어 "개념 엣지 → 문서 관계" 투영 후 벡터 related와 A/B 비교하는 격리 명령 신설 + 측정
source: 001-INBOX/vis-graphify-개념-그래프-GraphRAG-확장-전략.md (조사 보고서)
---

# vis × graphify — `vis graph-related` Walking Skeleton Design

> **작업 home**: `~/git/vault-intelligence` repo.
> 최종 산출물 설치 위치:
> - `src/features/graph_related.py` (신설 — GraphIndex 로드 + 엣지 필터 + 개념→문서 투영 + 비교)
> - `src/__main__.py` (수정 — `graph-related` subcommand 등록)
> - `tests/test_graph_related.py` (신설 — unit + integration)
> - `cache/graph/ddd/graph.json` (gitignored — graphify 오프라인 산출물, 코드 아님)
> - `config/settings.yaml` (수정 — `graph_related.confidence_threshold` 등 추가)
> - 기존 `advanced_search.py`·`related_docs_finder.py`·search/related 코드 경로는 **무변경**

## 1. Context & Motivation

### 1.1 배경

조사(`001-INBOX/vis-graphify-개념-그래프-GraphRAG-확장-전략.md`)에서 vis와 graphify의 핵심 차이를 **입자도(granularity)** 로 규명했다:

- **vis**: 노드 = 문서/태그/토픽 (`knowledge_graph.py` 의 `node_type: document|topic|tag`), 엣지 = 임베딩 유사도 / 공유 태그 / `[[링크]]`. → **문서 단위** 그래프. 빠른 로컬 벡터 검색이 정체성(visd 0.3초, BGE-M3, 무-LLM).
- **graphify**: 노드 = 문서에서 LLM 추출한 **개념**, 엣지 = `EXTRACTED/INFERRED/AMBIGUOUS` 감사추적 + 관계 타입. → **개념 단위** 그래프. 추출은 LLM-heavy(느림).

조사는 3-tier 통합 스펙트럼을 제시했고(Tier 1 보조 인덱스 / Tier 2 멀티홉 / Tier 3 GraphRAG hot-path), 가장 싸고 가역적인 Tier 1의 가장 작은 슬라이스를 walking skeleton으로 먼저 검증할 것을 권고했다.

### 1.2 핵심 통찰

- **벡터 검색의 사각지대**: "구조적으로 연결됐지만 의미적으로 안 닮은" 문서를 놓친다. 개념 그래프 엣지는 이런 cross-cutting 연결을 잡을 수 있다 — 이것이 검증할 가설이다.
- **단일 제약이 설계를 지배한다**: 통합 아이디어의 합격선은 "명령(query) 시점에 LLM 작업을 추가하는가?" 추가하면 vis 정체성이 깨진다. → LLM 개념 추출은 **오프라인**, 빠른 경로는 정적 graph.json을 **읽기만** 한다.
- **vis = graphify의 source-document 레이어**: graphify 노드는 `source_file`을 들고 있고, vis는 그 문서 본문·임베딩·`get` body fetch를 이미 가진다. 개념 그래프를 문서 관계로 투영하기에 최적의 위치.

## 2. Goal

graphify가 오프라인으로 만든 개념 그래프(`graph.json`)를 정적 sidecar로 읽어, 대상 문서의 개념 엣지를 문서 관계로 투영하고, 기존 벡터 기반 `related`와 나란히 비교해 "벡터가 놓친 신규 이웃"을 드러내는 **격리 명령 `vis graph-related`** 를 신설한다. 동시에 이 가설("개념 엣지가 벡터가 놓친 관련 문서를 잡는가")을 측정한다.

**성공 기준 (Definition of Done, testable)**:

1. `/graphify 003-RESOURCES/DDD` 가 `graph.json` 을 생성한다(오프라인 빌드 동작 확인).
2. `vis graph-related <DDD 문서>` 가 실제 문서에 대해 vector/graph/novel **3블록**을 출력하며, **명령 시점에 LLM 호출이 없다**.
3. 엣지 정책(`EXTRACTED` OR `INFERRED ≥ threshold`, `AMBIGUOUS` 제외)이 정확히 적용된다(unit test 통과).
4. `vis graph-related --sample 8 --output worksheet.md` 가 판정 워크시트(markdown)를 생성한다.
5. 사용자 판정 완료 후 "graph가 벡터(top-k)가 놓친 '진짜 관련' 문서를 8개 표본에서 N개 건졌다"를 정량 진술할 수 있다 → Tier 2/3 투자 결정 근거.

## 3. Constraints (non-negotiable)

- **명령 시점 무-LLM**: `graph-related` 실행 경로는 graph.json 읽기 + networkx 트래버설 + 기존 벡터 검색 재사용만. LLM·subagent 호출 금지.
- **기존 코드 경로 무변경**: `advanced_search.py`, `related_docs_finder.py`, `vis search`, `vis related` 의 동작을 바꾸지 않는다.
- **완전 가역**: 신규 파일 삭제 + subcommand 등록 제거 = 완전 롤백. graph.json은 gitignored cache.
- **벡터 베이스라인 재사용**: 벡터 related는 기존 `RelatedDocsFinder` 를 호출한다. 재구현 금지.

## 4. Non-Goals (YAGNI 범위 가드)

- **multi-hop 트래버설** — skeleton은 1-hop만. (Tier 2 후보)
- **HTTP 엔드포인트·daemon 통합** — CLI 전용.
- **`vis graph-build` 명령** — graphify 빌드는 수동(`/graphify` 직접 실행).
- **`vis related` 로의 병합** — 격리 명령 유지(production 통합은 측정 이후 결정).
- **증분 업데이트(`--update`) 처리** — 1회 빌드로 충분.
- **DDD 외 corpus 확장** — 측정 후 결정.

## 5. Architecture

graphify가 **오프라인**으로 DDD corpus의 개념 그래프를 만들고 → vis가 명령 시점에 그것을 **읽기만** 하여 개념 엣지를 문서 관계로 투영하고 → 기존 벡터 기반 `related`와 **나란히 비교**해 "벡터가 놓친 신규 이웃"을 드러낸다.

```
[오프라인 1회]  /graphify 003-RESOURCES/DDD  →  graph.json  →  cache/graph/ddd/graph.json (gitignored)
                                                    │
[명령 시점]  vis graph-related <doc>                │
   ├─ A. GraphIndex.load()  ───── graph.json 로드(networkx) + 엣지 정책 필터
   ├─ B. project(D)  ──────────── 개념→문서 투영 + 랭킹  →  [graph 관련문서]
   ├─ C. RelatedDocsFinder(D) ─── 기존 벡터 검색 재사용  →  [vector 관련문서]
   └─ D. compare()  ───────────── novelty(graph − vector top-k)  →  A/B + 신규이웃 출력
```

## 6. Components

모든 신규 로직은 `src/features/graph_related.py` 한 파일에 모은다(단일 책임, 격리).

- **A. GraphIndex**: `graph.json` 을 networkx 그래프로 로드. 엣지 필터 = `confidence == "EXTRACTED"` OR (`confidence == "INFERRED"` AND `confidence_score >= threshold`). threshold 기본 0.8, `config['graph_related']['confidence_threshold']` 로 튜닝. `AMBIGUOUS` 제외.
- **B. project(D)**: 개념→문서 투영(§7).
- **C. 벡터 베이스라인**: 기존 `RelatedDocsFinder.find_related_docs(D)` 호출(재사용).
- **D. compare()**: novelty 계산 + 출력 포맷팅(§8).
- **CLI**: `vis graph-related <doc>` (단일 A/B 뷰), `vis graph-related --sample N --output <md>` (워크시트). `__main__.py` 에 subcommand 등록.

## 7. 개념→문서 투영 알고리즘 (skeleton의 핵심)

대상 문서 `D` 에 대해:

1. **seed 개념** = `source_file == D` 인 노드들
2. 각 seed의 **1-hop 이웃**(필터 통과 엣지만)
3. 이웃 개념 → 그 `source_file` 문서로 **역매핑** (D 자신 제외)
4. 후보 문서 점수 = (D의 개념 ↔ 그 문서의 개념을 잇는 엣지들의 `weight × confidence_score`) 합산, 문서별 집계
5. 점수순 top-k 반환 + **기여한 엣지/개념**도 함께(audit·설명용)

**주의(실제 함정 — 반드시 처리)**: graphify의 `source_file` 은 graphify 입력 디렉토리 기준 상대경로(예: `Aggregate.md` 또는 `DDD/Aggregate.md`), vis는 vault 기준 상대경로(예: `003-RESOURCES/DDD/Aggregate.md`). → **경로 정규화로 문서 정체성을 일치**시켜야 후보 매칭이 동작한다. 정규화 규칙(공통 prefix 부착/제거)을 별도 함수로 분리하고 unit test로 고정한다.

## 8. 측정 (신규이웃 + 전문가 판정)

- **단일 문서 모드**: vector top-k · graph top-k · **NOVEL**(graph엔 있고 vector top-k엔 없는 이웃) 3블록 출력. NOVEL이 판정 대상.
- **표본 모드** (`--sample 8 --output worksheet.md`): 표본 N개 문서의 모든 novel 쌍을 모아 **판정 워크시트(markdown)** 생성 — 각 행: `대상문서 | 신규이웃 | 기여개념·엣지 | [판정칸]`.
- 사용자가 판정칸을 채움(관련/무관) → "N개 표본에서 graph가 벡터가 놓친 '진짜 관련' 문서를 M개 건짐" 집계.
- 표본 크기 기본 8. 표본 선택은 corpus 내 **결정적 추출**(경로 정렬 후 균등 stride 샘플 — 비결정적 난수 샘플링 금지, 재실행 시 동일 표본 재현).

## 9. Error Handling

- `graph.json` 없음 → 명확한 안내: "`/graphify 003-RESOURCES/DDD` 먼저 실행 후 `cache/graph/ddd/graph.json` 에 배치".
- 대상 문서가 corpus 밖(그래프에 해당 개념 없음) → "이 문서는 graph corpus에 없음" 안내, 빈 graph 블록.
- 경로 정규화 실패(매칭 불가 노드) → 경고 로그 후 skip(중단 아님).

## 10. Testing (TDD, test-first)

- **Unit — 엣지 필터**: EXTRACTED 유지 / INFERRED≥0.8 유지 / INFERRED<0.8 제거 / AMBIGUOUS 제거.
- **Unit — 투영**: 작은 합성 `graph.json` fixture(문서 2-3개, 알려진 엣지)로 기대 후보·점수 검증.
- **Unit — novelty**: graph 집합 − vector 집합 계산.
- **Unit — 경로 정규화**: graphify 상대 ↔ vault 상대 변환.
- **Integration**: 실제 DDD graph.json으로 문서 1개 E2E → 비어있지 않은 정상 출력.
- **Smoke**: 워크시트 생성.

## 11. Reversibility

신규 파일 `graph_related.py` + CLI subcommand + tests + config 키만 추가. 파일 삭제 + subcommand 등록 제거 + config 키 제거 = 완전 롤백. `graph.json` 은 gitignored cache. 기존 search/related 코드 경로 무변경.

## 12. Failure Conditions (이 중 하나라도면 skeleton 실패)

- 명령 경로에서 LLM/subagent가 호출된다(제약 위반).
- `vis search`/`vis related` 의 기존 동작이 바뀐다(회귀).
- 경로 정규화 미처리로 graph 블록이 항상 비어 측정이 불가능하다.
- 엣지 필터가 AMBIGUOUS를 포함하거나 INFERRED<threshold를 통과시킨다.
- 측정 워크시트가 novel 쌍의 기여 개념·엣지를 누락해 사용자가 판정 근거 없이 판단해야 한다.
- 표본 추출이 비결정적이어서 재실행 시 다른 표본이 나온다.
