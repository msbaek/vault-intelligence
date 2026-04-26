#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VIS_VAULT_PATH="${VIS_VAULT_PATH:-/tmp/vault-test}"
TEST_PORT="${TEST_PORT:-8742}"
PID_FILE="/tmp/vis-test-daemon.pid"

if [[ -f "$PID_FILE" ]] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
  echo "test vis daemon already running (pid=$(cat $PID_FILE), port=$TEST_PORT)"
  exit 0
fi

echo "starting test vis daemon: vault=$VIS_VAULT_PATH port=$TEST_PORT"
VIS_PORT="$TEST_PORT" nohup vis serve \
  --vault-path "$VIS_VAULT_PATH" \
  --port "$TEST_PORT" \
  > /tmp/vis-test-daemon.log 2>&1 &
echo $! > "$PID_FILE"
sleep 2
curl -sf "http://localhost:$TEST_PORT/health" > /dev/null \
  && echo "test daemon ready at port $TEST_PORT" \
  || echo "WARNING: daemon may not be ready yet — check /tmp/vis-test-daemon.log"
