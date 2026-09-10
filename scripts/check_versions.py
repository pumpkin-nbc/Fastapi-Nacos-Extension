"""Fail when release version declarations disagree."""

import os
from pathlib import Path

from check_release_tag import declared_version

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    declared = declared_version(ROOT)
    for changelog in ("CHANGELOG.md", "CHANGELOG.zh-CN.md"):
        if declared not in (ROOT / changelog).read_text(encoding="utf-8"):
            raise SystemExit(f"{changelog} does not mention {declared}")

    tag = os.getenv("GITHUB_REF_NAME")
    if tag and tag.startswith("v") and tag != "v" + declared:
        raise SystemExit(f"tag {tag!r} does not match v{declared}")
    print(f"version declarations agree: {declared}")


if __name__ == "__main__":
    main()
