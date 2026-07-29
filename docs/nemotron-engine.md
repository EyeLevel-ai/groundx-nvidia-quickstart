# Running GroundX + agents on Nemotron NIM endpoints — validated findings

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

`GET /v1/models` returned 102 models including `nvidia/llama-3.1-nemotron-70b-instruct`, but invoking that model returns `404 {"title":"Not Found","detail":"Function ... Not found"}`. **Pin models by verified invocation, not by catalog listing**, and re-verify pinned models before demos.

## Running a self-hosted deployment's language model on Nemotron

A self-hosted GroundX deployment can point its document-enrichment model at a hosted Nemotron endpoint with a values-file change — no code involved. In our testing (July 2026) a full document ingest completed with this configuration:

```yaml
engines:
  default:
    engineId: nvidia/llama-3.3-nemotron-super-49b-v1.5
    baseUrl: https://integrate.api.nvidia.com/v1
    apiKey: <NVIDIA_API_KEY — inject via secret management, never commit>
    service: openai
    vision: false
    maxInputTokens: 100000
    maxOutputTokens: 8192   # generous budget lets the reasoning model answer without /no_think
    maxRequests: 4
    requestLimit: 4
```

`helm upgrade` with this overlay switches the summary tier to Nemotron; removing it reverts to the bundled self-hosted LLM. Notes: `engineId` must be a **verified-invocable** NIM model (see Gotcha 2); reasoning models work through the standard OpenAI-shaped engine when `maxOutputTokens` is generous — `/no_think` is an optimization, not a requirement, for this path.

## Summary

GroundX's language-model layer speaks the standard OpenAI-compatible API with a configurable endpoint, so pointing it at Nemotron is a configuration change. The one behavior to plan for: Nemotron's reasoning-family models need either the `/no_think` system message or a generous output-token budget, or responses come back empty (Gotcha 1 above).
