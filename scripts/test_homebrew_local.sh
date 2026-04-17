#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DIST_ARCHIVE="$ROOT/dist/clawbackup-0.1.1.tar.gz"
TAP_NAME="${1:-local/clawbackup}"

if [[ ! -f "$DIST_ARCHIVE" ]]; then
  echo "missing archive: $DIST_ARCHIVE" >&2
  echo "run: \$HOME/Library/Python/3.11/bin/pyproject-build --sdist" >&2
  exit 1
fi

python3 "$ROOT/scripts/render_homebrew_formula.py" "$DIST_ARCHIVE" >/dev/null

TAP_ROOT="$(brew --repository)/Library/Taps/${TAP_NAME%/*}/homebrew-${TAP_NAME#*/}"
mkdir -p "$TAP_ROOT/Formula"
cp "$ROOT/Formula/clawbackup.rb" "$TAP_ROOT/Formula/clawbackup.rb"

HOMEBREW_NO_AUTO_UPDATE=1 brew install "${TAP_NAME}/clawbackup"
