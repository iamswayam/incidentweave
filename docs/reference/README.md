# Reference documents

**As of 2026-11-04.**

| Document | Contents |
|---|---|
| [openapi.json](openapi.json) | Generated API schema, deterministic from `app.main.app.openapi()` with sorted JSON keys and a trailing newline. |
| [metrics.md](metrics.md) | Provisional v1 development retrieval and guard scorecard, with registered metrics, intervals, limits, and plans. |

The API schema can be regenerated without a database connection or provider key:

```powershell
.\.venv\Scripts\python.exe -m scripts.export_openapi
```

The unit test at `tests/unit/scripts/test_export_openapi.py` compares the committed schema to
the current generated result. Update the schema in the same change as an intentional API
contract change. The scorecard protocol defines the registered formulas and data rules.

Back to the [documentation status index](../README.md).
