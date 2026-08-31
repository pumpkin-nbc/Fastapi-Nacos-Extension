"""Fail when release version declarations disagree."""

import os
from pathlib import Path

import tomli

from fastapi_nacos_extension import __version__

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    project = tomli.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    declared = project["project"]["version"]
    if declared != __version__:
        raise SystemExit(
            f"version mismatch: pyproject={declared!r}, package={__version__!r}"
        )
    for changelog in ("CHANGELOG.md", "CHANGELOG.zh-CN.md"):
        if declared not in (ROOT / changelog).read_text(encoding="utf-8"):
            raise SystemExit(f"{changelog} does not mention {declared}")

    tag = os.getenv("GITHUB_REF_NAME")
    if tag and tag.startswith("v") and tag != "v" + declared:
        raise SystemExit(f"tag {tag!r} does not match v{declared}")
    print(f"version declarations agree: {declared}")


if __name__ == "__main__":
    main()
