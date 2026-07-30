#!/usr/bin/env bash
# Run the GroundX × Nemotron agent. Usage: scripts/run_agent.sh "your question"
set -euo pipefail
cd "$(dirname "$0")/.."
[ -f .env ] && set -a && . .env && set +a
: "${GROUNDX_API_KEY:?set GROUNDX_API_KEY in .env}"
: "${NVIDIA_API_KEY:?set NVIDIA_API_KEY in .env}"
# Prefer the repo venv; fall back to nat on PATH (conda, system env, notebook kernel)
NAT=.venv/bin/nat
[ -x "$NAT" ] || NAT=$(command -v nat) || { echo "nat not found — install with: pip install -r requirements.txt" >&2; exit 1; }
exec "$NAT" run --config_file configs/groundx_agent.yml --input "${1:-What documents are available, and what is the standard deduction for married filing jointly? Cite the page.}"
