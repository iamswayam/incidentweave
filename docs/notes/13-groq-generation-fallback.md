# Optional Groq Generation Fallback

## Scope and policy

This adds Groq as an optional fallback for text generation only. Gemini remains
the primary generation provider and continues to serve all embeddings. The
embedding model and 768-dimensional vector contract do not change.

Fallback is disabled by default and is attempted only when
`GROQ_FALLBACK_ENABLED=true`, `GROQ_API_KEY` is set, and `GROQ_MODEL` is set.
Gemini's retry budget is used first; if it exhausts on an eligible failure, the
Groq adapter runs once, with its own configured retry budget and independently
owned rate limiter and cooldown.

| Gemini result | Fallback? | Reason |
|---|---:|---|
| `rate_limited`, including exhausted HTTP 429 or an open Gemini cooldown | Yes | Retry budget is exhausted or the Gemini circuit is open |
| `server_error` | Yes | A transient provider-side failure may be isolated to Gemini |
| `timeout` | Yes | The primary provider did not complete within its deadline |
| `auth` | No | Another provider does not repair invalid Gemini credentials |
| `bad_request` | No | The request itself must not be hidden by another provider |
| `safety_blocked` | No | A safety refusal must not be bypassed |
| `schema_invalid` | No | Invalid model output is not treated as provider availability |

Groq errors are surfaced with the original Gemini error as their cause. There is
no direct-provider bypass when the fallback is disabled or incompletely
configured. A successful response is normalized to the existing Gemini-shaped
payload and validated by the same investigation response parser.

## Configuration

All keys are read through `app/config.py` from environment variables or the
ignored local `.env`; `.env.example` contains blank secret placeholders only.
No key is committed or included in a request URL.

| Setting | Default | Purpose |
|---|---|---|
| `GROQ_API_KEY` | unset | Groq credential |
| `GROQ_MODEL` | unset | Explicit model identifier; there is no code-selected model |
| `GROQ_FALLBACK_ENABLED` | `false` | Master opt-in |
| `GROQ_TIMEOUT_SECONDS` | `60` | HTTP client timeout |
| `GROQ_RATE_LIMIT_RPM` | unset | Optional local request/minute ceiling |
| `GROQ_RATE_LIMIT_TPM` | unset | Optional local estimated token/minute ceiling |
| `GROQ_RATE_LIMIT_RPD` | unset | Optional local request/day ceiling |
| `GROQ_COOLDOWN_FAILURES` | unset | Optional retryable-failure threshold |
| `GROQ_COOLDOWN_SECONDS` | unset | Optional cooldown duration |

Unset limiter and cooldown settings disable those local controls; they do not
assert or infer a Groq account quota. Groq publishes organization-level limits
for RPM, RPD, TPM, TPD, and, for some organizations, ITPM and OTPM. The exact
limits are available in the account's Limits page. Its public table identifies
the shown values as Developer-plan base limits, not universal free-plan
quotas; numeric free-plan RPM, TPM, and RPD values for this deployment are
therefore **unverified** and are not hard-coded.

## Structured output and model selection

The configured model is sent to Groq's OpenAI-compatible Chat Completions
endpoint. For models documented as supporting `json_schema`, the request uses
best-effort (`strict: false`) schema output. Other configured models receive
`json_object` plus the response schema in the system instruction. In both cases,
the returned text is validated against the existing investigation response
contract; schema errors fail explicitly.

The official structured-output page lists these `strict: false` models:

- `openai/gpt-oss-20b`
- `openai/gpt-oss-120b`
- `openai/gpt-oss-safeguard-20b`
- `qwen/qwen3.8-27b`
- `meta-models/muse-spark-open`

Its strict-mode list excludes `openai/gpt-oss-safeguard-20b`. This implementation
uses `strict: false` for all listed models; it does not select a model by
default. Model capabilities and availability can change, so check the current
official list when configuring a model.

## Usage and observability

When provider usage logging is enabled, Groq records the existing metadata
fields: provider, configured model, `generation` operation, status, error class,
attempt count, latency, available token counts, and correlation ID. It does not
record prompt or response text. The existing report groups by provider and
model, so Groq appears in separate groups without a schema migration.

