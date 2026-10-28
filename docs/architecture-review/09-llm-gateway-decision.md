# LLM gateway decision (item 18)

## Context

Provider quotas constrain both request rate and total usage. Reported free-tier limits for
`gemini-embedding-001` are 100 requests per minute, 30K tokens per minute, and 1K requests per
day. These figures came from a forum reply, not an official page, and are unconfirmed. Google's
rate-limit documentation does not promise a `Retry-After` header on 429 responses, so retries
must work without one. The daily quota reset is reported to occur at midnight Pacific; this detail
is also unverified here. Heavy re-embedding experiments have hit these limits. The project has
no provider fallback or provider-usage tracking today.

## Decision

Run LiteLLM as a self-hosted proxy in Docker, using its own database in the existing PostgreSQL
service. Route generation and embedding calls through it. The proxy provides routing, retries,
cooldowns, configured fallbacks, usage logging to PostgreSQL, and a built-in `/ui` dashboard
showing spend by model, user, tag, and key.

The proxy is selected because it is free to self-host, adds usage tracking and a dashboard without
building those features in the application, reuses the existing Docker and PostgreSQL services,
and exposes one OpenAI-compatible endpoint to the application.

## Alternatives considered

1. **Build a thin router and an `llm_usage` table.** This offers more implementation learning but
   adds application code and provides no dashboard.
2. **Use LiteLLM as a Python library inside the application.** This does not provide the proxy
   dashboard and brings the library's pip supply-chain exposure into the application environment.
3. **Use OpenRouter alone.** Its free models have small daily caps and it does not provide
   embeddings.
4. **Use a second Google account or key.** Rejected: the reported quotas are per project, not per
   key; this is not a permanent solution and may conflict with terms. The terms implication has
   not been independently verified.

## Consequences

The application gains one provider endpoint for generation and embeddings and a dashboard for
usage inspection. The gateway is an additional service to operate and secure. Routing and fallback
behavior must be explicit, bounded, and covered by tests. Existing offline evaluation and
committed embedding caches remain unchanged.

## Security rules

In March 2026, LiteLLM PyPI releases 1.82.7 and 1.82.8 were reported to have been published after
a suspected maintainer account compromise and to contain a credential stealer. Official Docker
proxy image users were reported not to be affected. LiteLLM then released v1.83.0 through a new
pipeline and began cosign-signing Docker images. These incident details are from the cited
security update and have not been independently verified for this decision record.

Rules for implementation:

- Use the official LiteLLM Docker image, pinned by digest, at version 1.83.0 or later.
- Never pip-install an unpinned LiteLLM package into the application or CI environment.
- Commit gateway configuration without secrets. Do not put provider keys in the repository.
- Supply keys through ignored local `.env` configuration and/or Docker secrets; do not expose
  their values in logs or the dashboard's application-facing configuration.
- Verify the selected image digest and signature process when building the gateway.

Source: [LiteLLM security update, March 2026](https://docs.litellm.ai/blog/security-update-march-2026).

## Privacy

The supplied information states that Gemini free-tier prompts may be used to improve Google
products outside the EU/UK/EEA. This policy detail has not been independently verified here.
Because this project sends repository code to providers, do not send private code through that
free tier. Prefer providers described as offering no-training terms, such as Groq or Cerebras,
for private code, after verifying their current terms and configuration.

## Free-tier facts

The following are reported April 2026 values from the supplied comparison source, not a durable
quota guarantee. They change often and must be re-verified at build time. Store verified limits
in gateway configuration; never hard-code assumed provider quotas in application logic.

| Provider | Reported free-tier limits or condition |
|---|---|
| Groq | 30 RPM and 1,000 requests per day |
| Cerebras | 30 RPM and about 1M tokens per day |
| OpenRouter free models | 20 RPM and 50 requests per day |
| Gemini | 5–15 RPM and 20–1,500 requests per day |
| Mistral | About 1B tokens per month; free tier requires opting in to training |

Source: [OpenRouter free LLM APIs compared](https://openrouter.ai/blog/tutorials/free-llm-apis-compared/).
The table has not been independently verified and is only a point-in-time planning input.

Free hosted embedding alternatives are not dependable as permanent no-cost options: the supplied
reports describe Cohere trial use as non-commercial, time-limited, and about 1,000 calls per month;
Jina as a 10M-token trial with unclear license wording; and Mistral/Cohere signup credits rather
than permanent free tiers. These details and license interpretations are unverified here.

Sources: [Cohere free plan](https://costbench.com/software/embedding-apis/cohere-embed/free-plan/),
[Jina free plan](https://www.costbench.com/software/embedding-apis/jina-embeddings/free-plan/),
and [free-tier RAG stack comparison](https://perkstack.co/blog/rag-stack-free-tier).

The only permanently free option identified in the supplied information is an open embedding
model run locally, for example BGE, E5, or nomic through Ollama. Its quality on this code corpus
is unknown and must be measured before adoption.

## Honest limits

A fallback generation model can change answer quality and structured-output behavior. Every
fallback must pass schema validity and citation-quote validation on the golden set, and each
answer must record the provider and model that produced it. The gateway adds a service to run;
free limits change; and local embedding quality is unknown. These decisions do not claim that a
fallback is equivalent to Gemini or that any listed quota will remain available.

## Sequence

1. **18a — gateway foundation:** pinned LiteLLM sidecar, Gemini-only routing, safe retry/pacing,
   usage visibility, secret-free config, and application/telemetry integration.
2. **18b — generation fallback:** ordered Gemini, Groq, then Cerebras or OpenRouter free routes,
   with cooldowns, config-driven limits, and golden-set output/citation validation.
3. **18c — local embeddings:** register a development-only model comparison protocol, build a
   separate fixture and index labelled by `embedding_model`, and adopt only if its rule passes.
   There is no automatic cross-model embedding fallback.

External claims and prices, terms, limits, and incident details cited above are not independently
verified in this documentation-only decision record. Re-check applicable sources before
implementation and deployment.
