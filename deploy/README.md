# Self-Hosted GroundX on One GPU Machine

The complete GroundX stack — document processing, search, and all supporting services — on a single machine with one NVIDIA GPU. This is the same software a customer runs behind their own firewall, packed onto one node for demos and evaluation.

## Two ways to run it

**Already have a GPU machine?** (Ubuntu 22.04, one 48GB NVIDIA GPU, 8 cores, 64GB RAM, 500GB disk, Docker + NVIDIA Container Toolkit):

```bash
./single-node-install.sh
```

**Starting from nothing, on AWS?** This creates the machine and installs everything on it:

```bash
SUBNET_ID=subnet-xxxx SECURITY_GROUP_ID=sg-xxxx ./provision-and-install-aws.sh
```

Either way: 30–45 minutes, mostly downloads. Everything pulls from public registries — no accounts or credentials needed. Done when every pod in the `eyelevel` namespace shows `Running`.

## The files

| File | What it is |
|---|---|
| `single-node-install.sh` | The entire installation in order, commented step by step |
| `values-single-node.yaml` | The complete configuration: every service pinned to the one node, GPU worker counts capped so three model services share one GPU's memory, and demo credentials matching the bundled databases (**change them for anything beyond a demo**) |
| `provision-and-install-aws.sh` | Creates the AWS machine, then runs the installer on it remotely |

## Measured on this exact setup (July 2026, one NVIDIA L40S)

- Document processing: a 114-page IRS instruction booklet fully processed in about an hour (~110 pages/hour)
- Search: ~3 seconds per query

Production deployments put each model service on its own GPU and go much faster — see the [main deployment repo](https://github.com/eyelevelai/groundx-on-prem).
