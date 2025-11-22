from __future__ import annotations

import importlib
import json
from pathlib import Path
from typing import Any, Dict


def _yaml_module():
    spec = importlib.util.find_spec("yaml")
    if spec is None:
        return None
    return importlib.import_module("yaml")


def load_yaml(path: Path) -> Dict:
    if not path.exists():
        return {}
    text = path.read_text(encoding="utf-8")
    module = _yaml_module()
    if module:
        return module.safe_load(text) or {}
    return json.loads(text) if text else {}


def dump_yaml(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    module = _yaml_module()
    if module:
        text = module.safe_dump(data, sort_keys=False)
    else:
        text = json.dumps(data, indent=2)
    path.write_text(text, encoding="utf-8")
