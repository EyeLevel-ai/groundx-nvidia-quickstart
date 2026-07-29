# GroundX + NVIDIA Quickstart

An AI agent that answers questions about complex documents and cites the exact page — GroundX reads and searches the documents, NVIDIA Nemotron does the reasoning, and NVIDIA's NeMo Agent Toolkit runs the agent.

**Why GroundX for the document layer:**

- **Accuracy where documents are hard.** A vision model reads every page the way a person does — tables, figures, layout — before any language model touches it. Up to 99% accuracy on documents that break general-purpose pipelines; Air France/KLM measured 96.2% against a 60% target. Separately, EyeLevel's [published head-to-head test](https://www.eyelevel.ai/post/most-accurate-rag) is public — documents, questions, and code.
- **Cheaper at scale, by design.** Because pages are broken into typed elements first, small fast models do the enrichment work — no frontier-scale model required for ingestion.
- **Runs anywhere, configured two ways.** Same product as GroundX cloud or self-hosted on your GPUs (public [Helm chart](https://github.com/eyelevelai/groundx-on-prem), air-gap capable). Deployment is configured with Helm values; *processing* is configured with **workflows** — per-bucket, at runtime, over the API. You'll use both below.

**How the pieces fit — loading documents:**

```mermaid
flowchart LR
    D["Your documents"] --> G["GroundX<br/>vision model reads each page's<br/>tables, figures, and text"]
    G -- "page images" --> N["Nemotron nano-vl<br/>NVIDIA-hosted"]
    N -- "descriptions of<br/>tables & figures" --> G
    G --> X[("Search index")]
```

**How the pieces fit — asking questions:**

```mermaid
flowchart LR
    U["Your question"] --> A["Agent<br/>NeMo Agent Toolkit,<br/>reasoning on Nemotron super-49b"]
    A -- "search" --> S["GroundX search<br/>reranker scores results"]
    S -- "page-cited results" --> A --> R["Answer, with the page<br/>it came from"]
```

Two different models look at pages: GroundX's own vision model reads *layout* (where the tables, figures, and text sit); the vision-capable Nemotron writes the *descriptions* that make them searchable. Self-hosted, GroundX's vision model and reranker run on **your** NVIDIA GPU; on GroundX cloud they run on GroundX's NVIDIA GPUs. Nemotron is NVIDIA-hosted in both cases.

## Contents

- [What you need](#what-you-need)
- [Scenario A — GroundX cloud](#scenario-a--groundx-cloud) *(fastest: ~10 minutes)*
- [Scenario B — self-hosted GroundX + NVIDIA models](#scenario-b--self-hosted-groundx--nvidia-models) *(your machine: ~45 minutes)*
- [Let your coding agent drive GroundX](#let-your-coding-agent-drive-groundx)
- [Where your data goes](#where-your-data-goes)
- [Troubleshooting](#troubleshooting)

## What you need

- Python 3.11 or newer
- An NVIDIA API key — free at [build.nvidia.com](https://build.nvidia.com)
- A GroundX API key — free at [dashboard.groundx.ai](https://dashboard.groundx.ai)
- Scenario B additionally needs a GPU machine — see [deploy/](deploy/)

## Scenario A — GroundX cloud

Documents go to your GroundX cloud account; nothing to install beyond Python packages.

```bash
git clone https://github.com/EyeLevel-ai/groundx-nvidia-quickstart
cd groundx-nvidia-quickstart
cp .env.example .env          # put your two keys in .env
python -m venv .venv && .venv/bin/pip install -r requirements.txt
```

**1. Point document processing at NVIDIA models** — one command:

```bash
.venv/bin/python scripts/nvidia_workflow.py
```

This is GroundX's **workflow** system doing what it's for: every processing stage — document summaries, keywords, section and chunk summaries, the chunk instructions that turn tables and figures into searchable text, search-query generation — is a configurable step, and any step can run on any OpenAI-compatible model, per bucket (a named collection of documents), changed at runtime with an API call. This command points all of them at NVIDIA's vision-capable Nemotron. The same mechanism swaps prompts, chunking strategy, and models per project without redeploying anything.

**2. Load a document** (the sample is the IRS Form 1040 instructions — 100+ pages of dense tables; processing takes a few minutes, now running on Nemotron):

```bash
.venv/bin/python scripts/ingest.py
```

**3. Ask the agent a question.** The agent discovers its GroundX tools (search, ingest) from GroundX's hosted MCP server at `https://api.groundx.ai/mcp` — a standard tool interface any agent framework can use; NVIDIA's toolkit connects to it natively:

```bash
scripts/run_agent.sh "What is the standard deduction for married filing jointly? Cite the page."
```

**4. Use your own documents:**

```bash
.venv/bin/python scripts/ingest.py https://example.com/your-document.pdf
```

Prefer a notebook? [`notebooks/quickstart.ipynb`](notebooks/quickstart.ipynb) walks the same steps plus a raw-REST example.

## Scenario B — self-hosted GroundX + NVIDIA models

GroundX runs on your own GPU machine; documents never leave it. Your NVIDIA GPU runs the page-reading vision model and the search reranker; NVIDIA's hosted Nemotron handles enrichment, receiving page images during processing.

1. Install on your machine (or let the AWS script create one): **[deploy/](deploy/)** — one required input, ~45 minutes. Here the NVIDIA model choice lives in Helm values (deployment configuration); workflows work on top of it exactly as in Scenario A.
2. Run the quickstart scripts **on that machine**, pointing them at the local API with one line in `.env` (the deploy guide's "Use it" section shows the port-forward that makes this address work):
   ```
   GROUNDX_BASE_URL=http://localhost:8080/api
   ```
3. Load documents and search exactly as in Scenario A.

Note: the agent demo (`run_agent.sh`) connects to GroundX's hosted MCP tool server, which the single-node build doesn't include — so the agent step is for Scenario A; Scenario B drives loading and search through the scripts and notebook.

## Let your coding agent drive GroundX

Everything this quickstart does by script, your AI coding assistant can do conversationally. The [GroundX Agent Harness](https://github.com/GroundX-Studio/groundx-agent-harness) is a free skills bundle that makes Claude Code, Codex, and similar agents fluent in GroundX — ingest, search, workflows, debugging, self-hosted planning.

```bash
claude plugin marketplace add GroundX-Studio/groundx-agent-harness
claude plugin install groundx-agent-harness@groundx-agent-harness
```

(Those commands are for Claude Code; the [harness repo](https://github.com/GroundX-Studio/groundx-agent-harness) has steps for Codex and other clients.) What's in the bundle:

| Skill area | What your agent learns |
|---|---|
| Ingest & search | Load documents, check processing status, search with citations, debug stuck documents and empty results |
| Workflows & organization | Create and assign workflows (like this quickstart's), manage buckets and groups |
| Structured extraction | Build schema-first extraction workflows for pulling fields from documents |
| Self-hosted planning | Size and plan Helm-chart deployments |

Then ask in your own words, for example:

- *"Create a workflow like nvidia-nemotron but add a custom chunk prompt for financial tables."*
- *"Why is my document stuck in processing?"*
- *"Plan a self-hosted GroundX install for a 3-node cluster."*

Set `GROUNDX_API_KEY` in the shell that starts your agent. With that key the agent can create and delete documents and buckets in your account — treat it like any credential, and use a separate account if you want a sandbox.

## Go deeper

- [Security fact sheet](docs/it-reviewer-fact-sheet.md) — what runs where and what leaves the firewall, per configuration
- [GPU sizing](docs/sizing-worksheet.md) — measured throughput and how document volume converts to GPU count
- [Running GroundX on NVIDIA models](docs/nemotron-engine.md) — the two configuration surfaces and endpoint findings
- [AI-Q knowledge backend](aiq/) — GroundX as a retrieval backend for NVIDIA's AI-Q research agent, written to its documented plug-in contract

## Where your data goes

| Scenario | Your documents | The model |
|---|---|---|
| A — cloud | Your GroundX cloud account; delete anytime with `scripts/cleanup.py` | NVIDIA-hosted Nemotron receives page images (fetched from your account's access-controlled URLs) during processing, and text passages at question time — never files |
| B — self-hosted | Stay on your machine | Same: page images during processing, text passages at question time — never files |

API keys travel only in connection headers — never in prompts, tool arguments, or logs. Fully local deployments (models included, air-gap capable) are a production option in the [main deployment repo](https://github.com/eyelevelai/groundx-on-prem).

## Troubleshooting

| Symptom | Fix |
|---|---|
| `mcp_client not found` when validating the config | Install from `requirements.txt` — it includes the MCP plugin |
| `401 Unauthorized` connecting to GroundX | The header block in `configs/groundx_agent.yml` must be `custom_headers`, and `GROUNDX_API_KEY` must be set in `.env` |
| Model error about context length after a search | Keep the `additional_instructions` block in the config — it tells the agent to request small search responses |
| `Session termination failed: 401` warning at exit | Harmless; appears after the tools have already succeeded |
| Agent searches the wrong bucket | Ask questions that name the bucket, or keep the account free of unrelated buckets |
