#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

DLX_URL="${DLX_URL:-${DEEPLX_URL:-http://127.0.0.1:1188/translate}}"
DLX_ROOT="${DLX_URL%/translate}"
STARTED_BY_SCRIPT=0
DLX_PID=""
DLX_CONTAINER=""

cleanup() {
  if [[ -n "$DLX_PID" ]]; then
    kill "$DLX_PID" 2>/dev/null || true
  fi
  if [[ -n "$DLX_CONTAINER" ]]; then
    docker stop "$DLX_CONTAINER" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT INT TERM

reachable() {
  curl --silent --show-error --max-time 1 --output /dev/null "$DLX_ROOT" 2>/dev/null
}

# Avoid starting DLX when no source text has changed.
if python3 scripts/update_translations.py --check; then
  quarto publish gh-pages --no-prompt --no-browser
  exit 0
fi

if ! reachable; then
  if command -v deeplx >/dev/null 2>&1; then
    echo "Starting temporary local DLX binary..."
    deeplx >/tmp/leis-note-dlx.log 2>&1 &
    DLX_PID=$!
    STARTED_BY_SCRIPT=1
  elif command -v docker >/dev/null 2>&1; then
    echo "Starting temporary local DLX container..."
    DLX_CONTAINER="leis-note-dlx-$$"
    docker run --detach --rm \
      --name "$DLX_CONTAINER" \
      --publish 127.0.0.1:1188:1188 \
      ghcr.io/owo-network/deeplx:latest >/dev/null
    STARTED_BY_SCRIPT=1
  else
    cat >&2 <<'EOF'
Translations need updating, but neither a local `deeplx` binary nor Docker is available.

Install DLX from https://github.com/OwO-Network/DLX, or start it manually:
  docker run -d --rm -p 127.0.0.1:1188:1188 ghcr.io/owo-network/deeplx:latest
EOF
    exit 1
  fi

  for _ in $(seq 1 30); do
    reachable && break
    sleep 1
  done
fi

if ! reachable; then
  echo "DLX did not become reachable at $DLX_ROOT" >&2
  exit 1
fi

export DLX_URL TRANSLATION_PROVIDER=dlx
python3 scripts/update_translations.py
quarto publish gh-pages --no-prompt --no-browser

if ! git diff --quiet -- 'posts/**/translations-en.json'; then
  echo
  echo "Translation files changed. Review and commit them to the main branch."
fi

if [[ "$STARTED_BY_SCRIPT" == 1 ]]; then
  echo "Temporary DLX stopped."
fi
