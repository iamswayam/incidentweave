# Production CLI / API (Phase 9)

**Date built:** September 2026
**Status:** Drafted - author sections pending

## What I built

I added three HTTP endpoints: synchronous persisted `POST /investigations`, `GET /investigations/{id}`, and `GET /repositories`, protected by an `X-API-Secret` dependency and a 10-requests-per-60-seconds in-memory per-IP limiter. Investigation responses retain the evidence scores and Phase 8 evaluation note; the Docker image now includes scripts and migrations, and `scripts/serve.py` provides a psycopg-compatible Windows launch path. The persisted GET reconstructs evidence from the last recorded tool attempt, including a final grep result.

## Why this design

The HTTP routes call the existing investigation pipeline and database models rather than duplicating domain logic. Investigation work stays synchronous because a request takes a few Gemini seconds, and ingestion and embedding remain CLI-only; a job queue and production-grade authentication were explicitly deferred. Evidence scores and the fixed evaluation note keep Phase 8's measured uncertainty visible, while `scripts/serve.py` selects a Windows `SelectorEventLoop` before Uvicorn starts because psycopg does not support its default Proactor loop.

## Key concept, explained simply
Write this as if explaining to an interviewer with no context — one paragraph,
no jargon you can't unpack further if asked.

## Walkthrough example

Using the permanent `scripts/serve.py` server and the real `incidentweave-local` database, `GET /repositories` returned HTTP `200` with four repositories. A real POST asking “What chunk size does repository ingestion use?” returned HTTP `200` and investigation ID `23`; it cited chunks `1334`, `1333`, and `1335`, reported RRF `0.01639344262295082`, vector score `0.319359047097336`, and confidence `medium` (`raw_confidence: high`). `GET /investigations/23` returned HTTP `200` with matching diagnosis, citations, and evidence scores. Missing and wrong secrets each returned `401`; authenticated requests 1–10 returned `200`, and request 11 returned `429`.

## What broke when I tested it

On Windows, setting `WindowsSelectorEventLoopPolicy` in `app/main.py` did not fix direct Uvicorn startup: Uvicorn creates its loop before importing the app, and psycopg rejected the resulting `ProactorEventLoop`. An early launcher attempt called Uvicorn's removed `Config.setup_event_loop()` API; the working approach uses Uvicorn's current loop-factory path with an explicit `SelectorEventLoop`, now kept in `scripts/serve.py`. A separate GET bug filtered the stored tool trace to hybrid attempts, so it could report a failed hybrid result after grep had succeeded; it now uses the genuinely last attempt, with missing vector/RRF scores remaining `null` for grep.

## Interview-ready summary (3-4 sentences)
The condensed version you'd actually say out loud if asked "tell me about this part
of the project." Write this last, once everything above is filled in.