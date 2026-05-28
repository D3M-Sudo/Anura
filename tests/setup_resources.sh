#!/bin/bash
# tests/setup_resources.sh
# Programmatically compile Blueprint files and GResource bundle for testing

set -e

PROJECT_ROOT=$(pwd)
DATA_DIR="$PROJECT_ROOT/data"
UI_DIR="$DATA_DIR/ui"

echo "🔧 Compiling Blueprint files..."
for f in "$UI_DIR"/*.blp; do
    if [ -f "$f" ]; then
        blueprint-compiler compile "$f" --output "$UI_DIR/$(basename "$f" .blp).ui"
    fi
done

echo "🔨 Compiling GResource bundle..."
glib-compile-resources "$DATA_DIR/com.github.d3msudo.anura.gresource.xml" \
    --target="$DATA_DIR/com.github.d3msudo.anura.gresource" \
    --sourcedir="$DATA_DIR" \
    --sourcedir="$UI_DIR"

echo "✅ Resources ready for testing."
