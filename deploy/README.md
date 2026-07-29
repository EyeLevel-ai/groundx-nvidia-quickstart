# Self-Hosted GroundX on One GPU Machine

One script installs the complete GroundX stack — document processing, search, and all supporting services — on a single machine with one NVIDIA GPU. This is the same software a customer runs behind their own firewall; this profile packs it onto one node for demos and evaluation.

## Requirements

- Ubuntu 22.04 with Docker and the NVIDIA Container Toolkit (AWS example: a `g6e.2xlarge` with the Deep Learning Base GPU AMI ships ready)
- One NVIDIA GPU with 48GB memory (tested on an L40S), 8 CPU cores, 64GB RAM, 500GB disk
- `kubectl`, `helm`, and `minikube` installed
- Internet access during install (everything pulls from public registries — no accounts or credentials needed)

## Run

```bash
./single-node-install.sh
```

30–45 minutes, mostly downloads. When every pod in the `eyelevel` namespace shows `Running`, the API is live inside the cluster.

## What the two files are

- `single-node-install.sh` — the whole installation, in order, with comments explaining each step
- `values-single-node.yaml` — the settings that make one node work: every service pinned to the single node, GPU worker counts capped so three model services fit in one GPU's memory, and demo credentials matching the bundled databases (**change these for anything beyond a demo**)

## Measured on this exact profile (July 2026, one L40S)

- Document processing: a 114-page IRS instruction booklet, fully processed in about an hour (~110 pages/hour)
- Search: ~3 seconds per query

Production deployments put each model service on its own GPU and go much faster — see the [main deployment repo](https://github.com/eyelevelai/groundx-on-prem).
