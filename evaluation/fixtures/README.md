# Evaluation fixtures

Back to the [evaluation guide](../README.md).

IncidentWeave's manifest-selected retrieval fixture is now
[`../repos/incidentweave/retrieval_fixture.json.gz`](../repos/incidentweave/retrieval_fixture.json.gz).
This directory remains as a navigation stub for references in frozen historical notes.

The IncidentWeave entry in [`../manifest.json`](../manifest.json) selects the moved file and records its SHA-256 pin and compressed-size limit. The manifest validator checks the path, hash, and fixture metadata.

Use the [offline retrieval note](../../docs/notes/04-offline-retrieval-evaluation.md) for fixture construction details. Building a fixture requires the evaluation database and existing cached embeddings; it does not fetch embeddings.
