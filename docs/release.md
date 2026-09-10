# Release process

The public distribution name is `fastapi-nacos-extension`; the unrelated
`fastapi-nacos` project remains untouched. A `v0.1.0` release is allowed only
when:

1. `pyproject.toml`, `fastapi_nacos_extension.__version__`, changelogs and tag agree.
2. Ruff, mypy, the full pytest suite and branch coverage of at least 85% pass.
3. The Python 3.8 baseline and the versioned FastAPI/SDK compatibility matrix pass.
4. wheel/sdist build, Twine metadata checks and archive content checks pass.
5. the wheel installs and imports in a clean virtual environment.

## One-time trusted publisher setup

Create a `pypi` environment in the GitHub repository. Configure a matching
Trusted Publisher on PyPI, or a Pending Publisher when the project does not
exist yet, with:

- Owner: `pumpkin-nbc`
- Repository: `Fastapi-Nacos-Extension`
- Workflow: `release.yml`
- Environment: `pypi`
- PyPI project name: `fastapi-nacos-extension` (Pending Publisher only)

No PyPI API token is stored in GitHub. Only the isolated PyPI publishing job
receives `id-token: write`; build and validation remain read-only. The workflow
does not expose a manual trigger.

## Production release

Merge the release commit into `master`, then create and push the exact version
tag, for example `v0.1.0`. The workflow requires the tagged commit to belong to
`master`, validates that the tag matches the declared version, rejects an
existing PyPI version, and publishes through Trusted Publishing. Only after
PyPI succeeds does it create the GitHub Release with the same wheel and sdist.
