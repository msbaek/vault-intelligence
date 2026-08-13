#!/bin/bash
# vis-nightly-reindex.sh — 야간 자동 증분/전체 재인덱싱 (launchd에서 매일 01:00 실행)
#
# 동작:
#   - 평일: `vis reindex`      (증분, 캐시 기반)
#   - 일요일: `vis reindex --force` (전체 재구축)
#   - reindex 성공 시 `visd restart` 로 데몬 인메모리 인덱스 갱신
#   - 실행 결과를 로그 + terminal-notifier 알림으로 보고
#
# 옵션(테스트용):
#   VIS_REINDEX_MODE=full|incremental   요일 판별 대신 모드 강제
#   --dry-run (또는 VIS_REINDEX_DRYRUN=1) reindex/restart 생략, 알림·요약만 검증
#
# launchd는 최소 PATH로 실행되므로 절대경로 + 명시적 PATH 사용.

set -uo pipefail

# --- 실행 파일 경로 (launchd 환경 대비) ---
export PATH="/Users/msbaek/.local/bin:/Users/msbaek/bin:/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin"
VIS="/Users/msbaek/.local/bin/vis"
VISD="/Users/msbaek/bin/visd"
NOTIFIER="/opt/homebrew/bin/terminal-notifier"
HEALTH_URL="http://localhost:8741/health"

LOG_DIR="$HOME/.claude/logs/vis-reindex"
LATEST="$LOG_DIR/latest.txt"
LOCK_DIR="$LOG_DIR/.lock"
mkdir -p "$LOG_DIR"

# Slack 자격증명 (git 미추적, 머신 로컬, chmod 600). 없으면 Slack 알림 skip.
#   SLACK_WEBHOOK_URL="https://hooks.slack.com/services/..."   (권장, 채널 게시)
#   또는 SLACK_BOT_TOKEN="xoxb-..." + SLACK_CHANNEL="U0..또는 #채널"  (DM/채널)
SLACK_CONF="$HOME/.config/vis-reindex/slack.conf"

ts() { date '+%Y-%m-%d %H:%M:%S'; }
STAMP="$(date '+%Y-%m-%d-%H%M')"
RUN_LOG="$LOG_DIR/$STAMP.log"

# --- dry-run 판별 ---
DRYRUN="${VIS_REINDEX_DRYRUN:-0}"
[[ "${1:-}" == "--dry-run" ]] && DRYRUN=1

# --- 모드 판별: 일요일(u=7) => 전체, 그 외 => 증분 ---
mode="${VIS_REINDEX_MODE:-}"
if [[ -z "$mode" ]]; then
  if [[ "$(date +%u)" == "7" ]]; then mode="full"; else mode="incremental"; fi
fi
if [[ "$mode" == "full" ]]; then FORCE_FLAG="--force"; else FORCE_FLAG=""; fi

# --- 알림 (terminal-notifier 우선, osascript fallback) ---
notify() {  # $1=title $2=message $3=sound(optional)
  local title="$1" msg="$2" sound="${3:-}"
  if [[ -x "$NOTIFIER" ]]; then
    if [[ -n "$sound" ]]; then
      "$NOTIFIER" -title "$title" -message "$msg" -sound "$sound" -group vis-reindex >/dev/null 2>&1
    else
      "$NOTIFIER" -title "$title" -message "$msg" -group vis-reindex >/dev/null 2>&1
    fi
  else
    /usr/bin/osascript -e "display notification \"$msg\" with title \"$title\"" >/dev/null 2>&1
  fi
}

# --- Slack 전송 (webhook 우선, 없으면 bot token) ---
notify_slack() {  # $1=제목줄 $2=본문(요약)
  [[ -f "$SLACK_CONF" ]] || return 0
  # shellcheck disable=SC1090
  source "$SLACK_CONF"
  local text
  text="$1"$'\n'"\`\`\`"$'\n'"$2"$'\n'"\`\`\`"
  if [[ -n "${SLACK_WEBHOOK_URL:-}" ]]; then
    curl -sf -X POST -H 'Content-type: application/json' \
      --data "$(jq -n --arg t "$text" '{text:$t}')" \
      "$SLACK_WEBHOOK_URL" >/dev/null 2>&1
  elif [[ -n "${SLACK_BOT_TOKEN:-}" && -n "${SLACK_CHANNEL:-}" ]]; then
    curl -sf -X POST https://slack.com/api/chat.postMessage \
      -H "Authorization: Bearer ${SLACK_BOT_TOKEN}" \
      -H 'Content-type: application/json; charset=utf-8' \
      --data "$(jq -n --arg c "$SLACK_CHANNEL" --arg t "$text" '{channel:$c,text:$t}')" \
      >/dev/null 2>&1
  fi
}

