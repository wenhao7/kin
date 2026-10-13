#!/usr/bin/env bash
# Hermes container entrypoint: install on first start (into $HERMES_HOME), then run.
#   gateway  → hermes gateway run   (default; long-lived)
#   shell    → interactive bash with hermes on PATH (for `hermes setup`, `hermes doctor`, …)
#   <any>    → passed to `hermes` (e.g. `doctor`, `model`, `gateway setup`)
set -euo pipefail

export HERMES_HOME="${HERMES_HOME:-/opt/data}"
mkdir -p "$HERMES_HOME"

# Seed config.yaml from the repo template before the installer runs: the installer writes its
# own default config.yaml (OpenRouter) when none exists, and only adds new options to an
# existing one.
if [ ! -f "$HERMES_HOME/config.yaml" ] && [ -f /seed/config.yaml ]; then
  echo ">> seeding $HERMES_HOME/config.yaml from template"
  cp /seed/config.yaml "$HERMES_HOME/config.yaml"
fi
# Kin's persona; Hermes would otherwise seed its own default SOUL.md. Re-applied by `make hermes-config`.
if [ ! -f "$HERMES_HOME/SOUL.md" ] && [ -f /seed/SOUL.md ]; then
  cp /seed/SOUL.md "$HERMES_HOME/SOUL.md"
fi

# The installer's launcher lives on the volume; ~/.local/bin holds only a shim to it.
export PATH="$HERMES_HOME/hermes-agent/.hermes/bin:$HOME/.local/bin:$PATH"

if ! command -v hermes >/dev/null 2>&1; then
  echo ">> hermes not found; installing into $HERMES_HOME (first start only)"
  curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash
  if ! command -v hermes >/dev/null 2>&1; then
    echo "!! hermes still not on PATH after install. Contents of $HERMES_HOME and ~/.local/bin:"
    ls -la "$HERMES_HOME" "$HOME/.local/bin" 2>/dev/null || true
    exit 1
  fi
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
