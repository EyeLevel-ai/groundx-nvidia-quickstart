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

## Implication for GroundX's summary engine

GroundX's LLM tier is engine-agnostic (OpenAI-compatible engines with a configurable base URL), so pointing it at a Nemotron NIM is configuration — but the `/no_think` system-message requirement means the engine config for reasoning-family Nemotron models must inject that system message (or a non-reasoning Nemotron model must be pinned). This is the summary-engine validation finding; see the demo-kit change log for the follow-up decision.
