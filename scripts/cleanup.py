#!/usr/bin/env python3
"""Delete the quickstart bucket and everything in it.

Usage: python scripts/cleanup.py
"""

import os

from dotenv import load_dotenv
from groundx import GroundX

load_dotenv()
gx = GroundX(api_key=os.environ["GROUNDX_API_KEY"],
             base_url=os.environ.get("GROUNDX_BASE_URL") or None)  # unset = GroundX cloud
bucket_name = os.environ.get("GROUNDX_BUCKET", "nvidia-quickstart-demo")

bucket = next((b for b in gx.buckets.list().buckets if b.name == bucket_name), None)
if bucket is None:
    print(f"no bucket named {bucket_name!r} — nothing to delete")
else:
    gx.buckets.delete(bucket_id=bucket.bucket_id)
    print(f"deleted bucket {bucket_name!r} and its documents")
