#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "usage: $0 path/to/clawbackup-<version>.tar.gz" >&2
  exit 1
fi

archive="$1"
shasum -a 256 "$archive" | awk '{print $1}'
