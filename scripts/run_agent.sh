#!/usr/bin/env bash
# Run the GroundX × Nemotron agent. Usage: scripts/run_agent.sh "your question"
set -euo pipefail
cd "$(dirname "$0")/.."
[ -f .env ] && set -a && . .env && set +a
: "${GROUNDX_API_KEY:?set GROUNDX_API_KEY in .env}"
: "${NVIDIA_API_KEY:?set NVIDIA_API_KEY in .env}"
exec .venv/bin/nat run --config_file configs/groundx_agent.yml --input "${1:-What documents are available, and what is the standard deduction for married filing jointly? Cite the page.}"
