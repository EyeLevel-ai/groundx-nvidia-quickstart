# GPU Sizing Worksheet

Converts document volume into GPU capacity — standing volume, not a one-time batch, since documents keep arriving. One row is measured; every projection states its basis and is marked **not yet measured**.

## Measured row (July 2026)

| | |
|---|---|
| Machine | AWS g6e.2xlarge — one NVIDIA L40S (48GB), 8 cores, 64GB RAM |
| Configuration | Full GroundX stack on one machine. *This measurement ran three models on the GPU (vision, language, reranker); the current quickstart profile moves the language model to NVIDIA's hosted Nemotron, freeing ~19GB* |
| Document processing | 114-page IRS instruction booklet, fully processed: **62 minutes (~110 pages/hour)** |
| Search | **~3.1s median** per query (10 distinct queries) |

## What limits a single GPU (measured, not theoretical)

1. **GPU memory is the wall, not compute.** Budget roughly ~1GB per model worker process, plus ~19GB if the language model runs locally. Overshoot and the reranker fails in a misleading way: searches "work" but take ~21 seconds each (we measured this failure before fixing it).
2. **Worker counts are the throughput lever.** `layout.inference.workers` (vision) and `ranker.inference.workers` in the deploy configuration.

## Projections — not yet measured

Basis: page processing parallelizes across pages, so throughput scales roughly with vision-model workers until the machine's CPUs saturate.

| Configuration | Expected processing rate | Basis |
|---|---|---|
| Current quickstart profile (NVIDIA-hosted language model, 4 vision workers) | ~1.5–2× the measured row | Language model off the GPU; double the vision workers |
| One 24GB GPU (e.g., NVIDIA L4) | near the measured row | The two local models need well under 24GB at these worker counts |
| Three dedicated GPUs (production node groups) | ~3–4× the measured row | No GPU sharing at all |
