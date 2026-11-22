"""PY-REQ-015, PY-REQ-016: the vendored files match `integrity.json`; the conformance kit passes."""

import base64
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
from conftest import VENDOR

ROOT = Path(__file__).resolve().parents[1]


def test_scripts_match_integrity():
    integrity = json.loads((VENDOR / "integrity.json").read_text())
    for name in ("silverpoint-embed.full.js", "silverpoint-embed.full.mjs"):
        digest = base64.b64encode(hashlib.sha384((VENDOR / name).read_bytes()).digest()).decode()
        assert integrity[name] == f"sha384-{digest}"


def test_vendor_check():
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "vendor.py"), "--check"], capture_output=True, text=True
    )
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.node
def test_conformance_kit():
    result = subprocess.run(
        [shutil.which("node"), str(ROOT / "scripts" / "conformance.mjs")], capture_output=True, text=True
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "0 failed" in result.stdout


def test_wheel_contents(tmp_path):
    if not shutil.which("uv"):
        pytest.skip("uv is not on PATH")
    subprocess.run(["uv", "build", "--wheel", "-o", str(tmp_path), "-q"], cwd=ROOT, check=True)
    wheel = next(tmp_path.glob("*.whl"))
    assert wheel.name.endswith("-py3-none-any.whl")
    import zipfile

    names = zipfile.ZipFile(wheel).namelist()
    for needed in (
        "silverpoint-embed.full.js",
        "host-catalog.json",
        "props.json",
        "integrity.json",
        "OFL.txt",
    ):
        assert any(n.endswith("_vendor/" + needed) for n in names), needed
    assert any(n.endswith("templatetags/silverpoint.py") for n in names)


def _load_vendor_script():
    import importlib.util

    spec = importlib.util.spec_from_file_location("vendor_script", ROOT / "scripts" / "vendor.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_staging_of_a_new_version_does_not_need_pyproject_bumped_first(tmp_path):
    """PY-REQ-015, PY-DD-01: `vendor.py X.Y.Z` verifies the kit, then the version is set — not before."""
    vendor = _load_vendor_script()
    staging = tmp_path / "staging"
    shutil.copytree(VENDOR, staging)
    old = json.loads((VENDOR / "host-catalog.json").read_text())["version"]
    integrity = json.loads((staging / "integrity.json").read_text())
    for name in vendor.SCRIPTS:
        data = (
            (staging / name)
            .read_bytes()
            .replace(f"@silverpoint/embed {old}".encode(), b"@silverpoint/embed 9.9.9", 1)
        )
        (staging / name).write_bytes(data)
        integrity[name] = vendor.sri(data)
    (staging / "integrity.json").write_text(json.dumps(integrity))
    for name in ("host-catalog.json", "conformance.json"):
        doc = json.loads((staging / name).read_text())
        doc["version"] = "9.9.9"
        (staging / name).write_text(json.dumps(doc))
    assert vendor.verify(staging) == []


def test_package_version_mirrors_pyproject():
    """PY-REQ-010, PY-DD-01: `silverpoint.__version__` is the distribution's version."""
    import re

    import silverpoint

    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert silverpoint.__version__ == re.search(r'^version = "([^"]+)"', pyproject, re.M).group(1)
