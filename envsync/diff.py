"""Diff engine — compares two EnvFile instances and produces structured results."""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List

from envsync.parser import EnvFile


class ChangeType(str, Enum):
    ADDED = "added"       # key present in target but not in source
    REMOVED = "removed"   # key present in source but not in target
    CHANGED = "changed"   # key present in both but values differ
    UNCHANGED = "unchanged"


@dataclass
class DiffEntry:
    key: str
    change_type: ChangeType
    source_value: str | None = None
    target_value: str | None = None


@dataclass
class DiffResult:
    source_path: str
    target_path: str
    entries: List[DiffEntry]

    @property
    def has_changes(self) -> bool:
        return any(e.change_type != ChangeType.UNCHANGED for e in self.entries)

    def by_type(self, change_type: ChangeType) -> List[DiffEntry]:
        return [e for e in self.entries if e.change_type == change_type]

    def summary(self) -> Dict[str, int]:
        counts: Dict[str, int] = {ct.value: 0 for ct in ChangeType}
        for entry in self.entries:
            counts[entry.change_type.value] += 1
        return counts

    def changed_keys(self) -> List[str]:
        """Return a sorted list of keys that have any change (added, removed, or changed)."""
        return sorted(
            e.key for e in self.entries if e.change_type != ChangeType.UNCHANGED
        )


def diff_env_files(source: EnvFile, target: EnvFile) -> DiffResult:
    """Compare source vs target EnvFile and return a DiffResult.

    Args:
        source: The baseline EnvFile (e.g. a committed .env.example).
        target: The EnvFile to compare against the source (e.g. a local .env).

    Returns:
        A DiffResult containing one DiffEntry per unique key found across
        both files, each annotated with its ChangeType and values.
    """
    entries: List[DiffEntry] = []

    all_keys = dict.fromkeys(list(source.order) + list(target.order))

    for key in all_keys:
        src_val = source.get(key)
        tgt_val = target.get(key)

        if src_val is None and tgt_val is not None:
            change = ChangeType.ADDED
        elif src_val is not None and tgt_val is None:
            change = ChangeType.REMOVED
        elif src_val != tgt_val:
            change = ChangeType.CHANGED
        else:
            change = ChangeType.UNCHANGED

        entries.append(
            DiffEntry(
                key=key,
                change_type=change,
                source_value=src_val,
                target_value=tgt_val,
            )
        )

    return DiffResult(
        source_path=str(source.path),
        target_path=str(target.path),
        entries=entries,
    )
