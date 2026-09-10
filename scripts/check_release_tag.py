#!/usr/bin/env python
"""Require a release tag to exactly match the declared package version."""

import os
import re
import sys
from pathlib import Path
from typing import Optional

try:
    import tomllib
except ImportError:  # pragma: no cover - Python 3.8 compatibility
    import tomli as tomllib

ROOT = Path(__file__).resolve().parents[1]


def declared_version(root: Path = ROOT) -> str:
    project = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
    version = project["project"]["version"]
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
    return version


def validate_tag(tag: Optional[str], root: Path = ROOT) -> str:
    expected = "v" + declared_version(root)
    if tag != expected:
        raise ValueError(f"release tag must be {expected!r}, got {tag!r}")
    return expected


def main() -> int:
    tag = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("GITHUB_REF_NAME")
    try:
        expected = validate_tag(tag)
    except ValueError as exc:
        print(f"[check_release_tag] FAILED - {exc}", file=sys.stderr)
        return 1
    print(f"[check_release_tag] OK - {expected}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
