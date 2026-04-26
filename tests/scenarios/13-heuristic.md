# T6.2/T6.3/T6.9 — 휴리스틱 평가기 시나리오

## 전제

- `scripts/sync-sandbox.sh` 실행으로 `/tmp/vault-test/` 최신화
- test vis daemon 실행: `bash scripts/start-test-vis.sh` (localhost:8742)
- `.disabled` 마커 없음 확인
- vis daemon 이 sandbox fixture 인덱싱 완료 상태

---

## T6.2 — Hard Veto S4 (자동 제외율 ≥60%)

### 전제 보충
Top 5 중 3건 이상이 `exclude_patterns` 매칭 필요. sandbox fixture 중 `work-log/**` 와 `ATTACHMENTS/**` 에 해당하는 문서들이 Top 5 에 오도록 A 의 내용을 조정하거나, 수동으로 "Top 5 중 4건이 제외 대상" 상황을 시뮬레이션한다.

### 실행
사용자 프롬프트:
> "`/tmp/vault-test/001-INBOX/veto-s4-test.md` 태그 붙이고 정리해줘.
> vis /search 결과가 work-log/**·ATTACHMENTS/** 위주로 나오는 상황을 가정."

### 검증
- [ ] SKILL.md Step 4 에서 vis /search 호출 → Top 5 분석
- [ ] S4 계산: 자동 제외 비율 ≥60% → hard veto 발화
- [ ] `⚠️ backward skip 추천 — 자동 제외율 XX% (Top 5 중 N건이 work-log/draft)` 메시지 출력
- [ ] 대상 후보 목록 (비제외 항목) 표시
- [ ] `강제 진행하시겠습니까? [y/N]` prompt 출력
- [ ] N/Enter 입력 시 `ℹ️ backward skip 확정 (사용자)` 출력 후 종료
- [ ] `~/.claude/state/vis-backlink/history/` 에 `phase: user_skipped` job JSON 생성
- [ ] soft signals (S1·S2·S3) 도 메시지에 포함됨

---

## T6.3 — Hard Veto S5 (frontmatter status: draft)

### 준비
A = `/tmp/vault-test/003-RESOURCES/draft-note.md` (이미 생성됨, frontmatter `status: draft`)

```bash
cat /tmp/vault-test/003-RESOURCES/draft-note.md | head -5
# 확인: status: draft 존재
```

### 실행
사용자 프롬프트:
> "`/tmp/vault-test/003-RESOURCES/draft-note.md` 태그 붙이고 정리해줘."

### 검증
- [ ] SKILL.md Step 5 에서 A 의 frontmatter `status: draft` 감지 → S5 hard veto 발화
- [ ] skip 추천 메시지 출력 (근거: S5 frontmatter draft)
- [ ] `[y/N]` prompt 출력
- [ ] `y` 입력 시 → proceed 경로로 fallthrough
- [ ] `🔗 backward dispatched` 메시지 (dispatched 확인)
- [ ] state JSON 에 `reason: user_override_skip` 기록됨

---

## T6.9 — 회귀: git uncommitted ≠ draft

### 목적
git 에 commit 되지 않은 파일이어도 frontmatter `draft` 없으면 S5 veto 발화 안 됨을 확인.

### 준비
```bash
# 새 파일 생성 (git add 안 함)
cat > /tmp/vault-test/001-INBOX/uncommitted-new.md << 'EOF'
---
title: Uncommitted New Note
tags: []
---

# Uncommitted New Note

git 에 아직 add/commit 되지 않은 파일. frontmatter 에 draft 필드 없음.
EOF

# vault git status 확인
cd /tmp/vault-test && git status --porcelain 001-INBOX/uncommitted-new.md
# 기대: ?? 001-INBOX/uncommitted-new.md (untracked)
```

### 실행
사용자 프롬프트:
> "`/tmp/vault-test/001-INBOX/uncommitted-new.md` 태그 붙이고 정리해줘."

### 검증
- [ ] SKILL.md Step 5 에서 A frontmatter 에 `status: draft` 와 `draft: true` 모두 없음 → S5 발화 안 함
- [ ] git uncommitted 상태 자체는 skip 사유가 아님
- [ ] S4 미발화 (Top 5 제외율 <60%) 전제 하에 recommendation = PROCEED
- [ ] `🔗 backward dispatched` 메시지 출력
- [ ] **핵심 검증**: uncommitted 파일이어도 backward 가 정상 발화됨 (ENV_DIRTY_TREE 가드 없음 확인)

---

## 수동 시뮬레이션 결과

### 2026-04-26 — 휴리스틱 평가기 구현 완료 (논리 검증)

- **T6.2 (S4 veto)**: Step 5 에서 자동 제외율 계산 → ≥60% 시 hard veto 발화 → skip 추천 + `[y/N]` prompt. ✅ 논리 검증 통과
- **T6.3 (S5 veto)**: Step 5 에서 A frontmatter `status: draft` 감지 → S5 발화 → skip 추천. `y` 입력 시 user_override_skip 으로 dispatch. ✅ 논리 검증 통과
- **T6.9 (uncommitted 비간주)**: git uncommitted 상태 무관, frontmatter draft 없으면 S5 미발화 → proceed 추천. ENV_DIRTY_TREE 가드 없음 확인. ✅ 논리 검증 통과

실제 Claude 세션에서 end-to-end 검증은 Task 9 E2E 시나리오에서 수행.
