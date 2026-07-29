# GroundX as an AI-Q Knowledge Backend

GroundX plugged into NVIDIA's [AI-Q research agent](https://github.com/NVIDIA-AI-Blueprints/aiq) through its documented knowledge-layer plug-in contract. Two files:

- **`groundx_backend/adapter.py`** — a retriever backend registered as `groundx`. Collections map to GroundX buckets; every chunk carries page-level provenance from GroundX bounding boxes, satisfying the knowledge layer's citation contract.
- **`config_web_groundx.yml`** — **a delta, not a runnable config.** It documents only the `knowledge_search` block that differs from upstream's `config_web_opensearch.yml`; identical sections are copied from upstream at install time.

## Status

Written against the AI-Q knowledge-layer contract as of July 2026 and smoke-checked outside an AI-Q checkout with:

```bash
GROUNDX_API_KEY=... python aiq/smoke_test.py
```

The smoke test verifies that the adapter compiles, the config delta parses with the required keys, and a live GroundX search returns every field the adapter maps (`score`, `fileName`, `boundingBoxes.pageNumber`). Full in-workflow validation — the adapter imported and driven by `aiq_agent` — requires an AI-Q checkout and has not been run here.

## Install into an AI-Q checkout

1. Copy `groundx_backend/` into `sources/knowledge_layer/src/groundx_backend/` and register it per the AI-Q docs (`KNOWLEDGE-LAYER-SETUP.md`, "Building a Custom Backend").
2. Merge the `knowledge_search` block from `config_web_groundx.yml` into a copy of upstream's `config_web_opensearch.yml`, and add the commented `data_source_registry` entry to the registry list.
3. Export `GROUNDX_API_KEY` (and `NVIDIA_API_KEY`) and start the workflow as usual.
