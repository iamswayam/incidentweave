# Repository evaluation data

Back to the [evaluation guide](../README.md).

## Candidate composition

Measurements are at the pinned default-branch commit as of 2026-11-02. Candidates are not evaluation repositories until item 31 adds their questions.

| ID | Role | Pinned SHA / date | SPDX | Copyright holder | Python lines (source / all / indexed) | Issues (count / method) | Fixture estimate (chunks / bytes / location) |
|---|---|---|---|---|---:|---|---|
| `rq` | development | `1cf2c3eab33a8eda95c6107720dc40c7e285dd2b` / 2026-10-28 | BSD-2-Clause | Copyright 2012 Vincent Driessen. All rights reserved. | 13,300 / 29,625 / 29,625 | 109 / gh | 625 / 2,816,220 / release |
| `kopf` | development | `edaf7c634ed66153143da467b80d212c0601479b` / 2026-10-30 | MIT | Copyright (c) 2020-2025 Sergey Vasilyev <nolar@nolar.info> | 18,044 / 48,357 / 48,357 | 59 / gh | 1,065 / 4,798,838 / release |
| `luigi` | development (replaces `apscheduler`) | `f5feb7a4655ad73ef56f0ab04d7903ab43b63e12` / 2026-10-07 | Apache-2.0 | Copyright 2012-2021 Spotify AB | 29,592 / 62,936 / 62,936 | 43 / gh | 1,336 / 6,019,951 / release |
| `client_python` | development | `e2f2bf9dcb49b8e8c0bc7fc089ff550edd9d286d` / 2026-10-30 | Apache-2.0 | Not stated in LICENSE | 5,429 / 11,558 / 11,558 | 45 / gh | 246 / 1,108,464 / committed |
| `locust` | held_out | `d67bfacd96e83e70a95c23ac7b5da4ec7c61ae90` / 2026-11-01 | MIT | Copyright (c) 2009-2026, Carl Byström, Jonatan Heyman, Lars Holmberg | 12,663 / 35,905 / 35,905 | 119 / gh | 770 / 3,469,583 / release |
| `docker_py` | held_out | `e734fd5a5508bc1062a28a51dc2f31ae47af7a2f` / 2026-10-28 | Apache-2.0 | Copyright 2016 Docker, Inc. | 14,216 / 31,502 / 31,502 | 82 / gh | 682 / 3,073,059 / release |
| `uvicorn` | held_out | `a99c1b76ee9caea67ff98e2ccc457bd372db193f` / 2026-11-01 | BSD-3-Clause | Copyright © 2017-present, [Encode OSS Ltd](https://www.encode.io/). | 7,478 / 16,818 / 16,818 | 116 / gh | 366 / 1,649,179 / release |

## Qualified backups (unused)

None. `luigi` replaced `apscheduler`; `huey` did not meet the issue-count threshold.

## Verification

GitHub CLI query on 2026-11-02: merged pull requests, with `closingIssuesReferences`, merged on or before the pinned commit date, and at least one non-test source `.py` file. The query used `--limit 1000`; counts are conservative lower bounds over the most recent merged pull requests.

`apscheduler` had 17 qualifying issues and was replaced by `luigi` (43). `huey` had 4 and did not qualify. No query errors remained after retry.

## Attribution

| Repository | License and copyright holder | Upstream license at pinned commit |
|---|---|---|
| `rq/rq` | BSD-2-Clause; Copyright 2012 Vincent Driessen. All rights reserved. | [LICENSE](https://github.com/rq/rq/blob/1cf2c3eab33a8eda95c6107720dc40c7e285dd2b/LICENSE) |
| `nolar/kopf` | MIT; Copyright (c) 2020-2025 Sergey Vasilyev | [LICENSE](https://github.com/nolar/kopf/blob/edaf7c634ed66153143da467b80d212c0601479b/LICENSE) |
| `spotify/luigi` | Apache-2.0; Copyright 2012-2021 Spotify AB | [LICENSE](https://github.com/spotify/luigi/blob/f5feb7a4655ad73ef56f0ab04d7903ab43b63e12/LICENSE) |
| `prometheus/client_python` | Apache-2.0; no copyright-holder line in LICENSE | [LICENSE](https://github.com/prometheus/client_python/blob/e2f2bf9dcb49b8e8c0bc7fc089ff550edd9d286d/LICENSE) |
| `locustio/locust` | MIT; Copyright (c) 2009-2026, Carl Byström, Jonatan Heyman, Lars Holmberg | [LICENSE](https://github.com/locustio/locust/blob/d67bfacd96e83e70a95c23ac7b5da4ec7c61ae90/LICENSE) |
| `docker/docker-py` | Apache-2.0; Copyright 2016 Docker, Inc. | [LICENSE](https://github.com/docker/docker-py/blob/e734fd5a5508bc1062a28a51dc2f31ae47af7a2f/LICENSE) |
| `encode/uvicorn` | BSD-3-Clause; Copyright © 2017-present, Encode OSS Ltd. | [LICENSE.md](https://github.com/encode/uvicorn/blob/a99c1b76ee9caea67ff98e2ccc457bd372db193f/LICENSE.md) |

Backups assessed: `huey` (MIT, 4 issues; did not qualify) and `luigi` (Apache-2.0, 43 issues; selected to replace `apscheduler`).

## Qualification method

- Source lines exclude paths containing `tests`, `test`, `testing`, `docs`, `doc`, `examples`, or `example`, and files named `test_*.py`, `*_test.py`, or `conftest.py`. All Python lines include the full tree.
- Indexed lines and chunks use `scripts.ingest_repo.iter_python_files` and the registered S0 60/10 chunker; no embeddings are computed.
- Issue counts use distinct GitHub `closingIssuesReferences` from merged PRs that touch non-test source Python files by the pinned commit date.
- The GitHub CLI query is capped at the 1,000 most recent merged PRs; its issue counts are conservative lower bounds.
- Fixture bytes = candidate chunk count × median compressed bytes per chunk from the three v1 fixtures × 1.2 for query vectors. The median rate was 3,754.96 bytes/chunk; estimates at or below 1,572,864 bytes are `committed`, otherwise `release`. No candidate fixture was built.

## Changelog

| Date | Change |
|---|---|
| 2026-11-02 | Issue counts verified with gh; the split was restored to protocol 15 except `apscheduler`, replaced by `luigi` after 17 issues. `huey` did not qualify at 4 issues. The query limit is 1,000 merged PRs; no fixture was built. |