The fallback event logs only the error class and the provider transition
(`gemini` to `groq`). It does not log the key, prompt, source snippets, or model
response. Groq's `retry-after` header is honored for retries following HTTP 429.
The adapter classifies 429, 5xx, timeout, auth, bad request, and safety refusal
responses using the existing typed provider errors.

## Privacy warning

Enabling this feature transmits repository code snippets and incident text to
a second vendor. It is off by default. Before enabling it, the maintainer must
review Groq's current data terms, data controls, and account settings. Groq's
documentation says inference data is not retained by default, while reliability
and abuse monitoring may retain inputs and outputs for up to 30 days; Zero Data
Retention controls are available. Groq states customer data is retained in US
GCP buckets when retention applies. These statements are not a guarantee of
zero retention in every configuration.

## Verified provider facts

Official Groq documentation was checked on **2026-10-30**:

| Fact | Verified statement | Source |
|---|---|---|
| OpenAI-compatible endpoint and key input | Groq documents OpenAI-client compatibility, the `https://api.groq.com/openai/v1` base URL, and passing the Groq key as the client's `api_key`. The compatibility page does not explicitly spell out the raw HTTP authorization header; the implementation uses the OpenAI-compatible Bearer authorization header. | [OpenAI compatibility](https://console.groq.com/docs/openai) |
| Rate-limit dimensions | RPM, RPD, TPM, and TPD are documented; some organizations also have ITPM/OTPM. Limits apply at organization level. Exact organization limits are in its Limits page. | [Rate limits](https://console.groq.com/docs/rate-limits) |
| Numeric free-plan limits | **Unverified.** The page's displayed numeric table is labeled Developer-plan base limits and does not establish universal free-plan values. | [Rate limits](https://console.groq.com/docs/rate-limits) |
| 429 behavior | Exceeding a limit returns HTTP 429; `retry-after` is set when the rate-limit response is 429. | [Rate limits](https://console.groq.com/docs/rate-limits) |
| Structured output | `json_schema` model support is listed above. `json_object` is the documented alternative for models without structured-output support; the app validates schema compliance itself. | [Structured outputs](https://console.groq.com/docs/structured-outputs) |
| Data handling | Inference customer data is not retained by default; reliability/abuse monitoring can retain it for up to 30 days. ZDR controls are available and applicable retained customer data is stored in US GCP buckets. | [Your data](https://console.groq.com/docs/your-data) |
| Training use | The cited data page describes retention and monitoring but does not state whether customer inputs or outputs are used for model training; that point is **unverified** from the source read. | [Your data](https://console.groq.com/docs/your-data) |

The documentation verifies that clients pass a Groq API key through an
`api_key` parameter. The exact raw header spelling was not independently
verified from the fetched Groq compatibility text.

## Local activation and manual live check

First review the current Groq terms and account data controls. Then set the
key, model, and opt-in flag in the local shell or ignored `.env`; never commit
the key. The following PowerShell command directly exercises the Groq adapter
with a minimal prompt and prints no generated content:

```powershell
.\.venv\Scripts\python.exe -c "import asyncio; from app.providers.groq import generate_with_groq; asyncio.run(generate_with_groq('Return a minimal schema-compliant insufficient-evidence JSON object.')); print('Groq generation succeeded')"
```

The command requires `GROQ_FALLBACK_ENABLED=true`, `GROQ_API_KEY`, and
`GROQ_MODEL` in the process environment. This is a manual live request for the
maintainer to run; CI and this implementation task do not call Groq or Gemini.

## CI, evaluation, and limits

CI needs neither a gateway nor a provider key. Unit tests replace HTTP with
`httpx.MockTransport`. Offline evaluation and the embedding cache remain
unchanged; embeddings remain direct Gemini calls. Groq request pacing is
independently configurable and unset by default. There is no model quality
equivalence claim: answers may differ between Gemini and Groq, and all results
remain subject to the existing evidence and citation checks.
