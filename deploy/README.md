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

## What uses GPUs, and for what

**On your GPU (the machine this installs):**

| Model | Job |
|---|---|
| Vision model | Reads every page's layout — tables, figures, text regions — during document processing |
| Reranker | Re-scores results for relevance on every search |

**On NVIDIA's GPUs (hosted Nemotron, via your API key):** a vision-capable Nemotron receives each page image during processing and writes the descriptions that make tables and figures searchable. Images travel inside the request (base64) because this machine's storage isn't reachable from outside — that's the `service: openai-base64` setting in the values file, and it's why the model must be vision-capable.

Everything else on the machine is CPU-only plumbing: intake, queues, orchestration, OCR, the API, and storage (MySQL, MinIO, OpenSearch, Kafka).

Two local models leave the GPU headroom: tested on a 48GB L40S; should fit a 24GB GPU (not yet verified).

## Changing the NVIDIA model

Edit the `engines` block in [`values-single-node.yaml`](values-single-node.yaml) (endpoint + model name — keep it vision-capable), then re-run the `helm upgrade` line from the install script. Your API key is injected at install time and never sits in a file.

## Measured (July 2026, one 48GB L40S)

- Document processing: a 114-page IRS instruction booklet fully processed in about an hour (~110 pages/hour) — measured on an earlier profile that also ran a local language model; this profile frees that model's ~19GB of GPU memory and doubles the vision-model workers, so expect better (not yet re-measured)
- Search: ~3 seconds per query
