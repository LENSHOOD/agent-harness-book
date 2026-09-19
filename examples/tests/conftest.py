import json
import os
from pathlib import Path
import sys
import pytest

EXAMPLES = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(EXAMPLES))


@pytest.fixture
def evidence(tmp_path):
    root = Path(os.environ.get("EXAMPLES_RUN_DIR", tmp_path))
    root.mkdir(parents=True, exist_ok=True)

    def save(name, value):
        (root / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return root, save
