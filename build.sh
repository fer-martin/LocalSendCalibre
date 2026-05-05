#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
PLUGIN_DIR="$ROOT/plugin"
DIST_DIR="$ROOT/dist"
VERSION="${1:-dev}"
OUT="$DIST_DIR/localsend-calibre-plugin-$VERSION.zip"

mkdir -p "$DIST_DIR"
rm -f "$OUT"

cd "$PLUGIN_DIR"
zip -r "$OUT" . \
    -x "*.pyc" \
    -x "__pycache__/*" \
    -x ".DS_Store"

echo "Built: $OUT"
unzip -l "$OUT"