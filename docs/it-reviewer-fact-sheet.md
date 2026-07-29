# GroundX Self-Hosted — IT Reviewer Fact Sheet

*One page for security and infrastructure reviewers. Written for a questionnaire, not a pitch. Current as of 2026-07-29.*

## What runs where

| Configuration | Document content | Model inference | External runtime dependencies |
|---|---|---|---|
| **Self-hosted (this deployment)** | Entirely inside your Kubernetes cluster (object store, search index, database all in-cluster) | Three GPU inference services in-cluster: fine-tuned vision model, summary LLM, reranker | **None at runtime** — suitable for air-gapped operation |
| Self-hosted + external LLM (optional) | Stays in-cluster | Enrichment LLM calls go to the endpoint you configure (e.g., an NVIDIA-hosted Nemotron endpoint, or your own NIM in-cluster) | Only the LLM endpoint you opt into |
| GroundX hosted service | GroundX cloud (api.groundx.ai) | GroundX cloud | n/a |

## What leaves the firewall, per configuration

- **Self-hosted, default:** nothing at runtime. Install-time only: container image pulls and model-weight downloads (both can be pre-staged for air-gapped installs — offline bundle available on request).
- **Self-hosted with external LLM opt-in:** retrieved text passages sent to the configured LLM endpoint at enrichment time; no raw files leave.
- **Agent integrations (MCP):** the agent's LLM (wherever it runs) receives retrieved text chunks at question time — never raw files, never credentials. API keys travel only in transport headers.

## Data lifecycle

- Documents, extracted artifacts, and search indexes live in your cluster's storage (MinIO/S3-compatible object store, OpenSearch, MySQL).
- Deletion: per-document and per-bucket delete via API; storage is under your retention policies.
- Every search result carries provenance (document, page, bounding box) — auditability is structural, not bolted on.

## Deployment surface

- Helm chart (public: `registry.groundx.ai/helm`), Kubernetes 1.31-class clusters, including OpenShift (Red Hat publishes an official quickstart: `rh-ai-quickstart/Billing-extraction-with-GroundX`).
- All application pods are stateless; state lives in the backing stores. No inbound connectivity required beyond your API ingress.
- GPU: NVIDIA. Demo/sizing reference: all three inference services share a single L40S (48GB) via device-plugin time-slicing; production deployments use the documented node groups.

## Honest notes for this demo environment

- The demonstration node is an AWS EC2 instance operated by GroundX — *air-gapped is the supported deployment mode being demonstrated, not this demo's own network posture.*
- Demo credentials in this kit are placeholder values; production installs use your own secrets management.
