"""Vendors the hosts kit of ``@silverpoint/embed`` X.Y.Z into ``src/silverpoint/_vendor/`` (PY-DD-02).

    uv run python scripts/vendor.py 0.11.0               # from the GitHub release vX.Y.Z (hosts kit)
    uv run python scripts/vendor.py --from PATH          # from a silverpoint checkout, after `pnpm build`
    uv run python scripts/vendor.py --check              # verify the checked-in files (CI)

Every script is verified against ``integrity.json`` (SHA-384) before anything is written, and the host
catalog's version must equal the scripts' version. ``props.json`` is derived here from the engine: the
props ``validateSpec`` takes per chart, wider than the host catalog's options (issue #2).
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import io
import json
import re
import shutil
import sys
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VENDOR = ROOT / "src" / "silverpoint" / "_vendor"
# Django finds static files in an app's static/ folder: a copy of the script, kept equal by this script.
DJANGO_STATIC = (
    ROOT
    / "src"
    / "silverpoint"
    / "contrib"
    / "django"
    / "static"
    / "silverpoint"
    / "silverpoint-embed.full.js"
)
SCRIPTS = ("silverpoint-embed.full.js", "silverpoint-embed.full.mjs")
DATA = ("host-catalog.json", "conformance.json", "integrity.json")
RELEASE = (
    "https://github.com/ecrespo/silverpoint/releases/download/v{version}/silverpoint-hosts-kit-{version}.zip"
)
BANNER = re.compile(r"@silverpoint/embed (\d+\.\d+\.\d+(?:-[\w.]+)?)")


def sri(data: bytes) -> str:
    return "sha384-" + base64.b64encode(hashlib.sha384(data).digest()).decode()


# The fields of a spec that `validateSpec` refuses inside `props` (the package takes them as arguments).
SPEC_FIELDS = ("data", "width", "height", "id", "ground", "substrate", "mode", "palette")
JS_STRINGS = r'\[(?:"[A-Za-z0-9_-]+",?)*\]'


def engine_props(script: str, catalog: dict) -> dict:
    """The props ``validateSpec`` takes for each chart, read from the engine's own tables (issue #2).

    The host catalog declares a chart's *options*; the engine also takes the chart's other props
    (``names``, ``nodes``) and a common set wider than the catalog's ``common``. Neither table is
    exported, so they are found by content, not by their minified names: the one object literal keyed
    by exactly the catalog's slugs, and the one string array holding every common option.
    """
    slugs = {c["slug"] for c in catalog["charts"]}
    tables = []
    for match in re.finditer(
        r'\{"[a-z0-9-]+":' + JS_STRINGS + r'(?:,"[a-z0-9-]+":' + JS_STRINGS + r")*\}", script
    ):
        table = json.loads(match.group(0))
        if set(table) == slugs:
            tables.append(table)
    common_names = {o["name"] for o in catalog["common"]}
    commons = [
        names
        for match in re.finditer(JS_STRINGS, script)
        if common_names <= set(names := json.loads(match.group(0))) and "data" in names
    ]
    if len(tables) != 1 or len(commons) != 1:
        raise ValueError(
            f"the engine's prop tables are not found unambiguously ({len(tables)} chart tables, "
            f"{len(commons)} common lists)"
        )
    return {
        "common": [n for n in commons[0] if n not in SPEC_FIELDS],
        "charts": {c["slug"]: tables[0][c["slug"]] for c in catalog["charts"]},
    }


def write_props(folder: Path) -> None:
    catalog = json.loads((folder / "host-catalog.json").read_text(encoding="utf-8"))
    props = engine_props((folder / SCRIPTS[1]).read_text(encoding="utf-8"), catalog)
    (folder / "props.json").write_text(json.dumps(props, indent=1) + "\n", encoding="utf-8")


def verify(folder: Path) -> list[str]:
    """Problems with a vendored folder: digests, versions, the files a wheel needs."""
    problems = []
    integrity = json.loads((folder / "integrity.json").read_text(encoding="utf-8"))
    catalog = json.loads((folder / "host-catalog.json").read_text(encoding="utf-8"))
    kit = json.loads((folder / "conformance.json").read_text(encoding="utf-8"))
    for name in SCRIPTS:
        data = (folder / name).read_bytes()
        if integrity.get(name) != sri(data):
            problems.append(f"{name}: digest {sri(data)} is not integrity.json's {integrity.get(name)}")
        banner = BANNER.search(data[:400].decode("utf-8", "replace"))
        if not banner or banner.group(1) != catalog["version"]:
            problems.append(
                f"{name}: version {banner and banner.group(1)} is not the host catalog's {catalog['version']}"
            )
    if folder == VENDOR and (
        not DJANGO_STATIC.is_file() or DJANGO_STATIC.read_bytes() != (folder / SCRIPTS[0]).read_bytes()
    ):
        problems.append(
            "contrib/django/static/silverpoint/silverpoint-embed.full.js is not the vendored script"
        )
    if kit["version"] != catalog["version"]:
        problems.append(f"conformance.json {kit['version']} is not the host catalog's {catalog['version']}")
    try:
        props = engine_props((folder / SCRIPTS[1]).read_text(encoding="utf-8"), catalog)
        if not (folder / "props.json").is_file():
            problems.append("missing props.json")
        elif json.loads((folder / "props.json").read_text(encoding="utf-8")) != props:
            problems.append("props.json is not the engine's prop tables (run vendor.py again)")
    except ValueError as error:
        problems.append(f"{SCRIPTS[1]}: {error}")
    for needed in ("OFL.txt", "html-goldens/cases.json", "tables/rows.json"):
        if not (folder / needed).is_file():
            problems.append(f"missing {needed}")
    if folder == VENDOR:
        # PY-DD-01: the checked-in package mirrors what it vendors. A staging folder is checked before the
        # version is moved (`vendor.py X.Y.Z`, then the version), so it is exempt.
        problems.extend(version_problems(catalog["version"]))
    return problems


def version_problems(library: str) -> list[str]:
    """``pyproject.toml`` and ``silverpoint.__version__`` both equal X.Y.Z or X.Y.Z.postN of ``library``."""
    problems = []
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    version = re.search(r'^version = "([^"]+)"', pyproject, re.M).group(1)
    if version.split(".post")[0] != library:
        problems.append(f"pyproject version {version} does not mirror the library's {library} (PY-DD-01)")
    init = (ROOT / "src" / "silverpoint" / "__init__.py").read_text(encoding="utf-8")
    package = re.search(r'^__version__ = "([^"]+)"', init, re.M).group(1)
    if package != version:
        problems.append(f"silverpoint.__version__ {package} is not pyproject's {version}")
    return problems


KIT = (*SCRIPTS, *DATA)


def from_local(source: Path, staging: Path) -> None:
    """The same files the hosts kit holds, from a silverpoint checkout's ``packages/embed/dist``."""
    dist = source / "packages" / "embed" / "dist"
    for name in KIT:
        shutil.copy2(dist / name, staging / name)
    shutil.copytree(dist / "html-goldens", staging / "html-goldens")
    shutil.copytree(dist / "tables", staging / "tables")
    shutil.copy2(source / "packages" / "fonts" / "OFL.txt", staging / "OFL.txt")


