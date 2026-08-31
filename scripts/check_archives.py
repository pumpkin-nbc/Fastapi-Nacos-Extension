"""Validate required files in the generated wheel and sdist."""

import tarfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"


def check_wheel(path: Path) -> None:
    with zipfile.ZipFile(str(path)) as archive:
        names = set(archive.namelist())
    required = {
        "fastapi_nacos/__init__.py",
        "fastapi_nacos/extension.py",
        "fastapi_nacos/py.typed",
    }
    missing = required - names
    if missing:
        raise SystemExit(f"wheel missing: {sorted(missing)}")
    if not any(name.endswith("/licenses/LICENSE") for name in names):
        raise SystemExit("wheel does not contain LICENSE")
    if not any(name.endswith("/licenses/NOTICE") for name in names):
        raise SystemExit("wheel does not contain NOTICE")


def check_sdist(path: Path) -> None:
    with tarfile.open(str(path), "r:gz") as archive:
        names = set(archive.getnames())
    required_suffixes = (
        "/fastapi_nacos/py.typed",
        "/README.md",
        "/README.zh-CN.md",
        "/LICENSE",
        "/NOTICE",
        "/examples/docker-compose-nacos.yml",
    )
    for suffix in required_suffixes:
        if not any(name.endswith(suffix) for name in names):
            raise SystemExit(f"sdist missing {suffix}")


def main() -> None:
    wheels = list(DIST.glob("fastapi_nacos-0.1.0-*.whl"))
    sdists = list(DIST.glob("fastapi_nacos-0.1.0.tar.gz"))
    if len(wheels) != 1 or len(sdists) != 1:
        raise SystemExit("expected exactly one 0.1.0 wheel and one sdist")
    check_wheel(wheels[0])
    check_sdist(sdists[0])
    print("archive contents verified")


if __name__ == "__main__":
    main()

