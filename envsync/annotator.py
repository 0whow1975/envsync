"""Annotate .env entries with inline comments based on tag maps or custom notes."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envsync.parser import EnvEntry, EnvFile


@dataclass
class AnnotateOptions:
    annotations: Dict[str, str] = field(default_factory=dict)
    overwrite: bool = False
    prefix: str = "#"


@dataclass
class AnnotateResult:
    entries: List[EnvEntry]
    total_annotated: int
    total_skipped: int

    @property
    def was_modified(self) -> bool:
        return self.total_annotated > 0

    def to_env_file(self, path: str) -> EnvFile:
        return EnvFile(path=path, entries=self.entries)


def _annotate_entry(
    entry: EnvEntry,
    note: str,
    prefix: str,
    overwrite: bool,
) -> tuple[EnvEntry, bool]:
    """Return (new_entry, was_changed)."""
    if entry.comment and not overwrite:
        return entry, False
    new_comment = f"{prefix} {note}".strip()
    updated = EnvEntry(
        key=entry.key,
        value=entry.value,
        comment=new_comment,
        raw=entry.raw,
    )
    return updated, True


def annotate(env: EnvFile, options: Optional[AnnotateOptions] = None) -> AnnotateResult:
    """Attach inline comments to matching keys in *env*."""
    if options is None:
        options = AnnotateOptions()

    updated: List[EnvEntry] = []
    total_annotated = 0
    total_skipped = 0

    for entry in env.entries:
        if not entry.key or entry.key not in options.annotations:
            updated.append(entry)
            continue

        note = options.annotations[entry.key]
        new_entry, changed = _annotate_entry(
            entry, note, options.prefix, options.overwrite
        )
        updated.append(new_entry)
        if changed:
            total_annotated += 1
        else:
            total_skipped += 1

    return AnnotateResult(
        entries=updated,
        total_annotated=total_annotated,
        total_skipped=total_skipped,
    )
