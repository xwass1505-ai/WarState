
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
CONFIG = SRC / "ReplicatedStorage" / "Shared" / "Config"


def load_json(name):
    with open(CONFIG / name, encoding="utf-8") as f:
        return json.load(f)


def read(rel):
    return (ROOT / rel).read_text(encoding="utf-8")

import importlib.util
import sys

_spec = importlib.util.spec_from_file_location("luau_static", Path(__file__).with_name("luau_static.py"))
luau_static = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(luau_static)


class LuauStaticTests(unittest.TestCase):
    def test_all_luau_files(self):
        failures = {}
        files = list(SRC.rglob("*.luau")) + list((ROOT / "plugin").rglob("*.luau"))
        self.assertGreater(len(files), 20)
        for path in files:
            is_module = not (path.name.endswith(".server.luau") or path.name.endswith(".client.luau"))
            errors = luau_static.check_luau(path.read_text(encoding="utf-8"), is_module)
            if errors:
                failures[str(path.relative_to(ROOT))] = errors
        self.assertEqual(failures, {})

    def test_no_todo_placeholders_in_required_code(self):
        offenders = [
            str(p.relative_to(ROOT)) for p in SRC.rglob("*.luau") if "TODO" in p.read_text(encoding="utf-8")
        ]
        self.assertEqual(offenders, [])

    def test_json_configs_parse(self):
        for path in CONFIG.glob("*.json"):
            json.loads(path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
