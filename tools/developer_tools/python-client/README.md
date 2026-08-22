# BELY python client

A [uv workspace](https://docs.astral.sh/uv/concepts/projects/workspaces/) with one
publishable package:

- `packages/api/` — **bely-api**: the generated `belyApi` REST client plus the
  hand-written `BelyApiFactory` convenience wrapper.

`belyApi/` is **generated** by `generatePyClient.sh` from the portal's OpenAPI spec and is
gitignored — regenerate it before building, testing, or running anything that imports it.

## Dev setup

```sh
source setup.sh                       # from the repo root; puts packages/api on PYTHONPATH
cd tools/developer_tools/python-client
./generatePyClient.sh http://localhost:8080/bely   # requires the portal running locally
```

At this point `import belyApi` and `import BelyApiFactory` resolve directly against this
checkout via `PYTHONPATH` — no install required.

If you'd rather use uv directly (editable install into a real virtualenv):

```sh
uv sync                               # installs bely-api editable + dev deps (pytest)
uv run pytest test/
```

## Regenerating the client

```sh
./generatePyClient.sh <BELY_BASE_PATH>     # e.g. http://localhost:8080/bely
```

Downloads `openapi-generator-cli` (once — cached for subsequent runs), generates a client
from `<BELY_BASE_PATH>/api/openapi.yaml`, and overwrites `packages/api/belyApi/`. Run this
any time REST routes or `openapi.yaml` change.

## Building & publishing to PyPI

```sh
uv build --package bely-api --out-dir dist   # sdist + wheel
uv publish dist/*                            # needs UV_PUBLISH_TOKEN or ~/.pypirc
```

Or use the wrapper script, which also regenerates `belyApi` first and prompts before uploading:

```sh
./sbin/bely_release_pip.py api                                        # from repo root
./sbin/bely_release_pip.py api --dry-run                              # build only
./sbin/bely_release_pip.py api --publish-url https://test.pypi.org/legacy/  # TestPyPI
```

or `make release-python-client` from the repo root (publishes `bely-api`, `bely-cli`,
and `bely-mqtt-framework`).

`make prepare-release` (`sbin/bely_prepare_release.py`) bumps the version in
`packages/api/pyproject.toml` (and everywhere else version strings live) and refreshes
`uv.lock`.

## Building conda packages

```sh
./conda-build.sh http://localhost:8080/bely
```

Regenerates the client, builds `conda-recipe/API`, smoke-tests it in a throwaway env, and
prints a reminder to upload the resulting `bely-api-env.txt` with the c2 tool.

## Tests

```sh
uv run pytest test/          # requires the portal running on localhost:8080
```

`sbin/cdb_test.sh` (invoked by `make test`) regenerates the client and runs this as part of
the full suite.
