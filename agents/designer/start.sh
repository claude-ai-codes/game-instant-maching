#!/bin/bash
# Designer Agent launcher
# Usage: ./start.sh or via tmux

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$PROJECT_ROOT"

exec claude \
  --append-system-prompt "$(cat "$SCRIPT_DIR/AGENT.md")" \
  --allowedTools "Read,Glob,Grep,Write,Edit,Bash"
