# Threat Model

## Scope and assets

This short model covers the current local IncidentWeave workflow.

- **Source code in prompts:** retrieved repository chunks may contain proprietary or sensitive text.
- **Provider credential:** `GEMINI_API_KEY` authorizes embedding and generation requests.
- **Stored audits:** investigation queries, outcomes, retrieval metadata, and tool traces are stored in PostgreSQL.

## Trust boundaries

- Repository text is untrusted input, even when it is syntactically valid source code.
- Gemini is an external processor that receives query and selected evidence text.
- API clients are outside the service boundary; protected routes require the configured API secret.

## Threats

- Prompt injection embedded in repository text can attempt to change model behavior.
- Secrets in repository files may be sent to Gemini through embeddings or generation.
- Provider or API credentials may leak through logs, responses, or source control.
- API abuse may increase provider cost, latency, or load on the local service.

## Current mitigations

- Retrieved prompt sections use `<evidence>` tags, escape closing-tag prefixes, and are identified as untrusted data.
- Ingestion skips chunks matching supported secret patterns and warns without printing matched values.
- Gemini credentials use the `x-goog-api-key` request header; API routes use `X-API-Secret`.
- Input caps, a process-local API rate limit, and generic error responses constrain some API abuse and leakage paths.
- Persisted error outcomes store the exception class name, not the exception message.

## Residual risks

- Regex scanning can miss secrets, so sensitive repository text can still reach the provider.
- Evidence tags and instructions reduce but do not eliminate prompt-injection risk.
- The rate limit is process-local and is not a distributed quota or cost budget.
- Behavioral prompt-injection tests are deferred to checklist item 12b.
