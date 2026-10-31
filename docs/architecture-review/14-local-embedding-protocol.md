# Local embedding-model comparison protocol (item 18c)

## Purpose and registration

Compare two locally run, open-weight embedding models against the current retrieval control
using development data only. This protocol is committed before any candidate vectors or
comparison results exist. It fixes the data, model calls, evaluator, metrics, and decision
rules. No outcome automatically changes production.

## Control

The control is current production hybrid retrieval:

- Gemini `models/gemini-embedding-001`, 768 dimensions, current default task type.
- S0 fixed 60/10 line chunks.
- Current 14c lexical behavior unchanged; no test-file downweighting or exclusion.
- Existing reciprocal-rank fusion, deterministic ordering, and evidence-guard threshold
  unchanged. The guard threshold is `0.5`.
- No test-file handling or other retrieval changes.

## Candidates and embedding calls

Each candidate is compared separately with the control. Only the embedding model and its
required vector dimension change.

| Candidate | FastEmbed model | Dimension | Model registry size | License |
|---|---|---:|---:|---|
| C1 | `jinaai/jina-embeddings-v2-base-code` | 768 | 0.64 GB | Apache-2.0 |
| C2 | `BAAI/bge-small-en-v1.5` | 384 | 0.067 GB | MIT |

Use the FastEmbed library, pinned to **`fastembed==0.9.1`** for this comparison. The
development environment's installed model registry reports the dimensions, license strings,
size values, and input truncation descriptions above. The registry descriptions say query and
document prefixes are not necessary for both selected models. Inspection of FastEmbed 0.9.1's
installed `TextEmbedding.passage_embed` and `TextEmbedding.query_embed` implementations,
the shared `TextEmbeddingBase` implementations, and the respective model classes confirms
that neither call adds a query/document prefix for these models: passage embedding delegates
to `embed`, and query embedding delegates to the model's query embedding implementation,
which uses the original input text. The experiment must therefore call the library's
document/passage method for chunks and query method for questions while passing exactly the
same text values used by the control, without adding or stripping instructions, prefixes, or
other text transformations.

The installed implementation inspected for this protocol is FastEmbed 0.9.1:
`fastembed/text/text_embedding.py`, `fastembed/text/text_embedding_base.py`,
`fastembed/text/onnx_embedding.py`, and
`fastembed/text/pooled_normalized_embedding.py`. Its model registry describes the Jina model
as English plus 30 programming languages with 8192-token truncation, and BGE-small as
English-only with 512-token truncation. These are registry facts, not independent performance
claims.

## Data and split boundary

Use the existing development split loader and fixtures only:

- 33 answerable and 15 unanswerable development questions across the three registered
  repositories.
- Embed every development chunk/document and all 48 development questions for each candidate,
  including unanswerable questions needed for guard checks.
- Text inputs are exactly the chunk and question strings used by the control.
- Do not read, embed, evaluate, or otherwise use any held-out question, label, retrieval
  result, or vector. Do not open baseline, results, or question files directly; use the
  existing manifest, fixture, and split-helper APIs.
- One rank change is approximately `0.015` pooled MRR; all tolerances are expressed in whole
  questions.

## Isolation and evaluator equivalence gate

The production `chunks.embedding` column remains 768 dimensions and is **never written** by
this experiment. Candidate document and query vectors are stored only under the ignored,
versioned path `evaluation/cache/local_embedding_v1/<model-slug>/`. Cache identity and its
metadata must label every vector with the experiment/cache version, `embedding_model`,
dimension, FastEmbed version, vector role (document or query), and a hash of the exact input
text. Validate dimensions, numeric values, and finiteness before accepting a cache entry.
Candidate vectors must never be mixed across models, dimensions, or library versions.

