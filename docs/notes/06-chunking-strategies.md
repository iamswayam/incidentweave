# Chunking strategies

This note describes the deterministic candidate chunk specifications added for item 15a-1.
They are comparison inputs only; production ingestion and evaluation runners do not use them yet.

## Candidates

- **S0 (`s0_lines_60_10`)**: current 60-line windows with 10 lines of overlap.
- **S1 (`s1_lines_100_20`)**: 100-line windows with 20 lines of overlap.
- **S2 (`s2_ast_v1`)**: Python AST-aware units with raw source as embedding text.
- **S3 (`s3_ast_v1_embed_text`)**: the same chunk specifications as S2, but adds the file path
  and available symbol name to the text sent to the embedding model. Stored source remains raw.

## ast-v1 rules

1. Top-level functions and direct methods of top-level classes are separate units; decorators are
   included, and nested definitions remain with their enclosing unit.
2. Code outside those definitions forms module or class-body gap units.
3. Units longer than 80 lines are split into 60/10 windows within their original range.
4. Adjacent unsplit units merge greedily when either is under 8 lines and their combined range is
   at most 80 lines.
5. Blank-only units are omitted; source that fails AST parsing falls back to 60/10 line windows.
6. Chunk ranges are 1-based and inclusive, and S3 enrichment never changes stored content.

These candidates have no database repository name and make no provider calls. Fixtures, runner
wiring, and production ingestion changes are **not** part of this foundation step. Candidate
parameters are frozen before the experiment; changing them requires a new protocol version in
[the chunking comparison plan](../architecture-review/07-chunking-comparison-plan.md).
