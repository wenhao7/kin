#!/usr/bin/env bash
# Hermes container entrypoint: install on first start (into $HERMES_HOME), then run.
#   gateway  → hermes gateway run   (default; long-lived)
#   shell    → interactive bash with hermes on PATH (for `hermes setup`, `hermes doctor`, …)
#   <any>    → passed to `hermes` (e.g. `doctor`, `model`, `gateway setup`)
set -euo pipefail

export HERMES_HOME="${HERMES_HOME:-/opt/data}"
mkdir -p "$HERMES_HOME"

# Load shell init the installer may have written (adds hermes to PATH).
for f in "$HOME/.bashrc" "$HOME/.profile"; do
  # shellcheck disable=SC1090
  [ -f "$f" ] && source "$f" || true
done
export PATH="$HOME/.local/bin:$HERMES_HOME/bin:$HERMES_HOME/hermes-agent/.venv/bin:$PATH"

if ! command -v hermes >/dev/null 2>&1; then
  echo ">> hermes not found; installing into $HERMES_HOME (first start only)"
  curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash
  for f in "$HOME/.bashrc" "$HOME/.profile"; do
    # shellcheck disable=SC1090
    [ -f "$f" ] && source "$f" || true
  done
  export PATH="$HOME/.local/bin:$HERMES_HOME/bin:$HERMES_HOME/hermes-agent/.venv/bin:$PATH"
  if ! command -v hermes >/dev/null 2>&1; then
    echo "!! hermes still not on PATH after install. Contents of $HERMES_HOME and ~/.local/bin:"
    ls -la "$HERMES_HOME" "$HOME/.local/bin" 2>/dev/null || true
    exit 1
  fi
fi

# Seed config.yaml from the repo template on first start.
if [ ! -f "$HERMES_HOME/config.yaml" ] && [ -f /seed/config.yaml ]; then
  echo ">> seeding $HERMES_HOME/config.yaml from template"
  cp /seed/config.yaml "$HERMES_HOME/config.yaml"
fi

case "${1:-gateway}" in
  gateway)
    exec hermes gateway run
    ;;
  shell)
    exec bash
    ;;
  *)
    exec hermes "$@"
    ;;
esac