# --- 중복 실행 방지 lock (mkdir는 원자적) ---
# stale lock 대비: 이전 실행이 SIGKILL 등으로 죽으면 EXIT trap이 못 돌아 lock이 안 지워짐.
# → lock 안의 시작 시각이 STALE_SEC(기본 6시간, 실측 최장 full 실행 5.1h + 여유)보다 오래되면 stale로 간주하고 정리 후 진행.
STALE_SEC="${VIS_REINDEX_LOCK_STALE_SEC:-21600}"
if ! mkdir "$LOCK_DIR" 2>/dev/null; then
  lock_started=$(cat "$LOCK_DIR/started_at" 2>/dev/null || echo 0)
  lock_age=$(( $(date +%s) - lock_started ))
  if [[ "$lock_started" -gt 0 && "$lock_age" -gt "$STALE_SEC" ]]; then
    echo "[$(ts)] stale lock 감지 (${lock_age}s 경과, 임계값 ${STALE_SEC}s) — 정리 후 진행." | tee -a "$RUN_LOG"
    notify_slack "*vis reindex ⚠️ stale lock 정리*" "이전 실행이 비정상 종료된 것으로 보여 lock을 정리하고 진행합니다. (경과 ${lock_age}s)"
    rm -rf "$LOCK_DIR"
    if ! mkdir "$LOCK_DIR" 2>/dev/null; then
      echo "[$(ts)] stale lock 정리 후에도 획득 실패 — 이번 실행 건너뜀." | tee -a "$RUN_LOG"
      notify "vis reindex ⏭️ 건너뜀" "stale lock 정리 후에도 다른 인덱싱이 실행 중이라 건너뜁니다."
      notify_slack "*vis reindex ⏭️ 건너뜀*" "stale lock 정리 후에도 다른 인덱싱이 실행 중이라 건너뜁니다."
      exit 0
    fi
  else
    echo "[$(ts)] 다른 인덱싱이 실행 중 (lock: $LOCK_DIR, 경과 ${lock_age}s) — 이번 실행 건너뜀." | tee -a "$RUN_LOG"
    notify "vis reindex ⏭️ 건너뜀" "다른 인덱싱이 실행 중이라 건너뜁니다."
    notify_slack "*vis reindex ⏭️ 건너뜀*" "다른 인덱싱이 실행 중이라 건너뜁니다. (경과 ${lock_age}s)"
    exit 0
  fi
fi
date +%s > "$LOCK_DIR/started_at"
trap 'rmdir "$LOCK_DIR" 2>/dev/null || rm -rf "$LOCK_DIR" 2>/dev/null' EXIT

# --- 작업 디렉토리 고정 (launchd는 cwd=/ 로 실행 → vis의 상대경로 models/·cache/ 대비) ---
REPO_DIR="/Users/msbaek/git/vault-intelligence"
if ! cd "$REPO_DIR"; then
  echo "[$(ts)] ❌ repo 디렉토리 접근 불가: $REPO_DIR" | tee -a "$RUN_LOG"
  notify "vis reindex ⚠️ 실패" "repo 디렉토리 접근 불가: $REPO_DIR" "Basso"
  notify_slack "*vis reindex ⚠️ 실패*" "repo 디렉토리 접근 불가: $REPO_DIR"
  exit 1
fi

START=$(date +%s)
{
  echo "=================================================="
  echo "[$(ts)] vis-nightly-reindex 시작 (mode=$mode, dry_run=$DRYRUN)"
  echo "=================================================="
} | tee -a "$RUN_LOG"

# --- 1. 데몬 정지 (reindex와 동시 실행 시 BGE-M3 모델/인덱스 이중 로딩으로 OOM 발생 이력 있음) ---
if [[ "$DRYRUN" != "1" ]]; then
  echo "[$(ts)] visd stop (reindex 중 메모리 이중 사용 방지)..." >> "$RUN_LOG"
  "$VISD" stop >> "$RUN_LOG" 2>&1
fi

# --- 2. reindex ---
rc=0
if [[ "$DRYRUN" == "1" ]]; then
  echo "[$(ts)] (dry-run) vis reindex $FORCE_FLAG 생략" | tee -a "$RUN_LOG"
else
  echo "[$(ts)] vis reindex $FORCE_FLAG 실행..." >> "$RUN_LOG"
  "$VIS" reindex $FORCE_FLAG >> "$RUN_LOG" 2>&1
  rc=$?
  echo "[$(ts)] reindex 종료코드: $rc" >> "$RUN_LOG"
fi

# --- 3. 데몬 재시작 (reindex 성공/실패 무관 — 1단계에서 정지시켰으므로 항상 복구) ---
restart_ok="skip"
if [[ "$DRYRUN" != "1" ]]; then
  echo "[$(ts)] visd start..." >> "$RUN_LOG"
  if "$VISD" start >> "$RUN_LOG" 2>&1; then restart_ok="ok"; else restart_ok="fail"; fi
  # 인덱싱 완료(indexed=true) 대기 (최대 30s)
  for _ in $(seq 1 30); do
    h=$(curl -sf "$HEALTH_URL" 2>/dev/null)
    [[ -n "$h" && "$(echo "$h" | jq -r '.indexed // false' 2>/dev/null)" == "true" ]] && break
    sleep 1
  done
fi

# --- 3. 통계 수집 ---
docs="?"; indexed="?"
health=$(curl -sf "$HEALTH_URL" 2>/dev/null)
if [[ -n "$health" ]]; then
  docs=$(echo "$health" | jq -r '.document_count // "?"' 2>/dev/null)
  indexed=$(echo "$health" | jq -r '.indexed // "?"' 2>/dev/null)
fi

END=$(date +%s); DUR=$((END - START))

# --- 4. 요약 + 알림 ---
if [[ $rc -eq 0 && "$restart_ok" != "fail" ]]; then
  status="✅ 성공"; sound=""
else
  status="⚠️ 실패"; sound="Basso"
fi
mode_ko=$([ "$mode" = full ] && echo "전체(--force)" || echo "증분")

summary=$(cat <<EOF
[$status] vis-nightly-reindex
시각    : $(ts)
모드    : $mode ($mode_ko)$([ "$DRYRUN" = 1 ] && echo "  [dry-run]")
소요    : ${DUR}s
문서수  : $docs (indexed=$indexed)
데몬    : restart=$restart_ok
reindex exit: $rc
로그    : $RUN_LOG
EOF
)
echo "$summary" | tee "$LATEST" >> "$RUN_LOG"
echo "$summary"

msg="모드=$mode_ko · 문서=$docs · ${DUR}s · 데몬=$restart_ok"
notify "vis reindex $status" "$msg" "$sound"
notify_slack "*vis reindex $status* ($mode_ko)" "$summary"

exit $rc
