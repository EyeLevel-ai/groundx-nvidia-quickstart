# GroundX + NVIDIA Quickstart

An AI agent that answers questions about your documents and cites the exact page. Built from three parts, connected by one small config file:

- [NVIDIA NeMo Agent Toolkit](https://docs.nvidia.com/nemo/agent-toolkit/latest/index.html) — runs the agent
- [NVIDIA Nemotron](https://build.nvidia.com) — the language model, on NVIDIA's hosted endpoints
- [GroundX](https://docs.groundx.ai) — reads and searches the documents, via its [MCP server](https://docs.groundx.ai/documentation/agent-harness/connect-hosted-mcp-tools)

## What you need

- Python 3.11 or newer
- An NVIDIA API key — free at [build.nvidia.com](https://build.nvidia.com)
- A GroundX API key — free at [dashboard.groundx.ai](https://dashboard.groundx.ai)

## Run it

```bash
git clone https://github.com/EyeLevel-ai/groundx-nvidia-quickstart
cd groundx-nvidia-quickstart
cp .env.example .env          # put your two keys in .env
python -m venv .venv && .venv/bin/pip install -r requirements.txt
```

**1. Load a document** (the sample is the IRS Form 1040 instructions — 100+ pages of dense tables; processing takes a few minutes):

```bash
.venv/bin/python scripts/ingest.py
```

**2. Ask a question:**

```bash
scripts/run_agent.sh "What is the standard deduction for married filing jointly? Cite the page."
```

The agent finds the answer in the document library and cites the page it came from.

**3. Use your own documents:**

```bash
.venv/bin/python scripts/ingest.py https://example.com/your-document.pdf
scripts/run_agent.sh "a question about your document"
```

Prefer a notebook? [`notebooks/quickstart.ipynb`](notebooks/quickstart.ipynb) walks the same steps, plus a raw-REST example.

## Where your data goes

| Setup | Your documents | The model |
|---|---|---|
| This quickstart | GroundX's hosted service; delete anytime with `scripts/cleanup.py` | NVIDIA's hosted Nemotron receives only retrieved text passages, never files |
| Self-hosted ([one-machine install](deploy/)) | Stay on your own machine | NVIDIA's hosted Nemotron receives only text passages during document processing |

API keys travel only in connection headers — never in prompts, tool arguments, or logs. Fully local deployments (model included, air-gap capable) are a production option in the [main deployment repo](https://github.com/eyelevelai/groundx-on-prem).

## Troubleshooting

| Symptom | Fix |
|---|---|
| `mcp_client not found` when validating the config | `pip install "nvidia-nat[mcp]"` (already in requirements.txt) |
| `401 Unauthorized` connecting to GroundX | The header block in `configs/groundx_agent.yml` must be `custom_headers`, and `GROUNDX_API_KEY` must be set in `.env` |
| Model error about context length after a search | Keep the `additional_instructions` block in the config — it tells the agent to request small search responses |
| `Session termination failed: 401` warning at exit | Harmless; appears after the tools have already succeeded |
| Agent searches the wrong bucket | Ask questions that name the bucket, or keep the account free of unrelated buckets |
