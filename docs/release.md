# Release process

The public distribution name is `fastapi-nacos-extension`; the unrelated
`fastapi-nacos` project remains untouched. A `v0.1.0` release is allowed only
when:

1. `pyproject.toml`, `fastapi_nacos_extension.__version__`, changelogs and tag agree.
2. Ruff, mypy, the full pytest suite and branch coverage of at least 85% pass.
3. FastAPI and SDK compatibility matrix jobs pass on Python 3.8.
4. wheel/sdist build, Twine metadata checks and archive content checks pass.
5. the wheel installs and imports in a clean virtual environment.

The release workflow attaches `fastapi_nacos_extension-0.1.0-py3-none-any.whl`
and the sdist to GitHub Release. Public PyPI upload is not enabled until a
Trusted Publisher for `fastapi-nacos-extension` is configured explicitly.
