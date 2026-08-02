#!/usr/bin/env bash
# Stop hook: lint-only verification before allowing the turn to end.
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"
case "${HERETEK_STACK:-python}" in
  python)
    if [[ -f pyproject.toml ]]; then
      ruff check . || exit 1
      ruff format --check . || exit 1
    fi
    ;;
  node)
    [[ -f package.json ]] && npx --no-install eslint . || true
    ;;
esac
exit 0
