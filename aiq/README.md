# GroundX as an AI-Q Knowledge Backend — experimental preview

A working retriever adapter that plugs GroundX into NVIDIA's [AI-Q research agent](https://github.com/NVIDIA-AI-Blueprints/aiq) through its published knowledge-layer plug-in contract. Collections map to GroundX buckets; every chunk carries page-level provenance from GroundX bounding boxes, satisfying the knowledge layer's citation contract.

> **Status (July 2026):** written against AI-Q's published contract and checked by `smoke_test.py`, which verifies the package is importable, the adapter compiles, the config delta parses with the required keys, the backend name is `groundx`, and a live GroundX search returns every field the adapter maps (`score`, `fileName`, `boundingBoxes.pageNumber`). **Installing it requires hand-editing an AI-Q checkout, and it has not been run inside a live AI-Q workflow** — that needs a review slot with someone who has one.

Two files:

- **`groundx_backend/adapter.py`** — a retriever backend registered as `groundx`.
- **`config_web_groundx.yml`** — a delta over upstream's `config_web_opensearch.yml`: only the `knowledge_search` block differs.

Re-run the smoke check yourself:

```bash
GROUNDX_API_KEY=... python aiq/smoke_test.py
```

## Install into an AI-Q checkout

AI-Q registers custom backends by editing its own source — the exact steps are its `sources/knowledge_layer/KNOWLEDGE-LAYER-SETUP.md`, "Building a Custom Backend" (paths below verified against upstream, July 2026):

1. Copy `groundx_backend/` to `sources/knowledge_layer/src/groundx_backend/` (Steps 1–3 of the upstream guide — the adapter and `__init__.py` are already written).
2. Add `knowledge_layer.groundx_backend` to the `packages` list in `sources/knowledge_layer/pyproject.toml` (Step 4).
3. Edit `sources/knowledge_layer/src/register.py` per Step 5: add `"groundx"` to the `BackendType` literal, add `groundx_api_key` / `groundx_base_url` fields to `KnowledgeRetrievalConfig`, and add a `groundx` case to `_setup_backend()` that imports `knowledge_layer.groundx_backend.adapter` and passes those two fields through.
4. Merge the `knowledge_search` block from `config_web_groundx.yml` into a copy of upstream's `configs/config_web_opensearch.yml`, and add the commented `data_source_registry` entry to the registry list.
5. Export `GROUNDX_API_KEY` (and `NVIDIA_API_KEY`) and start the workflow as usual.
