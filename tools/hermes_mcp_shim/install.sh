#!/usr/bin/env sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
HERMES_HOME_DIR=${HERMES_HOME:-"$HOME/.hermes"}
TARGET_DIR=${HERMES_MCP_SHIM_DIR:-"$HERMES_HOME_DIR/mcp_shim"}

mkdir -p "$TARGET_DIR"
cp "$SCRIPT_DIR/mcp_serve.py" "$TARGET_DIR/mcp_serve.py"

printf 'Installed Hermes MCP shim to %s\n' "$TARGET_DIR/mcp_serve.py"

