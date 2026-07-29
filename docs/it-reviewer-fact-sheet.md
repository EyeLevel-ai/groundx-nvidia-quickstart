# GroundX Self-Hosted — IT Reviewer Fact Sheet

*One page for security and infrastructure reviewers. Written for a questionnaire, not a pitch. Current as of 2026-07-29.*

## What runs where

| Configuration | Document content | Model inference | External runtime dependencies |
|---|---|---|---|
| **Self-hosted + NVIDIA-hosted model (this quickstart's [deploy](../deploy/) setup)** | Entirely inside your cluster (object store, search index, database all in-cluster) | Vision model and reranker run in-cluster on your GPU; document-enrichment calls go to NVIDIA's hosted Nemotron with text passages only | The NVIDIA model endpoint |
| Fully self-hosted (production option, [main deployment repo](https://github.com/eyelevelai/groundx-on-prem)) | Entirely inside your cluster | All models in-cluster, including the language model | **None at runtime** — suitable for air-gapped operation |
| GroundX hosted service | GroundX cloud (api.groundx.ai) | GroundX cloud | n/a |

## What leaves the firewall, per configuration

- **Self-hosted + NVIDIA-hosted model (this quickstart):** text passages sent to the NVIDIA model endpoint during document processing; no raw files leave. Install-time: container images and model weights pull from public registries.
- **Fully self-hosted (production option):** nothing at runtime; installs can be pre-staged for air-gapped environments.
- **Agent integrations:** the agent's model (wherever it runs) receives retrieved text passages at question time — never raw files, never credentials. API keys travel only in connection headers.

## Data lifecycle

- Documents, extracted artifacts, and search indexes live in your cluster's storage (MinIO/S3-compatible object store, OpenSearch, MySQL).
- Deletion: per-document and per-bucket delete via API; storage is under your retention policies.
- Every search result carries provenance (document, page, bounding box) — auditability is structural, not bolted on.

## Deployment surface

- Helm chart (public: `registry.groundx.ai/helm`), Kubernetes 1.31-class clusters, including OpenShift (Red Hat publishes an official quickstart: `rh-ai-quickstart/Billing-extraction-with-GroundX`).
- All application pods are stateless; state lives in the backing stores. No inbound connectivity required beyond your API ingress.
- GPU: NVIDIA. Demo/sizing reference: the vision model and reranker share a single L40S (48GB); production deployments use the documented node groups.

## Honest notes for this demo environment

- The demonstration machine is an AWS instance operated by GroundX, and its language model is NVIDIA-hosted. Fully air-gapped operation is a production configuration, not what this demo runs.
- Demo credentials in this kit are placeholder values; production installs use your own secrets management.
