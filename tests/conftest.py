import json
import shutil
from pathlib import Path

import pytest

VENDOR = Path(__file__).resolve().parents[1] / "src" / "silverpoint" / "_vendor"
FIXTURES = Path(__file__).resolve().parent / "fixtures"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def pytest_collection_modifyitems(config, items):
    if shutil.which("node"):
        return
    skip = pytest.mark.skip(reason="Node 20+ is not on PATH")
    for item in items:
        if "node" in item.keywords:
            item.add_marker(skip)
