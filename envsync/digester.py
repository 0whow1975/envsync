"""Compute and compare content digests (checksums) for .env files."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envsync.parser import EnvFile


@dataclass
class DigestOptions:
    algorithm: str = "sha256"  # sha256 | md5 | sha1
    include_comments: bool = False
    include_blank_lines: bool = False
    keys_only: bool = False  # hash only keys, not values


@dataclass
class DigestEntry:
    key: str
    value_digest: str

    def to_dict(self) -> dict:
        return {"key": self.key, "value_digest": self.value_digest}


@dataclass
class DigestResult:
    path: str
    algorithm: str
    overall_digest: str
    entries: List[DigestEntry] = field(default_factory=list)
    key_count: int = 0

    def to_dict(self) -> dict:
        return {
            "path": self.path,
            "algorithm": self.algorithm,
            "overall_digest": self.overall_digest,
            "key_count": self.key_count,
            "entries": [e.to_dict() for e in self.entries],
        }

    def matches(self, other: "DigestResult") -> bool:
        return self.overall_digest == other.overall_digest


def _hash(value: str, algorithm: str) -> str:
    h = hashlib.new(algorithm)
    h.update(value.encode())
    return h.hexdigest()


def digest_env(env: EnvFile, options: Optional[DigestOptions] = None) -> DigestResult:
    """Compute a digest for an EnvFile."""
    opts = options or DigestOptions()
    algo = opts.algorithm

    entries: List[DigestEntry] = []
    for entry in env.entries:
        if entry.is_comment and not opts.include_comments:
            continue
        if entry.is_blank and not opts.include_blank_lines:
            continue
        if entry.key is None:
            continue
        raw = entry.key if opts.keys_only else f"{entry.key}={entry.value}"
        entries.append(DigestEntry(key=entry.key, value_digest=_hash(raw, algo)))

    combined = json.dumps(
        {e.key: e.value_digest for e in entries}, sort_keys=True
    )
    overall = _hash(combined, algo)

    return DigestResult(
        path=str(env.path),
        algorithm=algo,
        overall_digest=overall,
        entries=entries,
        key_count=len(entries),
    )


def compare_digests(a: DigestResult, b: DigestResult) -> Dict[str, str]:
    """Return a dict of keys whose digests differ between two DigestResults."""
    a_map = {e.key: e.value_digest for e in a.entries}
    b_map = {e.key: e.value_digest for e in b.entries}
    all_keys = set(a_map) | set(b_map)
    diffs: Dict[str, str] = {}
    for key in sorted(all_keys):
        av = a_map.get(key)
        bv = b_map.get(key)
        if av != bv:
            diffs[key] = f"{av or 'missing'} -> {bv or 'missing'}"
    return diffs
