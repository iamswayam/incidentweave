# End-to-end checks

Follow the registered [item 34 protocol](../architecture-review/17-end-to-end-protocol.md).
The `run` command uses only manifest-assigned development questions and requires Docker-backed
PostgreSQL, an ingested repository, and a Gemini API key. It performs three temperature-0
investigations per question and stores the run set under `evaluation/experiments/end-to-end/`.

```powershell
.\.venv\Scripts\python.exe -m scripts.run_end_to_end run --repository <id> --questions evaluation/repos/<repo>/questions.json
```

Generate reports from saved run sets without a database or provider key:

```powershell
.\.venv\Scripts\python.exe -m scripts.run_end_to_end report evaluation/experiments/end-to-end/ --out-md <report.md> --out-json <summary.json>
```

Use `--limit N` for a small development trial. The report command is deterministic unless an
explicit `--generated-at` value is supplied.
