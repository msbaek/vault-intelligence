# ColBERT 검색 제거 설계

- 작성일: 2026-08-13
- 상태: 승인됨 (구현 계획 대기)
- 계기: 2026-08-13 `vis reindex --with-colbert` 메모리 폭주로 시스템 스왑 고갈

## 1. 배경 — 무슨 일이 있었나

2026-08-13 01:14 launchd 야간 작업(`com.msbaek.vis-reindex`)이 시작한
`vis reindex --with-colbert`가 12시간 45분간 실행되며 `phys_footprint` 73 GB까지
단조 증가해, 시스템 스왑 77.8 GB 중 76.7 GB를 소진했다. macOS가
"run out of application memory" 경고를 띄웠고 `kill -TERM`으로 종료했다.

관측상의 함정: 이 프로세스의 **RSS는 190 MB**였다. `ps`의 RSS만 보면 놓친다.
`footprint -p <pid>`의 `phys_footprint`를 봐야 73 GB가 드러난다. 대부분이 이미
압축·스왑으로 밀려나 있었기 때문이다.

## 2. 원인 — 누수가 아니라 전량 메모리 적재

`ColBERTSearchEngine.build_index()`(`src/features/colbert_search.py:186,221`)는
**캐시 히트 문서까지 전부** `self.colbert_embeddings` 리스트에 append 한다.
신규 14건뿐인 증분 실행에서도 4,381건 전량을 SQLite → RAM으로 끌어올린다.

실측:

```
cache/embeddings.db = 34,037 MB
  colbert_embeddings : 4,415건 / blob 합계 32,402 MB
                       평균 1,879 토큰 × 1024 dim × 4 byte(float32) = 문서당 7.7 MB
  embeddings (dense) : 4,438건 / 합계 17 MB
```

32.4 GB 원본 + 읽기 중 사본·단편화 = `phys_footprint` 73 GB. 장비 물리 메모리는
32 GiB이므로 적재 자체가 용량을 초과한다. 로그의 "1개 문서 인퍼런스 358초"(정상 수 초)는
그 스래싱의 증상이다. vault 성장이 임계를 넘기며 8/11 8시간 → 8/13 12h45m으로
소요가 폭증했다.

동일 원인이 데몬에도 있다. `AdvancedSearchEngine.colbert_search()`
(`advanced_search.py:839`)는 호출마다 `colbert_engine`을 **지역 변수로 새로 만들어**
34 GB를 다시 적재한다. 조사 시점 데몬(pid 66196)은 27 GB를 점유하고 있었고
`phys_footprint_peak`는 68 GB였다(두 번 겹친 흔적).

## 3. 결정 — 메모리 최적화가 아니라 기능 제거

메모리를 고치는 대안(후보 재순위화, 스트리밍 스캔)보다 제거를 택한 근거는 사용량이다.
데몬 로그 전체 기간 집계:

| 지표 | 값 |
|---|---|
| 전체 `/search` 요청 | 7,161건 |
| `search_method=colbert` | **3건 (0.04%)** |
| `search_method=hybrid` | 6,706건 (+ 미지정 137건) |
| `rerank=true` | 3,110건 |
| ColBERT 34 GB 적재 발생 | 5회 |

품질 축은 이미 **BGE Reranker V2-M3**(`--rerank`)가 담당하며 3,110회 사용되고 있다.
ColBERT는 0.04%의 사용률을 위해 디스크 32 GB와 사용 시마다 RAM 34 GB를 요구하고,
그 대가로 이번 OOM과 야간 인덱싱 시간의 사실상 전부를 소비했다.

**버린 대안**

- *후보 재순위화*(hybrid top-N의 ColBERT 벡터만 fetch): 메모리는 수십 MB로 해결되나
  32 GB 캐시와 야간 인덱싱 부하가 그대로 남는다. 0.04% 기능에 유지 비용이 과하다.
- *전체 스트리밍 스캔*: 정확도는 보존되나 쿼리당 32 GB 디스크 읽기로 수십 초~분.
- *유지 + launchd 메모리 한도*: 증상만 가린다. 인덱싱이 실패로 끝날 뿐 문제는 남는다.

