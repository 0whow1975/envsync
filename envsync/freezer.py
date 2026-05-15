"""Freeze an EnvFile into an immutable snapshot dict and detect drift."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from envsync.parser import EnvFile


@dataclass
class FreezeOptions:
    include_comments: bool = False
    mask_secrets: bool = True


@dataclass
class FrozenKey:
    key: str
    value_hash: str  # sha256 of the raw value
    raw_value: str

    def to_dict(self) -> dict:
        return {"key": self.key, "value_hash": self.value_hash}


@dataclass
class FreezeResult:
    path: str
    frozen_keys: List[FrozenKey] = field(default_factory=list)
    checksum: str = ""

    def to_dict(self) -> dict:
        return {
            "path": self.path,
            "checksum": self.checksum,
            "keys": [fk.to_dict() for fk in self.frozen_keys],
        }

    @property
    def key_count(self) -> int:
        return len(self.frozen_keys)


@dataclass
class DriftEntry:
    key: str
    expected_hash: str
    actual_hash: str

    @property
    def drifted(self) -> bool:
        return self.expected_hash != self.actual_hash


@dataclass
class DriftReport:
    drifted: List[DriftEntry] = field(default_factory=list)
    missing: List[str] = field(default_factory=list)
    added: List[str] = field(default_factory=list)

    @property
    def is_clean(self) -> bool:
        return not self.drifted and not self.missing and not self.added


def _hash_value(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def freeze_env(env: EnvFile, options: Optional[FreezeOptions] = None) -> FreezeResult:
    opts = options or FreezeOptions()
    frozen_keys: List[FrozenKey] = []
    for entry in env.entries:
        if entry.is_comment or entry.is_blank:
            continue
        if entry.key:
            frozen_keys.append(
                FrozenKey(
                    key=entry.key,
                    value_hash=_hash_value(entry.value or ""),
                    raw_value=entry.value or "",
                )
            )
    payload = json.dumps(
        {fk.key: fk.value_hash for fk in frozen_keys}, sort_keys=True
    )
    checksum = hashlib.sha256(payload.encode()).hexdigest()
    return FreezeResult(
        path=str(env.path),
        frozen_keys=frozen_keys,
        checksum=checksum,
    )


def save_freeze(result: FreezeResult, dest: Path) -> None:
    dest.write_text(json.dumps(result.to_dict(), indent=2))


def load_freeze(src: Path) -> FreezeResult:
    data = json.loads(src.read_text())
    frozen_keys = [
        FrozenKey(key=k["key"], value_hash=k["value_hash"], raw_value="")
        for k in data.get("keys", [])
    ]
    return FreezeResult(
        path=data["path"],
        frozen_keys=frozen_keys,
        checksum=data.get("checksum", ""),
    )


def check_drift(frozen: FreezeResult, current: EnvFile) -> DriftReport:
    frozen_map: Dict[str, str] = {fk.key: fk.value_hash for fk in frozen.frozen_keys}
    current_map: Dict[str, str] = {}
    for entry in current.entries:
        if entry.is_comment or entry.is_blank:
            continue
        if entry.key:
            current_map[entry.key] = _hash_value(entry.value or "")

    drifted: List[DriftEntry] = []
    for key, expected_hash in frozen_map.items():
        if key not in current_map:
            continue
        if current_map[key] != expected_hash:
            drifted.append(DriftEntry(key=key, expected_hash=expected_hash, actual_hash=current_map[key]))

    missing = [k for k in frozen_map if k not in current_map]
    added = [k for k in current_map if k not in frozen_map]
    return DriftReport(drifted=drifted, missing=missing, added=added)
