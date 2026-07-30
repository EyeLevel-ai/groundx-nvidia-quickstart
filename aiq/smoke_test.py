#!/usr/bin/env python3
"""Smoke test for the GroundX AI-Q knowledge backend.

Checks, without requiring an AI-Q checkout:
  1. adapter.py compiles (syntax-valid against the documented contract)
  2. config_web_groundx.yml parses and carries the required knowledge_search keys
  3. the GroundX endpoint is reachable and the search path returns results
     with the fields the adapter maps (score, fileName, boundingBoxes.pageNumber)

Full in-workflow validation (adapter imported by aiq_agent) requires an AI-Q
checkout.
"""

import json
import os
import pathlib
import py_compile
import sys
import urllib.request

HERE = pathlib.Path(__file__).parent
FAILURES = []


def check(name: str, ok: bool, detail: str = ""):
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f" — {detail}" if detail else ""))
    if not ok:
        FAILURES.append(name)


# 0. package is complete (copying groundx_backend/ must yield an importable package)
check("groundx_backend/__init__.py exists", (HERE / "groundx_backend" / "__init__.py").is_file())

# 1. adapter compiles
try:
    py_compile.compile(str(HERE / "groundx_backend" / "adapter.py"), doraise=True)
    check("adapter.py compiles", True)
except py_compile.PyCompileError as e:
    check("adapter.py compiles", False, str(e))

# 2. YAML parses with required keys
try:
    import yaml  # type: ignore

    cfg = yaml.safe_load((HERE / "config_web_groundx.yml").read_text())
    ks = cfg["functions"]["knowledge_search"]
    required = {"_type", "backend", "collection_name", "groundx_api_key"}
    missing = required - set(ks)
    check("config parses + required keys", not missing, f"missing: {missing}" if missing else "")
    check("backend is groundx", ks.get("backend") == "groundx")
except Exception as e:  # noqa: BLE001
    check("config parses + required keys", False, repr(e))

# 3. endpoint reachable + field shape
key = os.environ.get("GROUNDX_API_KEY")
if not key:
    check("GROUNDX_API_KEY set", False, "export it to run the live check")
else:
    base = os.environ.get("GROUNDX_BASE_URL", "https://api.groundx.ai/api").rstrip("/")
    try:
        req = urllib.request.Request(f"{base}/v1/bucket", headers={"X-API-Key": key})
        buckets = json.load(urllib.request.urlopen(req, timeout=30)).get("buckets", [])
        check("endpoint reachable (bucket list)", True, f"{len(buckets)} buckets")
        target = next((b for b in buckets if b["name"] == os.environ.get("COLLECTION_NAME", "nvidia-quickstart-demo")), None)
        if target:
            body = json.dumps({"query": "standard deduction", "n": 2}).encode()
            req = urllib.request.Request(
                f"{base}/v1/search/{target['bucketId']}",
                data=body,
                headers={"X-API-Key": key, "Content-Type": "application/json"},
                method="POST",
            )
            results = json.load(urllib.request.urlopen(req, timeout=60)).get("search", {}).get("results", [])
            ok = bool(results) and all(
                "score" in r and "fileName" in r and r.get("boundingBoxes") for r in results[:1]
            )
            check("search returns adapter-mappable fields", ok, f"{len(results)} results")
        else:
            check("demo collection exists", False, "bucket nvidia-quickstart-demo not found")
    except Exception as e:  # noqa: BLE001
        check("endpoint reachable", False, repr(e))

sys.exit(1 if FAILURES else 0)