## 4. 설계

### 4.1 코드 제거 범위

| 대상 | 조치 |
|---|---|
| `src/features/colbert_search.py` (496줄) | 삭제 |
| `src/features/advanced_search.py:815-874` | `colbert_search()` 삭제, `search_method == "colbert"` 분기 6곳 제거 |
| `src/__main__.py` | `--with-colbert`·`--colbert-only` 인자, `run_reindex`의 ColBERT 블록(809-859), ColBERT 통계 블록(872-882) 제거 |
| `src/server.py`, `src/client.py` | `search_method` 허용값에서 `colbert` 제거 |
| `src/core/embedding_cache.py` | `colbert_embeddings` 테이블 생성·조회·저장·통계 메서드 제거 |
| `config/settings.yaml` | `colbert:` 섹션, `caching.enable_colbert` 제거 |
| `test_colbert.py`, `tests/test_server.py` | 삭제·갱신 |
| `reindex.sh` | `--with-colbert` 제거 |
| `CLAUDE.md`, `README.md`, `docs/USER_GUIDE.md` 외 | 검색 방법 표에서 colbert 행 제거 |

**폴백 정책**: `--search-method colbert` 지정 시 즉시 에러가 아니라
**경고 1줄 출력 후 hybrid로 폴백**한다. 외부 스킬 문서가 아직 colbert를 부를 수 있고,
조용한 성공으로 감추면 호출 경로를 영영 못 찾기 때문이다.

### 4.2 캐시 DB 처리

`DROP TABLE` + `VACUUM`은 34 GB 임시 공간과 수십 분을 요구한다. 대신:

1. 새 DB에 `embeddings` 테이블 스키마 생성
2. dense 4,438건(17 MB) 복사
3. 원본을 새 DB로 교체, 원본 삭제 (**백업 보관하지 않음** — 결정)

수초에 끝나며, 실패해도 원본이 그대로 남는다. 디스크 32 GB를 즉시 회수한다.

### 4.3 야간 job

`scripts/vis-nightly-reindex.sh`에서 `--with-colbert` 제거, "ColBERT 저장실패(경합)"
카운터와 Slack 항목 제거. 예상 소요 12시간 → **dense만 약 90분**.

`fit_documents`가 SQLite 캐시를 존중하지 않아 매 실행 전체 재인코딩하는 별건의 성능 문제
(`sentence_transformer_engine.py:151`)는 이번 범위 밖이며 그대로 남는다.

launchd 작업은 현재 unload 상태다. 검증 완료 후 재 load 한다.

### 4.4 외부 스킬 문서 (claude-config 레포)

colbert 권장문이 남아 있으면 에이전트가 계속 호출한다. 별도 레포이므로 커밋도 분리한다.

- `~/.claude/skills/vis/SKILL.md`, `README.md`, `references/cli-reference.md`
- `~/.claude/skills/vis-search-strategy/SKILL.md`
- `~/.claude/skills/vis-orchestra/SKILL.md`

## 5. 승인 조건 (acceptance criteria)

1. `vis search "TDD" --rerank` 정상 동작, 결과 개수·점수 이상 없음
   ✅ 실측: 5개 결과 정상 반환, 에러 없음 (2026-08-13)
2. `vis search "TDD" --search-method colbert` → 경고 1줄 + hybrid 결과 반환 (에러 아님)
   ✅ 실측: 경고 로그 출력 후 hybrid 결과 정상 반환, exit 0 (2026-08-13)
3. `vis reindex` 완료 후 검색 50회를 돌려도 데몬 `phys_footprint` **8 GB 미만** 유지
   (기존 27 GB / peak 68 GB). 기준선 실측: ColBERT를 한 번도 부르지 않은 신규 데몬이
   6,445 MB — 대부분 BGE-M3 모델과 reranker이며 dense 인덱스는 17 MB에 불과하다.
   따라서 "0에 가깝게"가 아니라 "기준선에서 자라지 않음"이 판정 기준이다.
   ✅ 실측: ~65회 누적 검색 후 phys_footprint 5,926~5,933 MB (peak 7,138 MB) 유지 (2026-08-13)
