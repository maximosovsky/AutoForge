#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
SKILL_NAME="autoforge-hermes"
SOURCE_DIR="$REPO_ROOT/hermes/skills/$SKILL_NAME"
HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"
TARGET_DIR="$HERMES_HOME/skills/software-development/$SKILL_NAME"

python_path() {
  if command -v cygpath >/dev/null 2>&1; then
    cygpath -w "$1"
  else
    printf '%s\n' "$1"
  fi
}

if [[ ! -f "$SOURCE_DIR/SKILL.md" ]]; then
  echo "ERROR: missing $SOURCE_DIR/SKILL.md" >&2
  exit 1
fi

python "$(python_path "$SCRIPT_DIR/validate-skill.py")"
mkdir -p "$(dirname "$TARGET_DIR")"
rm -rf "$TARGET_DIR"
cp -R "$SOURCE_DIR" "$TARGET_DIR"

echo "Installed $SKILL_NAME to $TARGET_DIR"
echo "Start a new Hermes session or run /reload-skills before using it."
