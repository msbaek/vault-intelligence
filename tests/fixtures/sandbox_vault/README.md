# Sandbox Vault Fixture

vis-backlink reverse update 훅 검증용 미니 vault. `scripts/sync-sandbox.sh` 로 `/tmp/vault-test/` 에 복사된다.

## 파일 카탈로그

| 경로 | 역할 | Related Notes 섹션 | 일탈 케이스 |
|---|---|---|---|
| `003-RESOURCES/foo.md` | 정상 A 후보 | 있음 (2 links) | — |
| `003-RESOURCES/bar.md` | 정상 B 후보 | 있음 (3 links) | — |
| `003-RESOURCES/baz.md` | 정상 C 후보 | 있음 (1 link) | — |
| `003-RESOURCES/deviant-multiline.md` | 파서 skip 대상 | 있음 (multi-line desc) | multi-line description |
| `003-RESOURCES/deviant-image.md` | 필터 대상 | 있음 | `![[diagram.png]]` 링크 포함 |
| `003-RESOURCES/no-section.md` | bootstrap 대상 | 없음 | — |
| `997-BOOKS/quux.md` | 정상 후보 | 없음 | — |
| `work-log/2026-04-14.md` | 자동 제외 대상 | 없음 | `work-log/**` |
| `ATTACHMENTS/dummy-image.md` | 자동 제외 대상 | 없음 | `ATTACHMENTS/**` |
| `001-INBOX/.gitkeep` | A 생성 위치 | — | — |

## 재생성

```bash
./scripts/sync-sandbox.sh          # /tmp/vault-test/ 재생성 (rm -rf 후 cp)
./scripts/start-test-vis.sh        # test daemon 실행 (port 8742)
```
