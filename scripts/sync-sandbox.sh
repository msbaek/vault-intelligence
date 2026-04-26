#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC="$REPO_ROOT/tests/fixtures/sandbox_vault"
DST="/tmp/vault-test"

if [[ ! -d "$SRC" ]]; then
  echo "ERROR: sandbox fixture missing at $SRC" >&2
  exit 1
fi

rm -rf "$DST"
cp -a "$SRC" "$DST"
echo "sandbox synced: $DST"
