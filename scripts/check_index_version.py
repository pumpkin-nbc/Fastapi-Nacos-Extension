#!/usr/bin/env python
"""Fail when the release version already exists on PyPI or TestPyPI."""

import argparse
import re
import sys
from pathlib import Path
from typing import Tuple
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

try:
    import tomllib
except ImportError:  # pragma: no cover - Python 3.8 compatibility
    import tomli as tomllib

ROOT = Path(__file__).resolve().parents[1]
INDEXES = {
    "pypi": "https://pypi.org",
    "testpypi": "https://test.pypi.org",
}


def release_identity(root: Path = ROOT) -> Tuple[str, str]:
    project = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    name = project["name"]
    version = project["version"]
    package_text = (root / "fastapi_nacos_extension" / "__init__.py").read_text(
        encoding="utf-8"
    )
    match = re.search(r'^__version__\s*=\s*"([^"]+)"', package_text, re.MULTILINE)
    if not match:
        raise ValueError("could not read package version")
    package_version = match.group(1)
    if version != package_version:
        raise ValueError(
            f"version mismatch: pyproject={version!r}, package={package_version!r}"
        )
    return name, version


def ensure_version_available(index: str) -> Tuple[str, str]:
    name, version = release_identity()
    url = f"{INDEXES[index]}/pypi/{name}/{version}/json"
    try:
        response = urlopen(url, timeout=15)
    except HTTPError as exc:
        if exc.code == 404:
            return name, version
        raise RuntimeError(f"index preflight returned HTTP {exc.code}") from exc
    except (URLError, TimeoutError) as exc:
        reason = getattr(exc, "reason", str(exc))
        raise RuntimeError(f"index preflight failed: {reason}") from exc
    else:
        response.close()
        raise ValueError(f"{name}=={version} already exists on {index}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("index", choices=sorted(INDEXES))
    args = parser.parse_args()
    try:
        name, version = ensure_version_available(args.index)
    except (RuntimeError, ValueError) as exc:
        print(f"[check_index_version] FAILED - {exc}", file=sys.stderr)
        return 1
    print(f"[check_index_version] OK - {name}=={version} is available on {args.index}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
