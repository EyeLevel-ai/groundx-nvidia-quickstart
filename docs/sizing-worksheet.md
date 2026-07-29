# GroundX GPU Sizing Worksheet

*Measured 2026-07-29 on the demo profile. One fully measured row; every projection row states its method and is labeled [to validate]. One extrapolated row will be replaced by a measured row before this worksheet is used in any field quote.*

## Measured row (demo profile)

| Config | AWS g6e.2xlarge — 1× NVIDIA L40S (48GB), 8 vCPU, 64GB RAM |
|---|---|
| Topology | All three GroundX GPU inference services (fine-tuned vision model, summary LLM, reranker) **time-slicing the single GPU**; full stack (29 pods) on one node via minikube |
| Ingest throughput | IRS Form 1040 instructions — ~114 pages [verify vs X-Ray], 1.12M file tokens, full agentic processing: **3,695s (≈62 min)** → **≈110 pages/hour sustained** |
| Query latency (distinct, uncached) | **median ≈3.1s, range 3.02–3.58s** (n=10) — hybrid search + GPU rerank |
| Query latency (repeat, cached) | ≈42ms |
| Cold-start first query | ≈3.8s |

## Binding constraints observed on this profile (measured, not theoretical)

1. **GPU memory, not compute, is the wall.** Time-slicing shares compute; VRAM is hard-partitioned by allocation. Budget: summary LLM ≈19GB + ~1GB per inference worker process. Worker counts (`layout.inference.workers`, `ranker.inference.workers`) must be set so total VRAM < 44GB usable, else the reranker OOMs and every query pays a ~21s timeout-fallback penalty (measured before the fix).
2. **CPU requests must be trimmed** to fit the single node (see quickstart overlay) — production uses the chart's documented node groups instead.

## Projection method

Pages/hour scales approximately linearly with dedicated GPU capacity per service until the pipeline's CPU stages saturate, because per-page work (vision inference, OCR, enrichment) is embarrassingly parallel across pages. Stated assumptions: (a) dedicating a GPU to each service removes time-slice contention (measured profile shares one GPU three ways); (b) L40S↔L40S comparisons are 1:1; (c) CPU stages sized per the chart's node-group guidance don't bottleneck below 5× the single-node rate. Assumption (a) is the next measurement.

| Config (per chart node groups) | Projected ingest | Basis | Status |
|---|---|---|---|
| 3× L40S (one per GPU service) + CPU node group | ≈300–450 pages/hour | Remove 3-way time-slice contention (2.7–4×) | **[to validate — next measured row]** |
| 2-node scale-out of the above | ≈600–900 pages/hour | Stateless pods scale horizontally; queue-based pipeline | [to validate] |
| Query latency, dedicated ranker GPU | ≈1–2s uncached | Removes time-slice wait from the ~3.1s measured | [to validate] |

## Deal-shaping note

Every row above is NVIDIA GPU capacity. Documents keep arriving (claims daily, filings quarterly), so ingest is recurring utilization — not a one-time batch. Volume growth converts directly to GPU count via this worksheet.
