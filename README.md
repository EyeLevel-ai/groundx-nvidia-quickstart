# GroundX × NVIDIA Quickstart

Run a [NeMo Agent Toolkit](https://docs.nvidia.com/nemo/agent-toolkit/1.3/index.html) (v1.3) agent that answers questions over complex documents using **GroundX** as its document-intelligence layer — connected through the GroundX MCP server — with a hosted **Nemotron** NIM endpoint as the agent's language model.

**Time to first cited answer: ~15 minutes.** No GroundX engineer required.

## What this demonstrates

1. **Zero-glue integration** — the agent uses GroundX's `search` and `ingest` tools via MCP, natively supported by NeMo Agent Toolkit v1.3. No adapters, no forked code.
2. **Nemotron in the loop** — the agent LLM is a build.nvidia.com hosted Nemotron NIM endpoint; the same OpenAI-compatible endpoint can also drive GroundX's own ingestion-time enrichment tier (see `docs/nemotron-engine.md`).
3. **Inspectable retrieval** — every answer carries page-level citations. The `inspect` step dumps GroundX's X-Ray output for a page: per-element structured JSON (summaries, keywords, multiple text renderings, source-page provenance). The retriever is not a black box.

## Prerequisites

- Python 3.11+
- An NVIDIA API key — free at [build.nvidia.com](https://build.nvidia.com)
- A GroundX API key — from [dashboard.eyelevel.ai](https://dashboard.eyelevel.ai)

## Quickstart

```bash
git clone https://github.com/EyeLevel-ai/groundx-nvidia-quickstart
cd groundx-nvidia-quickstart
cp .env.example .env   # add your two keys
pip install -r requirements.txt
python scripts/run_agent.py "What is the total baggage allowance for a business-class transatlantic ticket?"
```

The demo corpus is pre-ingested — your first query returns a cited answer immediately. To ingest your own documents:

```bash
python scripts/ingest.py path/to/your.pdf
python scripts/run_agent.py "your question about your document"
```

## Data flow

| Configuration | Where your documents go | Where inference runs |
|---|---|---|
| Default (this quickstart) | GroundX hosted service (api.groundx.ai) | Agent LLM: NVIDIA-hosted Nemotron endpoint |
| Self-hosted GroundX | Your own cluster — [air-gapped Helm deployment](https://github.com/eyelevelai/groundx-on-prem), no external runtime dependencies | Your GPUs; agent LLM configurable to a local NIM |

Documents ingested to the hosted demo bucket can be deleted at any time via `scripts/cleanup.py` or the GroundX API. Nothing in this quickstart sends your documents to NVIDIA; the agent LLM receives only retrieved text chunks at question time.

## Ownership and compatibility

This repo is maintained by the GroundX team (EyeLevel/Valantor). We own compatibility with **NeMo Agent Toolkit v1.3** and will re-certify against new toolkit releases within 30 days; issues are triaged here, not against NVIDIA's repos.

## Repo layout

```
configs/     NeMo Agent Toolkit workflow config (MCP wiring, Nemotron LLM)
scripts/     run_agent.py, ingest.py, cleanup.py
notebooks/   quickstart.ipynb — the 5-minute guided path
docs/        nemotron-engine.md (GroundX enrichment on Nemotron), architecture notes
```

## Status

Work in progress — built as part of the GroundX × NVIDIA demo kit (private during construction; gated public release).
