"""Human-readable summary statistics derived from a DiffResult."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from envsync.diff import DiffResult, ChangeType


@dataclass
class DiffSummary:
    """Aggregated counts and metadata for a diff result."""

    added: int
    removed: int
    changed: int
    unchanged: int
    total: int
    source_path: Optional[str] = None
    target_path: Optional[str] = None

    @property
    def total_changes(self) -> int:
        """Number of keys that differ (added + removed + changed)."""
        return self.added + self.removed + self.changed

    @property
    def is_clean(self) -> bool:
        """True when source and target are identical."""
        return self.total_changes == 0

    def as_dict(self) -> dict:
        return {
            "added": self.added,
            "removed": self.removed,
            "changed": self.changed,
            "unchanged": self.unchanged,
            "total": self.total,
            "total_changes": self.total_changes,
            "is_clean": self.is_clean,
            "source_path": self.source_path,
            "target_path": self.target_path,
        }

    def __str__(self) -> str:
        lines = []
        if self.source_path and self.target_path:
            lines.append(f"Comparing {self.source_path} → {self.target_path}")
        lines.append(
            f"  added={self.added}  removed={self.removed}  "
            f"changed={self.changed}  unchanged={self.unchanged}  total={self.total}"
        )
        if self.is_clean:
            lines.append("  ✓ Files are in sync")
        else:
            lines.append(f"  ✗ {self.total_changes} key(s) differ")
        return "\n".join(lines)


def summarize(result: DiffResult) -> DiffSummary:
    """Build a :class:`DiffSummary` from a :class:`DiffResult`."""
    counts: dict[ChangeType, int] = {
        ChangeType.ADDED: 0,
        ChangeType.REMOVED: 0,
        ChangeType.CHANGED: 0,
        ChangeType.UNCHANGED: 0,
    }
    for entry in result.entries:
        counts[entry.change_type] += 1

    total = sum(counts.values())

    source_path: Optional[str] = getattr(result.source, "path", None)
    target_path: Optional[str] = getattr(result.target, "path", None)

    return DiffSummary(
        added=counts[ChangeType.ADDED],
        removed=counts[ChangeType.REMOVED],
        changed=counts[ChangeType.CHANGED],
        unchanged=counts[ChangeType.UNCHANGED],
        total=total,
        source_path=str(source_path) if source_path else None,
        target_path=str(target_path) if target_path else None,
    )
