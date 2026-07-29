# Running GroundX on NVIDIA Models — the two configuration surfaces

GroundX points its document processing at NVIDIA models through two surfaces, used in this repo:

| Surface | Scope | When |
|---|---|---|
| **Workflows** (`scripts/nvidia_workflow.py`) | Per bucket, at runtime, over the API — works on cloud and self-hosted alike | Change models, prompts, or chunking per project with an API call; no redeploy |
| **Helm values** (`deploy/values-single-node.yaml`, the `engines` block) | Per deployment, at install/upgrade time — self-hosted only | Set the deployment-wide default model |

Both carry the same engine fields (endpoint URL, model name, key, transport). The rest of this page is endpoint-level findings that apply to either surface.

## Endpoint findings (July 2026, integrate.api.nvidia.com)

Validated 2026-07-28 against `https://integrate.api.nvidia.com/v1` (OpenAI-compatible hosted NIM endpoints, free-trial API key).

## Validated model + recipe

| Setting | Value |
|---|---|
| Base URL | `https://integrate.api.nvidia.com/v1` |
| Model | `nvidia/llama-3.3-nemotron-super-49b-v1.5` |
| Required system message | `/no_think` (when you want plain content, e.g. for GroundX's ingestion-time enrichment) |
| Auth | `Authorization: Bearer $NVIDIA_API_KEY` |

Verified: `temperature: 0`, deterministic short completion, `finish_reason: stop`, clean `usage` block (36 total tokens for the smoke test).

## Gotcha 1 — reasoning models return null `content` by default

Nemotron's current flagship models are *reasoning* models. Without the toggle, the response places chain-of-thought in `message.reasoning` / `message.reasoning_content`, and if `max_tokens` is consumed by reasoning, **`message.content` is `null` with `finish_reason: "length"`**.

Any OpenAI-compatible client that reads `choices[0].message.content` (including GroundX's summary engine pointed at this endpoint) must either:

1. send the `/no_think` system message (validated — content returns normally), or
2. budget `max_tokens` generously and handle reasoning fields, or
3. pin a non-reasoning model.

Token accounting note: reasoning tokens count in `usage` — cost/metering must expect higher totals when reasoning is on.

## Gotcha 2 — the model catalog lists models that are not invocable

`GET /v1/models` returned 102 models including `nvidia/llama-3.1-nemotron-70b-instruct`, but invoking that model returns `404 {"title":"Not Found","detail":"Function ... Not found"}`. **Pin models by verified invocation, not by catalog listing**, and re-verify pinned models before relying on them.

## Running a self-hosted deployment's language model on Nemotron

A self-hosted GroundX deployment can point its document-enrichment model at a hosted Nemotron endpoint with a values-file change — no code involved. In our testing (July 2026) a full document ingest completed with this configuration:

```yaml
engines:
  default:
    engineId: nvidia/llama-3.1-nemotron-nano-vl-8b-v1   # must be vision-capable
    baseUrl: https://integrate.api.nvidia.com/v1
    apiKey: <NVIDIA_API_KEY — inject at install time, never commit>
    service: openai-base64
    vision: true
    maxInputTokens: 100000
    maxOutputTokens: 8192
    maxRequests: 8
    requestLimit: 8
```

Two settings matter for extraction quality on a self-hosted machine:

- **`vision: true`** — enrichment sends page images, not just text. Without images, charts and figure-heavy pages extract poorly.
- **`service: openai-base64`** — images travel inside the request body. Required whenever the machine's image storage isn't reachable from the internet (a hosted model can't fetch internal URLs). Use plain `service: openai` only if your image URLs are externally accessible.

The model in `engineId` must therefore be **vision-capable and verified-invocable** (see Gotcha 2). Text-only models like `llama-3.3-nemotron-super-49b-v1.5` are fine as an *agent's* language model (this repo's agent config) but not for image-based document enrichment.

## Summary

GroundX's language-model layer speaks the standard OpenAI-compatible API with a configurable endpoint, so pointing it at Nemotron is a configuration change. The one behavior to plan for: Nemotron's reasoning-family models need either the `/no_think` system message or a generous output-token budget, or responses come back empty (Gotcha 1 above).
