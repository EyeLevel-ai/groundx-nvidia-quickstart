#!/usr/bin/env python3
"""Point GroundX's document processing at NVIDIA's Nemotron — cloud or self-hosted.

Usage: python scripts/nvidia_workflow.py

This uses GroundX *workflows*: every stage of document processing (document
summaries, keywords, section summaries, chunk summaries, search-query
generation) is a configurable step, and any step can run on any
OpenAI-compatible model — per bucket, changeable at any time, no redeploy.

This script creates a workflow whose steps all run on NVIDIA's hosted
vision-capable Nemotron, then assigns it to the quickstart bucket. Every
document loaded into that bucket afterward is processed by NVIDIA models.

Images are sent base64-inside-the-request ("openai-base64") so it works
whether or not the model can fetch image URLs.
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

# One engine definition, reused by every step.
ENGINE = {
    "engine": {
        "apiKey": NV_KEY,
        "baseURL": "https://integrate.api.nvidia.com/v1",
        "engineID": MODEL,          # must be a vision-capable model
        "service": "openai-base64", # images travel inside the request
    }
}

# Each step keeps GroundX's default prompts — only the model changes.
WORKFLOW = {
    "name": "nvidia-nemotron",
    "steps": {
        "doc-summary":   {"all": ENGINE},
        "doc-keys":      {"all": ENGINE},
        "sect-summary":  {"all": ENGINE},
        "sect-keys":     {"all": ENGINE},
        "chunk-summary": {"all": ENGINE},
        "search-query":  {"all": ENGINE},
    },
}

# Find or create the workflow by name
existing = requests.get(f"{BASE}/v1/workflow", headers=H, timeout=30).json()
match = next((w for w in existing.get("workflows", []) if w.get("name") == "nvidia-nemotron"), None)
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
