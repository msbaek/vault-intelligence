# dense 재인덱싱 메모리 — 조사 결과와 재개 지점

- 작성일: 2026-08-14
- 상태: 1차 수정 완료·병합됨 / 구조 개선은 보류 (2026-08-16 일요일 전체 재인덱싱 결과 확인 후 판단)
- 계기: 2026-08-13 `vis reindex`가 2h23m 실행 후 `phys_footprint` 42-48GB, 스왑 여유 807MB까지 도달
- 선행 문서: [2026-08-13-colbert-removal-design.md](2026-08-13-colbert-removal-design.md) §8 — 이 문제가 처음 관측된 기록

## 1. 확정된 원인 — PyTorch MPS 할당자 캐시

누수가 아니라 캐시다. 재현 실험에서 실사용(`torch.mps.current_allocated_memory`)은
전 구간 **2,170MB로 고정**인 반면, 할당자 보유(`torch.mps.driver_allocated_memory`)만
청크당 +2.3GB씩 늘었다.

원인은 FlagEmbedding의 `M3Embedder.encode_single_device`가 **청크마다 문서를 길이순으로
정렬**하는 데 있다. 배치 텐서 shape이 매번 달라지므로 shape별 캐시 블록이 계속 새로
생기고, 반환되지 않는다.

### 실측 — 50문서 청크, `_generate_dense_embeddings` 재현

| 청크 | baseline footprint | `empty_cache` 적용 |
|---|---|---|
| 1 | 6,111 MB | 6,260 MB |
| 2 | 8,457 MB (+2,346) | 6,418 MB (+158) |
| 3 | — | 6,563 MB (+145) |
| 4 | — | 7,307 MB (+744) |
| 5 | — | 7,532 MB (+225) |
| 6 | — | **5,841 MB (−1,691)** |

`empty_cache` 적용 시 4-6GB 대역에서 진동만 하고 누적되지 않는다. 4번째 청크의
+744MB 계단은 누적이 아니라 일시적 피크였다 — 5번째에서 `mps_driver`가
6,278→4,146MB로 되돌아왔다.

## 2. 적용한 수정 (main에 병합됨)

| 커밋 | 위치 | 내용 |
|---|---|---|
| `7dca2c9` | `sentence_transformer_engine.py:208` | 청크 임베딩 루프 끝에 `torch.mps.empty_cache()` |
| `bac59d0` | `advanced_search.py:272` | 인덱스 구축 루프에 50문서 주기 `empty_cache` |

`encode_text()` 안이 아니라 호출부 루프에 둔 이유: `encode_text`는 `advanced_search.py:436`
검색 쿼리 임베딩에도 쓰인다. 거기 넣으면 매 검색이 GPU 동기화 비용을 문다.

### 효과

| | 수정 전 | 수정 후 |
|---|---|---|
| 1단계 임베딩 | 42-48GB 단조 증가 → OOM | 15-18GB 진동 |
| 2단계 인덱스 구축 | 25 → 32.6GB 상승 | 격리 계측상 350문서 순증가 0 |
| 스왑 | 77.8GB로 확장 후 고갈 | 확장 없음 |
| 야간 증분 실행 | 12h45m 후 강제 종료 | **73분 정상 완주** (2026-08-14 01:00) |

## 3. 남은 문제 — 임베딩을 두 번 만든다

`build_index()`(`advanced_search.py:131`)가 같은 문서를 두 번 인코딩한다.

```
build_index()
 ├─ 143행  process_all_files()          문서 4,485개 읽기      →  0.06 GB
 ├─ 159행  engine.fit_documents()       ★1단계: 전체 임베딩
 │           └ _generate_dense_embeddings()  200문서×22청크    →  15~18 GB 대역
 │           └ _build_bm25_index()                             →  0.7 GB
 │         ...아무것도 해제하지 않음...
 └─ 203행  for i, doc in enumerate(self.documents):  ★2단계
              encode_text(doc.content)   같은 문서를 또 인코딩  →  +4 GB
              4,485회 호출
```

1단계가 만든 `engine.dense_embeddings`를 2단계가 쓰지 않고 처음부터 다시 만든다.

**재사용 코드는 이미 있다.** 샘플링 모드(`163~196행`)는 1단계 결과를 그대로 쓴다:

```python
# advanced_search.py:178-179 — 샘플링 경로
doc.embedding = self.engine.dense_embeddings[i]
embeddings_list.append(self.engine.dense_embeddings[i])
```

전체 모드(`198행` 이하)만 이걸 안 하고 재인코딩한다. 없는 기능을 만드는 게 아니라
전체 경로에도 같은 재사용을 적용하는 일이다.

### 20GB대의 정체 — 측정으로 확인

Python 데이터 구조는 원인이 아니다. 실측:

| 항목 | 실측 |
|---|---|
| `tokenized_docs` (BM25 입력, 4,533,008 토큰) | 0.34 GB |
| `BM25Okapi` 모델 (`doc_freqs` 246MB + `idf` 77MB) | 0.32 GB |
| 원문 문자열 4,485개 | 0.06 GB |
| **합계** | **0.7 GB** |

