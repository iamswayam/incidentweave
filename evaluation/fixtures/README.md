# Evaluation fixtures

Back to the [evaluation guide](../README.md).

`retrieval_fixture.json.gz` is the shared IncidentWeave retrieval fixture. It contains pinned source chunks and question embeddings for offline retrieval evaluation.

The IncidentWeave entry in [`../manifest.json`](../manifest.json) selects this file and records its SHA-256 pin and compressed-size limit. The manifest validator checks the path, hash, and fixture metadata.

Use the [offline retrieval note](../../docs/notes/04-offline-retrieval-evaluation.md) for fixture construction details. Building a fixture requires the evaluation database and existing cached embeddings; it does not fetch embeddings.
