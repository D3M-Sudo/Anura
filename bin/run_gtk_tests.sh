#!/bin/bash
# Helper script to run GTK tests using xvfb-run

# Ensure we are in the project root
cd "$(dirname "$0")/.."

# Check if xvfb-run is installed
if ! command -v xvfb-run &> /dev/null; then
    echo "Error: xvfb-run is not installed. Please install it to run GTK tests."
    exit 1
fi

# 1. Detect system PyGObject (gi)
GI_PATH=""
# Try common python versions
for py_ver in "3" "3.10" "3.11" "3.12" "3.13"; do
    for base in "/usr/lib/python$py_ver" "/usr/local/lib/python$py_ver"; do
        if [ -d "$base/dist-packages/gi" ]; then
            GI_PATH="$base/dist-packages"
            break 2
        fi
        if [ -d "$base/site-packages/gi" ]; then
            GI_PATH="$base/site-packages"
            break 2
        fi
    done
done

if [ -n "$GI_PATH" ]; then
    echo "Detected system PyGObject at: $GI_PATH"
    export PYTHONPATH="$GI_PATH:$PYTHONPATH"
else
    echo "Warning: Could not detect system PyGObject (gi). Tests may fail."
fi

# 2. Detect GObject Introspection typelibs
TYPELIB_PATHS=""
# Common arch-independent path
if [ -d "/usr/lib/girepository-1.0" ]; then
    TYPELIB_PATHS="/usr/lib/girepository-1.0"
fi

# Common multi-arch paths
ARCH=$(uname -m)
case $ARCH in
    x86_64)  ARCH_DIR="x86_64-linux-gnu" ;;
    i386|i686) ARCH_DIR="i386-linux-gnu" ;;
    aarch64) ARCH_DIR="aarch64-linux-gnu" ;;
    armv7l)  ARCH_DIR="arm-linux-gnueabihf" ;;
    *)       ARCH_DIR="" ;;
esac

if [ -n "$ARCH_DIR" ] && [ -d "/usr/lib/$ARCH_DIR/girepository-1.0" ]; then
    if [ -n "$TYPELIB_PATHS" ]; then
        TYPELIB_PATHS="$TYPELIB_PATHS:/usr/lib/$ARCH_DIR/girepository-1.0"
    else
        TYPELIB_PATHS="/usr/lib/$ARCH_DIR/girepository-1.0"
    fi
fi

if [ -n "$TYPELIB_PATHS" ]; then
    echo "Setting GI_TYPELIB_PATH to: $TYPELIB_PATHS"
    export GI_TYPELIB_PATH="$TYPELIB_PATHS:$GI_TYPELIB_PATH"
fi

# Run tests
echo "Running GTK tests with xvfb-run..."
xvfb-run -a uv run pytest tests/ -v -m gtk --tb=long "$@"
