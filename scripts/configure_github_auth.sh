#!/usr/bin/env bash
set -euo pipefail

REMOTE_URL="${1:-https://github.com/brwa59196-beep/project-polymasters.git}"
TOKEN="${GITHUB_TOKEN:-}"

if ! command -v git >/dev/null 2>&1; then
    echo "ERROR: git is not installed or is not available in PATH." >&2
    exit 1
fi

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    echo "ERROR: run this script from inside the repository checkout." >&2
    exit 1
fi

if [[ -z "$TOKEN" && -t 0 ]]; then
    read -r -s -p "GitHub token: " TOKEN
    echo
fi

if [[ -z "$TOKEN" ]]; then
    cat >&2 <<'MSG'
ERROR: GITHUB_TOKEN is not set.
Create a fine-grained GitHub token with Contents: Read and write, then run:
  export GITHUB_TOKEN=YOUR_TOKEN
  scripts/configure_github_auth.sh
MSG
    exit 1
fi

git remote get-url origin >/dev/null 2>&1 || git remote add origin "$REMOTE_URL"
git remote set-url origin "$REMOTE_URL"
git config credential.helper "cache --timeout=28800"
printf 'protocol=https\nhost=github.com\nusername=x-access-token\npassword=%s\n\n' "$TOKEN" | git credential approve

echo "GitHub credentials cached for this terminal session."
echo "Remote origin: $(git remote get-url origin)"
echo "Test with: git ls-remote --heads origin"
echo "Push with: git push origin HEAD:codex/write-code-for-call-option-arbitrage"
