# Retrieval inspection report

Item 13c adds offline per-question Markdown cards and a per-repository summary from committed retrieval fixtures. Run `.\.venv\Scripts\python.exe -m scripts.inspect_retrieval`; files are written to `evaluation/inspection/<repo>/<strategy>-<split>.md` and `evaluation/inspection/<repo>/summary-<split>.md`.

Read each card by checking the evidence span, whether any top-five result overlaps it, the rank and vector/text/fusion scores, and the provisional guard decision. Ask: Was the evidence retrieved at all? Was it ranked first? Was a similar distractor ranked above it?

Limits: reports are offline from committed fixtures and use the development split by default. Single-line labels can make a hit or miss look luckier or harsher than it is. The guard threshold is provisional.

## Example HIT (batch-processing-service, S0, development)

````markdown
### direct-01 | direct | HIT at rank 1

**Question:** How does claim_pending_items prevent two workers from claiming the same item?

**Evidence needed:**
- `app/worker/engine.py:42-54` (13 lines)
```text
42 |         .with_for_update(of=BatchItem, skip_locked=True)
43 |     )
44 |     rows = result.all()  # list of Row(BatchItem, tenant_id)
45 | 
46 |     if not rows:
47 |         return []
48 | 
49 |     item_ids = [row[0].id for row in rows]
```

**Top 5 retrieved**

| # | Overlaps evidence | File:lines | Lines | Starts with | Vector distance | Text score | Fusion score |
|---:|---|---|---:|---|---:|---:|---:|
| 1 | yes | app/worker/engine.py:1-60 | 60 | import asyncio | 0.291 |  | 0.0164 |
| 2 | yes | app/worker/engine.py:51-110 | 60 | update(BatchItem) | 0.304 |  | 0.0161 |
| 3 | no | tests/test_worker.py:51-110 | 60 | async def test_claim_pending_items_returns_tenant_id(db: Asy... | 0.307 |  | 0.0159 |
| 4 | no | tests/test_worker.py:1-60 | 60 | """ | 0.311 |  | 0.0156 |
| 5 | no | app/worker/engine.py:101-160 | 60 | logger.warning("Lost lease before vendor call, skipping: ite... | 0.338 |  | 0.0154 |

**Guard (provisional threshold 0.5):** would answer; best vector distance: 0.291.
````

## Example MISS (batch-processing-service, S0, development)

````markdown
### direct-02 | direct | MISS

**Question:** What does derive_batch_status return when every item is either done or failed?

**Evidence needed:**
- `app/api/routes.py:46-47` (2 lines)
```text
46 |     if done + failed == total:
47 |         return "completed" if failed == 0 else "partially_failed"
```

**Top 5 retrieved**

| # | Overlaps evidence | File:lines | Lines | Starts with | Vector distance | Text score | Fusion score |
|---:|---|---|---:|---|---:|---:|---:|
| 1 | no | app/api/routes.py:151-210 | 60 | status = derive_batch_status(total, done, failed, in_progres... | 0.275 | 0.500 | 0.0325 |
| 2 | no | app/worker/engine.py:101-160 | 60 | logger.warning("Lost lease before vendor call, skipping: ite... | 0.309 | 0.500 | 0.0320 |
| 3 | no | tests/test_worker.py:151-210 | 60 | batch_id = await _create_batch_with_items(db, "tenant-partia... | 0.293 | 0.500 | 0.0313 |
| 4 | no | app/api/routes.py:101-160 | 60 | # (tenant_id, idempotency_key) committed first. Re-run the e... | 0.322 | 0.500 | 0.0313 |
| 5 | no | tests/test_worker.py:101-160 | 60 | future_lease = datetime.now(timezone.utc) + timedelta(second... | 0.281 |  | 0.0161 |

**Guard (provisional threshold 0.5):** would answer; best vector distance: 0.275.

**Why it missed (fill in by hand):** ______
````
