# Repository evaluation data

Back to the [evaluation guide](../README.md).

## Candidate composition

Measurements are at the pinned default-branch commit as of 2026-11-02. These candidates are not evaluation repositories until item 31 adds their questions.

| ID | Role | Pinned SHA / date | SPDX | Copyright holder | Python lines (source / all / indexed) | Issues (count / method) | Fixture estimate (chunks / bytes / location) |
|---|---|---|---|---|---:|---|---|
| `rq` | development | `1cf2c3eab33a8eda95c6107720dc40c7e285dd2b` / 2026-10-28 | BSD-2-Clause | Copyright 2012 Vincent Driessen. All rights reserved. | 13,300 / 29,625 / 29,625 | 73 / git-closing-keywords | 625 / 2,816,220 / release |
| `huey` | development (replaces `kopf`) | `5aba8d35a2504a35be46d39734d02eebb1471c62` / 2026-11-01 | MIT | Copyright (c) 2017 Charles Leifer | 6,749 / 14,254 / 14,231 | 65 / git-closing-keywords | 309 / 1,392,339 / committed |
| `apscheduler` | development | `05b4e2d69f89e3f8d87c6eec5df71ed1dd5705ec` / 2026-10-26 | MIT | Copyright (c) 2009 Alex Grönholm | 8,718 / 13,754 / 13,754 | 65 / git-closing-keywords | 297 / 1,338,268 / committed |
| `luigi` | development (replaces `client_python`) | `f5feb7a4655ad73ef56f0ab04d7903ab43b63e12` / 2026-10-07 | Apache-2.0 | Copyright 2012-2021 Spotify AB | 29,592 / 62,936 / 62,936 | 51 / git-closing-keywords | 1,336 / 6,019,951 / release |
| `locust` | held_out | `d67bfacd96e83e70a95c23ac7b5da4ec7c61ae90` / 2026-11-01 | MIT | Copyright (c) 2009-2026, Carl Byström, Jonatan Heyman, Lars Holmberg | 12,663 / 35,905 / 35,905 | 91 / git-closing-keywords | 770 / 3,469,583 / release |
| `docker_py` | held_out | `e734fd5a5508bc1062a28a51dc2f31ae47af7a2f` / 2026-10-28 | Apache-2.0 | Copyright 2016 Docker, Inc. | 14,216 / 31,502 / 31,502 | 68 / git-closing-keywords | 682 / 3,073,059 / release |

## Pending issue verification

Repositories below 40 Git-history proxy issues are excluded from manifest candidates. `gh` was unavailable, so no GitHub verification was possible.

| ID | Role | Pinned SHA / date | SPDX | Python lines (source / all / indexed) | Issues | Status |
|---|---|---|---|---:|---:|---|
| `kopf` | development | `edaf7c634ed66153143da467b80d212c0601479b` / 2026-10-30 | MIT | 18,044 / 48,357 / 48,357 | 2 | Replaced by `huey`; pending verification |
| `client_python` | development | `e2f2bf9dcb49b8e8c0bc7fc089ff550edd9d286d` / 2026-10-30 | Apache-2.0 | 5,429 / 11,558 / 11,558 | 17 | Replaced by `luigi`; pending verification |
| `uvicorn` | held_out | `a99c1b76ee9caea67ff98e2ccc457bd372db193f` / 2026-11-01 | BSD-3-Clause | 7,478 / 16,818 / 16,818 | 10 | Pending verification; excluded from manifest candidates |

`structlog` was rejected because its license text did not match a supported SPDX identifier. `flower` was rejected at 4,398 source Python lines, below the 5,000-line minimum. Backup order was `structlog`, `huey`, `flower`, `luigi`.

## Attribution

| Repository | License and copyright holder | Upstream license at pinned commit |
|---|---|---|
| `rq/rq` | BSD-2-Clause; Copyright 2012 Vincent Driessen. All rights reserved. | [LICENSE](https://github.com/rq/rq/blob/1cf2c3eab33a8eda95c6107720dc40c7e285dd2b/LICENSE) |
| `coleifer/huey` | MIT; Copyright (c) 2017 Charles Leifer | [LICENSE](https://github.com/coleifer/huey/blob/5aba8d35a2504a35be46d39734d02eebb1471c62/LICENSE) |
| `agronholm/apscheduler` | MIT; Copyright (c) 2009 Alex Grönholm | [LICENSE](https://github.com/agronholm/apscheduler/blob/05b4e2d69f89e3f8d87c6eec5df71ed1dd5705ec/LICENSE) |
| `spotify/luigi` | Apache-2.0; Copyright 2012-2021 Spotify AB | [LICENSE](https://github.com/spotify/luigi/blob/f5feb7a4655ad73ef56f0ab04d7903ab43b63e12/LICENSE) |
| `locustio/locust` | MIT; Copyright (c) 2009-2026, Carl Byström, Jonatan Heyman, Lars Holmberg | [LICENSE](https://github.com/locustio/locust/blob/d67bfacd96e83e70a95c23ac7b5da4ec7c61ae90/LICENSE) |
| `docker/docker-py` | Apache-2.0; Copyright 2016 Docker, Inc. | [LICENSE](https://github.com/docker/docker-py/blob/e734fd5a5508bc1062a28a51dc2f31ae47af7a2f/LICENSE) |
| `nolar/kopf` | MIT; Copyright (c) 2020-2025 Sergey Vasilyev | [LICENSE](https://github.com/nolar/kopf/blob/edaf7c634ed66153143da467b80d212c0601479b/LICENSE) |
| `prometheus/client_python` | Apache-2.0; no copyright-holder line in LICENSE | [LICENSE](https://github.com/prometheus/client_python/blob/e2f2bf9dcb49b8e8c0bc7fc089ff550edd9d286d/LICENSE) |
| `encode/uvicorn` | BSD-3-Clause; Copyright © 2017-present, Encode OSS Ltd. | [LICENSE.md](https://github.com/encode/uvicorn/blob/a99c1b76ee9caea67ff98e2ccc457bd372db193f/LICENSE.md) |

The `rq` BSD-2-Clause license has two numbered conditions; `uvicorn` BSD-3-Clause has three bulleted conditions.

## Qualification method

- Source lines exclude paths containing `tests`, `test`, `testing`, `docs`, `doc`, `examples`, or `example`, and files named `test_*.py`, `*_test.py`, or `conftest.py`. All Python lines include the full tree.
- Indexed lines and chunks use `scripts.ingest_repo.iter_python_files` and the registered S0 60/10 chunker; no embeddings are computed.
- Issue counts are distinct closing-keyword references in commits that change a non-test source `.py` file. This Git-history proxy approximates closed issues with merged linked PRs; records below 40 are pending if GitHub CLI verification is unavailable.
- Commits are the latest default-branch commits measured on 2026-11-02; qualification requires commit dates within 12 months. Candidate pins are immutable.
- Fixture bytes = candidate chunk count × median compressed bytes per chunk from the three v1 fixtures × 1.2 for query vectors. The median rate was 3,754.96 bytes/chunk; estimates at or below 1,572,864 bytes are `committed`, otherwise `release`. No candidate fixture was built.

## Changelog

| Date | Change |
|---|---|
| 2026-11-02 | Candidates qualified and pinned. `kopf` was replaced by `huey`; `client_python` was replaced by `luigi`. `uvicorn` remains pending issue verification and is excluded from manifest candidates. `structlog` and `flower` failed qualification; no fixture was built. |
