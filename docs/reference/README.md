# Generated API reference

**As of 2026-11-01.**

[`openapi.json`](openapi.json) is generated deterministically from
`app.main.app.openapi()` with sorted JSON object keys and a trailing newline. It can be
regenerated without a database connection or provider key:

```powershell
.\.venv\Scripts\python.exe -m scripts.export_openapi
```

The unit test at `tests/unit/scripts/test_export_openapi.py` compares the committed schema to
the current generated result. Update the schema in the same change as an intentional API
contract change.

Back to the [documentation status index](../README.md).