def from_release(version: str, staging: Path) -> None:
    """The hosts kit attached to the GitHub release ``vX.Y.Z`` (silverpoint TD delta §6)."""
    with urllib.request.urlopen(RELEASE.format(version=version)) as response:
        archive = zipfile.ZipFile(io.BytesIO(response.read()))
    for member in archive.namelist():
        name = member.split("/", 1)[0]
        if name in KIT or name in ("html-goldens", "tables"):
            archive.extract(member, staging)
    # The font licence is not in the kit: it ships with the package already and is kept across versions.
    shutil.copy2(VENDOR / "OFL.txt", staging / "OFL.txt")


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("version", nargs="?")
    parser.add_argument("--from", dest="source", type=Path)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.check:
        problems = verify(VENDOR)
        for p in problems:
            print("✗", p)
        print("vendor ok" if not problems else f"{len(problems)} problem(s)")
        return 1 if problems else 0
    staging = ROOT / ".vendor-staging"
    shutil.rmtree(staging, ignore_errors=True)
    staging.mkdir()
    try:
        if args.source:
            from_local(args.source.expanduser(), staging)
        elif args.version:
            from_release(args.version, staging)
        else:
            parser.error("give a version, --from PATH or --check")
        write_props(staging)
        problems = verify(staging)
        if problems:
            for p in problems:
                print("✗", p)
            return 1
        shutil.rmtree(VENDOR)
        staging.rename(VENDOR)
        shutil.copy2(VENDOR / SCRIPTS[0], DJANGO_STATIC)
        print(
            "vendored",
            json.loads((VENDOR / "host-catalog.json").read_text())["version"],
            "into",
            VENDOR.relative_to(ROOT),
        )
        print("now run: uv run python scripts/make_builders.py, and set the version in pyproject.toml")
        print("and silverpoint/__init__.py (`vendor.py --check` fails until both mirror it)")
        return 0
    finally:
        shutil.rmtree(staging, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
