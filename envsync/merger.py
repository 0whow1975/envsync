"""Merge multiple .env files with configurable conflict resolution strategies."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional

from envsync.parser import EnvEntry, EnvFile


class ConflictStrategy(str, Enum):
    FIRST = "first"    # keep value from the first file that defines the key
    LAST = "last"      # keep value from the last file that defines the key
    ERROR = "error"    # raise an error on conflict


@dataclass
class MergeConflict:
    key: str
    values: Dict[str, str]  # path -> value

    def __str__(self) -> str:
        parts = ", ".join(f"{p}={v!r}" for p, v in self.values.items())
        return f"Conflict on '{self.key}': {parts}"


@dataclass
class MergeResult:
    merged: EnvFile
    conflicts: List[MergeConflict] = field(default_factory=list)
    sources: List[str] = field(default_factory=list)

    @property
    def has_conflicts(self) -> bool:
        return len(self.conflicts) > 0


class MergeError(ValueError):
    """Raised when strategy=ERROR and a conflict is detected."""


def merge(
    env_files: List[EnvFile],
    strategy: ConflictStrategy = ConflictStrategy.LAST,
    ignore_comments: bool = False,
) -> MergeResult:
    """Merge a list of EnvFile objects into a single EnvFile.

    Parameters
    ----------
    env_files:
        Ordered list of EnvFile instances to merge.
    strategy:
        How to handle keys that appear in more than one file.
    ignore_comments:
        When True, comment entries are dropped from the merged output.
    """
    if not env_files:
        return MergeResult(merged=EnvFile(path="merged", entries=[]))

    seen: Dict[str, EnvEntry] = {}
    conflicts: List[MergeConflict] = []
    conflict_map: Dict[str, Dict[str, str]] = {}
    sources = [ef.path for ef in env_files]

    for env_file in env_files:
        for entry in env_file.entries:
            if entry.comment or ignore_comments and entry.comment:
                continue
            if entry.key is None:
                continue

            if entry.key in seen:
                existing = seen[entry.key]
                if existing.value != entry.value:
                    if strategy == ConflictStrategy.ERROR:
                        raise MergeError(
                            f"Conflict on key '{entry.key}': "
                            f"{existing.value!r} vs {entry.value!r}"
                        )
                    if entry.key not in conflict_map:
                        conflict_map[entry.key] = {existing.source: existing.value}
                    conflict_map[entry.key][entry.source] = entry.value

                    if strategy == ConflictStrategy.LAST:
                        seen[entry.key] = entry
                    # FIRST: keep existing, do nothing
            else:
                seen[entry.key] = entry

    for key, values in conflict_map.items():
        conflicts.append(MergeConflict(key=key, values=values))

    merged_entries = list(seen.values())
    merged = EnvFile(path="merged", entries=merged_entries)
    return MergeResult(merged=merged, conflicts=conflicts, sources=sources)
