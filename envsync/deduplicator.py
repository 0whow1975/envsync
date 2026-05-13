"""Deduplicator: remove or report duplicate keys in an EnvFile."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict

from envsync.parser import EnvFile, EnvEntry


@dataclass
class DeduplicateOptions:
    """Options controlling deduplication behaviour."""
    keep: str = "last"  # "first" or "last"
    report_only: bool = False


@dataclass
class DeduplicateResult:
    """Result of a deduplication run."""
    entries: List[EnvEntry]
    duplicates: Dict[str, List[int]]  # key -> list of original line indices

    @property
    def total_removed(self) -> int:
        """Total number of duplicate entries removed."""
        return sum(len(v) - 1 for v in self.duplicates.values() if len(v) > 1)

    @property
    def has_duplicates(self) -> bool:
        return bool(self.duplicates)

    def to_env_file(self, source: EnvFile) -> EnvFile:
        """Return a new EnvFile with deduplicated entries."""
        return EnvFile(path=source.path, entries=self.entries)


def deduplicate(env: EnvFile, options: DeduplicateOptions | None = None) -> DeduplicateResult:
    """Deduplicate entries in *env* according to *options*.

    Args:
        env: Parsed environment file.
        options: Deduplication options; defaults are used when *None*.

    Returns:
        A :class:`DeduplicateResult` containing the cleaned entry list and a
        mapping of every key that appeared more than once to its original
        positions (0-based index into ``env.entries``).
    """
    if options is None:
        options = DeduplicateOptions()

    # Track all positions per key (comments / blank lines have key=None)
    seen: Dict[str, List[int]] = {}
    for idx, entry in enumerate(env.entries):
        if entry.key is None:
            continue
        seen.setdefault(entry.key, []).append(idx)

    duplicates = {k: v for k, v in seen.items() if len(v) > 1}

    if options.report_only:
        # Return original entries unchanged; just surface the duplicate map.
        return DeduplicateResult(entries=list(env.entries), duplicates=duplicates)

    # Build a set of indices to drop
    indices_to_drop: set[int] = set()
    for positions in duplicates.values():
        if options.keep == "first":
            # Drop everything after the first occurrence
            indices_to_drop.update(positions[1:])
        else:  # "last"
            # Drop everything before the last occurrence
            indices_to_drop.update(positions[:-1])

    cleaned = [
        entry for idx, entry in enumerate(env.entries)
        if idx not in indices_to_drop
    ]

    return DeduplicateResult(entries=cleaned, duplicates=duplicates)
