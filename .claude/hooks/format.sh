#!/bin/bash
FILE_PATH=$(jq -r '.tool_input.file_path')
if [ -f "$FILE_PATH" ] && [[ "$FILE_PATH" == *.py ]]; then
  uv run ruff format "$FILE_PATH" 2>/dev/null || true
fi
