# GroundX on One GPU Machine, with NVIDIA's Hosted Nemotron

GroundX runs inside your own machine; the language model it calls for document enrichment is NVIDIA's hosted Nemotron. Documents never leave your machine — the model only receives text passages during processing. (Running the language model locally too is a production option covered in the [main deployment repo](https://github.com/eyelevelai/groundx-on-prem), not here.)

## Required

- `export NVIDIA_API_KEY=nvapi-...` — free at [build.nvidia.com](https://build.nvidia.com). **That's the only required input.**

## Optional

- Demo passwords (admin login, database, object storage) — listed in the header of `values-single-node.yaml`. Fine to leave for a demo; change them for anything else.

## Run it

Already have a GPU machine (Ubuntu 22.04, one NVIDIA GPU, 8 cores, 64GB RAM, 500GB disk, Docker + NVIDIA Container Toolkit — an AWS g6e.2xlarge with the Deep Learning Base GPU AMI matches):

```bash
export NVIDIA_API_KEY=nvapi-...
./single-node-install.sh
```

Starting from nothing on AWS (creates the machine, then installs on it):

```bash
export NVIDIA_API_KEY=nvapi-... SUBNET_ID=subnet-... SECURITY_GROUP_ID=sg-...
./provision-and-install-aws.sh
```

30–45 minutes either way, mostly downloads. Done when every pod in the `eyelevel` namespace shows `Running`.

## What runs on the machine

| Group | Services | GPU? |
|---|---|---|
| Document pipeline | intake, queueing, orchestration, **vision model** (reads page layout: tables, figures, text), OCR, assembly, save | vision model: yes |
| Search | query handling, **reranker** (scores search results) | reranker: yes |
| Enrichment routing | one service that sends enrichment calls to NVIDIA's hosted Nemotron | no — the model is NVIDIA-hosted |
| Storage | MySQL, MinIO (files), OpenSearch (search index), Kafka (queues) | no |

Only two models run locally, so the GPU has headroom: tested on a 48GB L40S; this profile should also fit a 24GB GPU (not yet verified).

## Where the NVIDIA model is configured

The `engines` block in [`values-single-node.yaml`](values-single-node.yaml) — endpoint URL and model name. Your API key is injected at install time by the script (`--set engines.default.apiKey=...`), so it never sits in a file. To change models later, edit that block and run the same `helm upgrade` command from the install script.

## Measured (July 2026, one 48GB L40S)

- Document processing: a 114-page IRS instruction booklet fully processed in about an hour (~110 pages/hour) — measured on an earlier profile that also ran a local language model; this profile frees that model's ~19GB of GPU memory and doubles the vision-model workers, so expect better (not yet re-measured)
- Search: ~3 seconds per query
