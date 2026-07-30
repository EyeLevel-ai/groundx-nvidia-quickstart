#!/usr/bin/env python3
"""Point GroundX's document processing at NVIDIA's Nemotron — cloud or self-hosted.

Usage: python scripts/nvidia_workflow.py

This uses GroundX *workflows*: every stage of document processing (document
summaries, keywords, section summaries, chunk summaries, chunk instructions
for tables and figures, search-query generation) is a configurable step, and any step can run on any
OpenAI-compatible model — per bucket, changeable at any time, no redeploy.

This script creates a workflow whose steps all run on NVIDIA's hosted
vision-capable Nemotron, then assigns it to the quickstart bucket. Every
document loaded into that bucket afterward is processed by NVIDIA models.

Image transport is picked automatically: against GroundX cloud, page images
are referenced by URL (cloud artifacts are publicly accessible); against a
self-hosted instance (GROUNDX_BASE_URL set), images are sent base64 inside the
request, because a private machine's URLs aren't reachable by a hosted model.
"""

import os
import sys

import requests
from dotenv import load_dotenv
from groundx import GroundX

load_dotenv()
GX_KEY = os.environ["GROUNDX_API_KEY"]
NV_KEY = os.environ.get("NVIDIA_API_KEY") or sys.exit("export NVIDIA_API_KEY first (free at build.nvidia.com)")
BASE = (os.environ.get("GROUNDX_BASE_URL") or "https://api.groundx.ai/api").rstrip("/")
MODEL = os.environ.get("NVIDIA_INGEST_MODEL", "nvidia/llama-3.1-nemotron-nano-vl-8b-v1")
H = {"X-API-Key": GX_KEY, "Content-Type": "application/json"}

# Cloud artifacts are publicly accessible -> reference images by URL ("openai").
# Self-hosted artifacts are internal -> embed images base64 ("openai-base64").
SERVICE = "openai-base64" if os.environ.get("GROUNDX_BASE_URL") else "openai"

# One engine definition, reused by every step.
ENGINE = {
    "engine": {
        "apiKey": NV_KEY,
        "baseURL": "https://integrate.api.nvidia.com/v1",
        "engineID": MODEL,   # must be a vision-capable model
        "service": SERVICE,
    }
}

# Each step keeps GroundX's default prompts — only the model changes.
WORKFLOW = {
    "name": "nvidia-nemotron",
    "steps": {
        "doc-summary":    {"all": ENGINE},
        "doc-keys":       {"all": ENGINE},
        "sect-summary":   {"all": ENGINE},
        "sect-keys":      {"all": ENGINE},
        "chunk-summary":  {"all": ENGINE},
        "chunk-instruct": {"all": ENGINE},  # the step that turns tables & figures into searchable text
        "search-query":   {"all": ENGINE},
    },
}

# Reuse the workflow this script created last time. The id is cached locally so
# re-runs are idempotent without depending on the workflow-list endpoint, which
# is slow enough to time out.
import pathlib
import time

CACHE = pathlib.Path(__file__).with_name(".nvidia-workflow-id")
match = None
if CACHE.exists():
    wid_cached = CACHE.read_text().strip()
    g = requests.get(f"{BASE}/v1/workflow/{wid_cached}", headers=H, timeout=60)
    if g.ok:
        match = {"workflowId": wid_cached}
    else:
        CACHE.unlink()  # stale (deleted elsewhere) — fall through and create

if match is None:
    # No cached id: try the list endpoint, but retry and never treat a failure as
    # "not found" without saying so — that would silently create a duplicate.
    listed = False
    for attempt in range(3):
        r = requests.get(f"{BASE}/v1/workflow", headers=H, timeout=60)
        if r.ok:
            match = next((w for w in r.json().get("workflows", []) if w.get("name") == "nvidia-nemotron"), None)
            listed = True
            break
        if attempt < 2:
            time.sleep(5 * (attempt + 1))
    if not listed:
        print(f"note: the workflow list endpoint timed out ({r.status_code}); creating a "
              "fresh 'nvidia-nemotron' workflow and caching its id for next time.")
if match:
    wid = match["workflowId"]
    r = requests.put(f"{BASE}/v1/workflow/{wid}", headers=H, json=WORKFLOW, timeout=30)
    r.raise_for_status()
    print(f"updated workflow nvidia-nemotron ({wid})")
else:
    r = requests.post(f"{BASE}/v1/workflow", headers=H, json=WORKFLOW, timeout=30)
    r.raise_for_status()
    wid = r.json()["workflow"]["workflowId"]
    print(f"created workflow nvidia-nemotron ({wid})")
CACHE.write_text(wid)

# Ensure the quickstart bucket exists, then assign the workflow to it
gx = GroundX(api_key=GX_KEY, base_url=os.environ.get("GROUNDX_BASE_URL") or None)
bucket_name = os.environ.get("GROUNDX_BUCKET", "nvidia-quickstart-demo")
bucket = next((b for b in gx.buckets.list().buckets if b.name == bucket_name), None)
if bucket is None:
    bucket = gx.buckets.create(name=bucket_name).bucket
    print(f"created bucket {bucket_name!r} (id {bucket.bucket_id})")

r = requests.post(f"{BASE}/v1/workflow/relationship/{bucket.bucket_id}",
                  headers=H, json={"workflowId": wid}, timeout=30)
r.raise_for_status()
print(f"bucket {bucket_name!r} now processes every document with {MODEL}")
print("undo anytime: delete the assignment or the workflow — no redeploy, no downtime")