Use a separate exact in-memory cosine index for each model. Do not create or alter a
production table, vector column, migration, or schema. For each question, combine the
candidate model's vector ranking with the unchanged PostgreSQL lexical branch and apply the
control's RRF settings, deterministic tie rules, top-k, and guard threshold. The control
vectors must pass through this same evaluator and lexical branch before candidate results
count. Reconcile the evaluator's 33 answerable per-question control ranks with the committed
development baseline and require **33/33 exact per-question agreement**. If the gate fails,
stop before evaluating either candidate and report the mismatch without changing protocol
rules.

The `plan` command prints exact development-only counts and cache-miss counts without
downloading models. The `embed` command downloads each model at most once and creates only
development vectors. The cache-only `evaluate` command reads only validated cached vectors,
uses the local evaluation database for the lexical branch, performs the control-equivalence
gate, and then evaluates candidates. Model download is the only network need; inference and
retrieval are local/offline. Do not call provider APIs.

## Metrics and guard reporting

For each model and the control, report pooled and per-repository answerable MRR and Hit@1,
Hit@3, and Hit@5. Also report per-model vector-distance distributions for answerable and
unanswerable questions, embedding time per chunk and per query on this CPU, model size,
dimension, license, test-file share of the top five, and the unchanged guard's decisions on
all unanswerable questions.

Cosine-distance distributions are model-specific and are **not comparable across models**.
The `0.5` guard threshold was calibrated to the Gemini control; it is deliberately not
recalibrated for either candidate in this experiment. Report development ordinals only for
guard decisions that differ; do not report question text or identifiers.

Use paired bootstrap resampling over the 33 question-level reciprocal-rank differences,
seed `20261031`, 10,000 resamples, 95% interval with linear interpolation. Report the exact
two-sided sign test descriptively only; it is not part of the decision.

## Registered retention rules

Each candidate is assessed independently. Retain a candidate only if all four rules pass:

| Rule | Retention condition |
|---|---|
| R1 | Pooled MRR over the 33 answerable development questions improves by at least `0.03` versus control. |
| R2 | The paired-bootstrap 95% interval lower bound for pooled MRR difference is above `0`. |
| R3 | In each repository, answerable Hit@5 successes do not decrease (tolerance: 0 questions). |
| R4 | In each repository, guard decisions for the 15 unanswerable questions are unchanged or improved with the unchanged threshold `0.5`. |

There is **no R5**. The exact sign test is descriptive only.

Apply these outcome classes without modification:

1. If all of R1-R4 pass: **"candidate: needs a separately registered held-out validation, a
   per-model guard threshold under item 3b, and a production migration plan before any
   adoption"**.
2. If R1-R3 pass and R4 fails: **"retrieval-promising; guard needs per-model recalibration;
   control kept"**.
3. Otherwise: **"keep control"**.

The two candidates are two comparisons without multiplicity correction. A pass nominates a
candidate only; it does not authorize or automatically perform adoption. No held-out
selection, threshold tuning, or post-result rule change is permitted.

## Hard boundaries

- Never enable automatic cross-model fallback: vectors from distinct embedding models are
  incomparable.
- Do not change production embeddings, schema, chunking, lexical retrieval, baselines, gates,
  or evaluation manifest.
- Do not write candidate vectors to the production vector column or mix candidate caches.
- The result is development-only and cannot establish general model quality.

## Reproduction and outputs

The implementation provides `plan`, `embed`, and `evaluate` commands. Run each once in that
order. `plan` has no model download; `embed` downloads each selected model once and embeds
only development inputs; `evaluate` is cache-only. Evaluation writes aggregate-only JSON
under the ignored cache and a reviewed, aggregate-only note at
`docs/notes/18-local-embedding-results.md`. Never commit model files, vector caches, detailed
question results, or other run outputs.

The result note reports the R1-R4 table and outcome class per candidate; per-repository and
pooled retrieval metrics; paired intervals and descriptive sign tests; model-specific vector
distance distributions; embedding timings; model footprint, dimensions and license; network
requirements; top-five test-file share; and these limits: 33 answerable questions, 15
unanswerable questions, three small single-author repositories, unvalidated model-specific
guard thresholds, and no held-out evaluation.