2단계를 격리 실행하면 7.6GB인데 실제 실행은 19.4GB에서 시작한다. 차이 약 12GB는
**1단계가 남긴 MPS 할당자 캐시**다. `empty_cache()`는 사용 중이 아닌 블록만 반환하는데,
1단계는 청크당 200문서 × 최대 4,096토큰이라 순간 점유가 커서 할당자 유지 대역 자체가
15~18GB로 올라앉고, 1단계가 끝나도 그대로 남는다.

(어제 이 12GB를 `tokenized_docs` + 원문 이중 보관으로 설명했는데 틀렸다. 위 실측이 정정이다.)

### 고치면 얻는 것 (추정)

| | 지금 | 두 곳 수정 후 |
|---|---|---|
| 최대 footprint | 20GB대 | 5~8GB |
| 소요 시간 | 약 2시간 | 약 1시간 (2단계 제거) |
| 임베딩 생성 | 2회 | 1회 |

고칠 지점 둘: (a) 2단계가 1단계 결과를 재사용, (b) 1단계 청크 크기 200 → 50
(50문서 청크는 4-6GB 대역, 200문서는 15-18GB 대역).

### 위험 — 단순 삭제 금지

2단계는 임베딩 생성 외에 **SQLite 캐시 저장**과 `doc.embedding` 할당도 한다
(`advanced_search.py:224-245`). 그리고 1단계 `fit_documents`는 캐시를 전혀 보지 않고
무조건 전량 인코딩하는 반면 2단계는 캐시 히트를 확인한다 — 2026-08-14 증분 실행이
73분에 끝난 건 이 캐시 덕이다(`캐시 히트 4385개 / 신규 임베딩 0개`).

2단계를 그냥 지우면 증분 실행의 캐시 활용이 깨져 매번 전체 인코딩이 될 수 있다.
두 단계의 책임을 다시 나누는 설계가 필요하다.

## 4. 별건 — `device` 인자가 무시된다

`sentence_transformer_engine.py:80`이 `BGEM3FlagModel(device=...)`를 넘기는데, 설치된
FlagEmbedding의 인자명은 `devices`(복수)다. 이 값은 `**kwargs`로 삼켜져 무시되고,
장치는 라이브러리 자동선택 결과(`mps:0`)로 결정된다. 즉 `config/settings.yaml`의
`model.device` 설정이 아무 효과가 없다.

우연히 원하는 장치로 동작 중이라 급하지 않다. 교정 시 `'auto'` 값이 그대로 넘어가
동작이 바뀔 수 있으므로 검증이 따로 필요하다.

## 5. 재개 시 확인할 것 (2026-08-16 일요일 이후)

야간 job은 일요일에만 `--force`(전체)로 돈다. 2026-08-14 실행은 증분이었고 신규
임베딩이 0건이었으므로, **전체 재인덱싱 경로는 아직 완주로 검증되지 않았다.**

1. `cat ~/.claude/logs/vis-reindex/latest.txt` — 모드가 `full`인지, exit 0인지, 소요 시간
2. `sysctl -n vm.swapusage` + `ls -lt /System/Volumes/VM/swapfile*` — 01~03시 사이 생성된
   스왑 파일이 있으면 압박이 있었다는 뜻 (2026-08-14에는 없었다)
3. `log show --last 12h --predicate 'eventMessage CONTAINS "memory"'`에 jetsam /
   "run out of application memory" 가 있는지

판단 기준:
- **완주 + 스왑 확장 없음** → 3절 구조 개선은 급하지 않다. 성능(2시간 → 1시간) 목적으로만 검토.
- **실패 또는 스왑 확장** → 3절 구조 개선을 brainstorming부터 시작.

## 6. 재현 스크립트

세션 스크래치패드에 있었고 영구 보관하지 않았다. 필요하면 재작성한다.

- **1단계 재현**: vault 문서 N개를 읽어 `model.encode()`를 청크 단위로 반복 호출하며
  매 청크 후 `footprint -p <pid>` + `torch.mps.driver_allocated_memory()` +
  `torch.mps.current_allocated_memory()` 셋을 함께 기록. `--empty-cache` 플래그로
  청크 사이 `torch.mps.empty_cache()` 호출 여부를 가른다.
- **2단계 재현**: 같은 계측을 문서당 `model.encode([doc], batch_size=1)` 루프로.
  50문서 주기로 `empty_cache` 호출.
- 파라미터는 실제와 맞춘다: `batch_size=2`, `max_length=4096`, 청크 200(1단계).

계측 함정 둘:
- `ps`의 RSS는 무의미하다. 압축·스왑된 페이지가 빠져 인시던트 당시 RSS는 190MB였다.
  `footprint -p <pid>`의 `phys_footprint`를 봐야 한다.
- `footprint` 출력은 값에 따라 MB/GB 단위가 바뀐다. 숫자만 파싱하면 11GB를 11MB로 읽는다.
