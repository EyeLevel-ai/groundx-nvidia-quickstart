#!/usr/bin/env bash
# Install a complete self-hosted GroundX on ONE machine with ONE NVIDIA GPU.
#
# Tested July 2026 on: Ubuntu 22.04, NVIDIA L40S (48GB), 8 vCPU, 64GB RAM,
# 500GB disk, Docker + NVIDIA Container Toolkit preinstalled (an AWS
# g6e.2xlarge with the Deep Learning Base GPU AMI matches this exactly).
#
# What it does, in order:
#   1. Creates a single-node Kubernetes cluster (minikube) with GPU access
#   2. Installs the four backing services GroundX needs: MySQL, MinIO
#      (object storage), OpenSearch, Kafka
#   3. Configures the GPU to be shared by GroundX's three model services
#   4. Installs GroundX itself from the public Helm chart
#
# Takes roughly 30-45 minutes, most of it downloading images and model weights.
# Everything is pulled from public registries; no credentials required.
#
# This profile is for demos and evaluation. Production installs use dedicated
# GPU node groups — see https://github.com/eyelevelai/groundx-on-prem
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
VALUES="$HERE/values-single-node.yaml"

# --- 1. Single-node Kubernetes with GPU ------------------------------------
# Kubernetes is pinned to 1.31: newer versions break the Kafka operator
# version this chart needs.
minikube delete 2>/dev/null || true
minikube start --driver=docker --gpus=all --cpus=7 --memory=49152 \
  --disk-size=300g --kubernetes-version=v1.31.9
minikube addons disable nvidia-device-plugin   # replaced below with a shared-GPU config

# GroundX's chart schedules pods by node label; a single node carries them all.
kubectl label node minikube node=eyelevel-cpu-only --overwrite
kubectl create namespace eyelevel

# The chart expects a storage class named eyelevel-pv to exist.
kubectl apply -f - <<SC
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata: {name: eyelevel-pv}
provisioner: k8s.io/minikube-hostpath
reclaimPolicy: Delete
volumeBindingMode: Immediate
SC

# --- 2. Backing services -----------------------------------------------------
git clone --depth 1 https://github.com/eyelevelai/groundx-on-prem /tmp/groundx-on-prem 2>/dev/null || true
cd /tmp/groundx-on-prem
helm repo add percona https://percona.github.io/percona-helm-charts/ >/dev/null 2>&1 || true
helm repo add minio-operator https://operator.min.io/ >/dev/null 2>&1 || true
helm repo add opensearch https://opensearch-project.github.io/helm-charts/ >/dev/null 2>&1 || true
helm repo add groundx https://registry.groundx.ai/helm >/dev/null 2>&1 || true
helm repo add nvdp https://nvidia.github.io/k8s-device-plugin >/dev/null 2>&1 || true
helm repo update >/dev/null

helm install db-operator percona/pxc-operator -n eyelevel -f helm/values/percona/values.operator.yaml >/dev/null
helm install minio-operator minio-operator/operator -n eyelevel -f helm/values/minio/values.operator.yaml >/dev/null
helm install opensearch opensearch/opensearch -n eyelevel -f helm/values/opensearch/values.yaml >/dev/null
# Kafka operator version matters: 0.49 is the newest that still speaks the
# API version GroundX's chart uses AND supports the Kafka version it requests.
helm install stream-operator oci://quay.io/strimzi-helm/strimzi-kafka-operator \
  --version 0.49.0 -n eyelevel -f helm/values/strimzi/values.yaml >/dev/null
echo "waiting for the four operators to come up..."
kubectl wait --for=condition=available deployment --all -n eyelevel --timeout=900s

helm install db-cluster percona/pxc-db -n eyelevel -f helm/values/percona/values.cluster.yaml >/dev/null
helm install minio-cluster minio-operator/tenant -n eyelevel -f helm/values/minio/values.tenant.yaml >/dev/null
helm install groundx-kafka-cluster groundx/groundx-strimzi-kafka-cluster -n eyelevel >/dev/null
echo "backing services installing"

# --- 3. Share the one GPU across GroundX's three model services --------------
# The device plugin advertises the GPU as 8 schedulable slots. Note: this
# shares compute; GPU MEMORY is still finite — the values file caps worker
# counts so everything fits in 48GB.
cat > /tmp/gpu-sharing.yaml <<CFG
version: v1
sharing:
  timeSlicing:
    resources:
    - name: nvidia.com/gpu
      replicas: 8
CFG
helm upgrade --install nvdp nvdp/nvidia-device-plugin -n nvidia-device-plugin \
  --create-namespace --set-file config.map.config=/tmp/gpu-sharing.yaml \
  --set config.default=config >/dev/null
# The plugin only schedules onto nodes carrying these labels (normally set by
# NVIDIA's feature-discovery service, which a single-node install doesn't run):
kubectl label node minikube nvidia.com/gpu.present=true \
  nvidia.com/device-plugin.config=config --overwrite
sleep 25
echo "GPU slots available: $(kubectl get node minikube -o jsonpath='{.status.allocatable.nvidia\.com/gpu}')"

# --- 4. GroundX itself --------------------------------------------------------
curl -sfLo /tmp/groundx-base-values.yaml \
  https://raw.githubusercontent.com/eyelevelai/groundx-on-prem/main/src/groundx/values/minikube/values.yaml
helm install groundx groundx/groundx -n eyelevel \
  -f /tmp/groundx-base-values.yaml -f "$VALUES"

# On a fully-packed single node, the default rolling-update strategy deadlocks
# any future config change; terminate-then-start avoids that.
for d in $(kubectl get deploy -n eyelevel -o name); do
  kubectl patch "$d" -n eyelevel \
    -p '{"spec":{"strategy":{"type":"Recreate","rollingUpdate":null}}}' >/dev/null 2>&1
done

echo ""
echo "GroundX is installing. Model downloads take a while; watch with:"
echo "  kubectl get pods -n eyelevel"
echo "Ready when all pods show Running."
