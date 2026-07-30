#!/usr/bin/env python3
"""Load documents into GroundX so the agent has something to search.

Usage:
  python scripts/ingest.py                 # loads the sample document (IRS Publication 501, ~30 pages)
  python scripts/ingest.py URL [URL ...]   # loads your own documents by URL
  python scripts/ingest.py FILE [FILE ...] # loads local files

Creates the bucket named in GROUNDX_BUCKET (default: nvidia-quickstart-demo)
if it doesn't exist, then waits for processing to finish. Processing time
scales with page count; the ~30-page sample takes a few minutes.
"""

import os
import pathlib
import sys
import time

from dotenv import load_dotenv
from groundx import GroundX

SAMPLE_URL = "https://www.irs.gov/pub/irs-pdf/p501.pdf"

load_dotenv()
gx = GroundX(api_key=os.environ["GROUNDX_API_KEY"],
             base_url=os.environ.get("GROUNDX_BASE_URL") or None)  # unset = GroundX cloud
bucket_name = os.environ.get("GROUNDX_BUCKET", "nvidia-quickstart-demo")

bucket = next((b for b in gx.buckets.list().buckets if b.name == bucket_name), None)
if bucket is None:
    bucket = gx.buckets.create(name=bucket_name).bucket
    print(f"created bucket {bucket_name!r} (id {bucket.bucket_id})")
else:
    print(f"using bucket {bucket_name!r} (id {bucket.bucket_id})")

existing = {d.file_name for d in gx.documents.lookup(id=bucket.bucket_id).documents}
sources = sys.argv[1:] or [SAMPLE_URL]
docs = []
for src in sources:
    tail = src.rsplit("/", 1)[-1]
    if tail in existing:
        print(f"skipping {tail} — already loaded")
        continue
    if src.startswith("http"):
        name = src.rsplit("/", 1)[-1] or "document.pdf"
        docs.append({"bucket_id": bucket.bucket_id, "file_name": name,
                     "file_type": name.rsplit(".", 1)[-1] if "." in name else "pdf",
                     "source_url": src, "process_level": "full"})
    else:
        p = pathlib.Path(src)
        if not p.exists():
            sys.exit(f"file not found: {src}")
        print(f"uploading local file {p.name} ...")
        gx.ingest(documents=[{"bucket_id": bucket.bucket_id, "file_name": p.name,
                              "file_path": str(p), "process_level": "full"}])

if docs:
    ing = gx.ingest(documents=docs)
    pid = ing.ingest.process_id
    print(f"processing {len(docs)} document(s) — this takes a few minutes for large files")
    while True:
        status = gx.documents.get_processing_status_by_id(process_id=pid).ingest.status
        print(f"  status: {status}")
        if status in ("complete", "error", "cancelled"):
            break
        time.sleep(20)
    if status != "complete":
        sys.exit(f"processing ended with status {status!r}")

print("done — ask a question with: scripts/run_agent.sh \"your question\"")
