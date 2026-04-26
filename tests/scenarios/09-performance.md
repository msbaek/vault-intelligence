# T3 — 성능 측정

## 지표

| 지표 | 목표 | 측정 방법 |
|---|---|---|
| Forward blocking | < 2초 | forward 시작~종료 timestamp |
| Backward 5 대상 완료 | < 90초 | dispatch~`phase=completed` |
| Polling 오버헤드 | < 5초 | polling 진입~해제 |
| vis `/search` 1회 | < 500ms | curl `-w '%{time_total}'` |
| 스킬 응답 | < 1초 | `/vis-backlink-status` 실행 시간 |

## 방법

샌드박스 3회 반복 측정 평균값 기록.

- [ ] 각 지표 3회 측정
- [ ] 평균값이 목표 이내
- [ ] 목표 초과 시 원인 분석 inline 기록

## vis daemon 응답 측정 (사전 확인)

```bash
# vis daemon이 실행 중인지 확인
curl -sf http://localhost:8741/health && echo "daemon OK"

# /search latency 측정 (실제 vault 기준)
time curl -s --get --data-urlencode "query=TDD" "http://localhost:8741/search?top_k=5&rerank=true" > /dev/null
```
