# var.py - various variables that can change troughout

import json
from pathlib import Path

from scripts.const import SETTINGS_PATH

"""
This has to be the most fucky-wucky thing i ever did, but it works wonderfully
This also assuems that the json is strictly only key:val pairs and also fixed keys, however changing attributes in the classes also writes to the json
In another module you 'from var import Sizes' and then access all attributes while pyright knows the contents since theyre hard coded
When changing a value in a class, say Sizes.chunk_size=100 it immediatly updates the json aswell
"""

class _Sizes:
    chunk_size: int
    first_digits_amount: int
    pairs_per_insert: int
    max_processes: int

    def __init__(self) -> None:
        raw = json.loads(SETTINGS_PATH.read_text())
        object.__setattr__(self, "chunk_size", int(raw["chunk_size"]))
        object.__setattr__(self, "first_digits_amount", int(raw["first_digits_amount"]))
        object.__setattr__(self, "pairs_per_insert", int(raw["pairs_per_insert"]))
        object.__setattr__(self, "max_processes", int(raw["max_processes"]))

    def __setattr__(self, name: str, value: object) -> None:
        object.__setattr__(self, name, value)
        self._save()

    def _save(self):
        raw = json.loads(SETTINGS_PATH.read_text())
        raw.update({
            "chunk_size":self.chunk_size,
            "first_digits_amount":self.first_digits_amount,
            "pairs_per_insert":self.pairs_per_insert,
            "max_processes":self.max_processes,
        })
        SETTINGS_PATH.write_text(json.dumps(raw, indent=2))

class _Switches:
    report_not_found: bool
    one_indexed: bool

    def __init__(self) -> None:
        raw = json.loads(SETTINGS_PATH.read_text())
        object.__setattr__(self, "report_not_found", bool(raw["report_not_found"]))
        object.__setattr__(self, "one_indexed", bool(raw["one_indexed"]))

    def __setattr__(self, name: str, value: object) -> None:
        object.__setattr__(self, name, value)
        self._save()

    def _save(self):
        raw = json.loads(SETTINGS_PATH.read_text())
        raw.update({
            "report_not_found":self.report_not_found,
            "one_indexed":self.one_indexed,
        })
        SETTINGS_PATH.write_text(json.dumps(raw, indent=2))

class _Paths:
    num_dir: Path
    sqlite_path: Path

    def __init__(self) -> None:
        raw = json.loads(SETTINGS_PATH.read_text())
        object.__setattr__(self, "num_dir", Path(raw["num_dir"]))
        object.__setattr__(self, "sqlite_path", Path(raw["sqlite_path"]))

    def __setattr__(self, name: str, value: object) -> None:
        object.__setattr__(self, name, value)
        self._save()

    def _save(self):
        raw = json.loads(SETTINGS_PATH.read_text())
        raw.update({
            "num_dir":str(self.num_dir),
            "sqlite_path":str(self.sqlite_path),
        })
        SETTINGS_PATH.write_text(json.dumps(raw, indent=2))

Sizes = _Sizes()
Switches = _Switches()
Paths = _Paths()