4. `cache/embeddings.db` **100 MB 미만** (기존 34,037 MB)
   ✅ 실측: 21 MB (dense 4,438건, 원본과 row count 일치·integrity_check ok 확인 후 교체) (2026-08-13)
5. `launchctl start com.msbaek.vis-reindex` 실행 성공 — foreground 테스트가 아니라
   **실제 launchd 경로**로 검증 (2026-07-08 cwd=`/` 버그 교훈)
   ⚠️ 부분 통과: 실제 launchd 경로 시작은 확인됨(cwd 버그 재발 없음, `vis reindex`가
   `--with-colbert` 없이 정상 호출됨). 완주는 확인 못함 — §8의 새 dense 임베딩 메모리
   문제로 2h23m 지점에서 의도적으로 종료(kill -TERM). ColBERT/cwd 회귀가 원인이 아님.
6. 레포 전체에 `colbert` 잔존 참조 없음 (archive·private 등 과거 기록 문서 제외)
   ✅ 실측: 남은 6개 파일 매치 전부 의도적(정규화 코드·테스트명·역사 기록·무관한
   라이브러리 파라미터명) — 상세는 SDD 진행 로그 참조 (2026-08-13)

## 6. 되돌리기

코드는 `git revert`로 즉시 복구된다. 인덱스는 재생성 가능하지만
**ColBERT 재인덱싱에 약 12시간**이 든다. 이것이 유일한 비가역 비용이며,
백업을 남기지 않기로 한 결정에 이 비용이 포함된다.

## 7. 이번 범위 밖 (별건으로 남는 것)

- `~/.vis-server.pid` 유실 시 `visd stop`이 프로세스를 못 찾고 `visd restart`가
  조용히 no-op가 되는 버그 — 이번 조치 중 실제로 발생
- `fit_documents`의 캐시 미존중으로 인한 dense 전체 재인코딩 (4.3 참조)

## 8. 검증 중 새로 발견한 인시던트 (이번 plan 범위 밖)

구현 완료 후 실제 launchd 경로로 재인덱싱을 검증하던 중(§5 AC5), ColBERT를 전혀
호출하지 않는 dense 전용 코드에서 **별개의 메모리 문제**를 발견했다. `vis reindex`
프로세스가 2h23m 실행 후 `phys_footprint` 42-48 GB, 시스템 스왑 여유 807 MB까지
도달 — 이번 사고와 같은 신호(낮은 RSS, 거대한 footprint)였다. `kill -TERM`으로
즉시 종료해 스왑을 회복시켰다.

핵심 확인: 이 문제는 이번 plan이 고친 것(검색·데몬 경로의 ColBERT 캐시 적재)과는
무관하다 — 종료 후 데몬은 정상(5.9 GB, 검색 정상)이었고, 로그의 유일한 "colbert"
문자열은 BGE-M3 모델이 원래 다기능 가중치를 로딩할 때 찍는 무해한 메시지였다.

원인 가설(미확정): `sentence_transformer_engine.py:186`의 `self.model.encode()`
반복 호출 사이에 `torch.mps.empty_cache()` 호출이 없다 — Apple Silicon PyTorch
MPS 백엔드가 반복 추론 사이 메모리를 해제하지 않는 알려진 패턴과 신호가 일치한다.
확정되지 않았으므로 이번 plan에서 성급히 고치지 않고 별도 `brainstorming`
세션으로 넘긴다(사용자 결정, 2026-08-13).

임시 조치: 근본 원인 해결 전까지 오늘 밤 재발을 막기 위해
`launchctl unload ~/Library/LaunchAgents/com.msbaek.vis-reindex.plist`로 야간
job을 다시 정지했다(사용자 결정) — Task 6이 만든 코드 자체는 정상이며, 이 정지는
새 인시던트에 대한 임시 조치일 뿐 Task 6의 결함이 아니다.
