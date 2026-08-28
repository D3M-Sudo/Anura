#!/bin/bash
# setup_resources.sh
#
# Copyright 2026 D3M-Sudo (Anura)
#
# MIT License

set -e

# Path to the data directory containing gresource.xml
DATA_DIR="data"

# Compile resources using the correct application ID
glib-compile-resources "$DATA_DIR/io.github.d3msudo.anura.gresource.xml" \
    --sourcedir="$DATA_DIR" \
    --sourcedir="$DATA_DIR/ui" \
    --target="$DATA_DIR/io.github.d3msudo.anura.gresource" \
    --xml-stripblanks

echo "Resources compiled successfully at $DATA_DIR/io.github.d3msudo.anura.gresource"
