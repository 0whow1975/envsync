"""Clone an EnvFile, optionally filtering or transforming keys during the copy."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Collection, Optional

from envsync.parser import EnvEntry, EnvFile


@dataclass
class CloneOptions:
    """Options that control how a clone is produced."""

    include_keys: Optional[Collection[str]] = None
    """When set, only these keys are copied (comments/blanks always copied)."""

    exclude_keys: Collection[str] = field(default_factory=set)
    """Keys to omit from the clone."""

    key_transform: Optional[Callable[[str], str]] = None
    """Optional function applied to every key name."""

    value_transform: Optional[Callable[[str, str], str]] = None
    """Optional function ``(key, value) -> new_value`` applied to every value."""

    strip_comments: bool = False
    """Drop comment and blank lines from the clone."""


@dataclass
class CloneResult:
    """Result of a clone operation."""

    env: EnvFile
    total_copied: int
    total_skipped: int

    @property
    def was_filtered(self) -> bool:
        return self.total_skipped > 0


def clone_env(source: EnvFile, options: Optional[CloneOptions] = None) -> CloneResult:
    """Return a new :class:`EnvFile` cloned from *source* according to *options*."""
    if options is None:
        options = CloneOptions()

    include = set(options.include_keys) if options.include_keys is not None else None
    exclude = set(options.exclude_keys)

    new_entries: list[EnvEntry] = []
    copied = 0
    skipped = 0

    for entry in source.entries:
        # Pass through structural lines unless the caller wants them stripped.
        if entry.key is None:
            if not options.strip_comments:
                new_entries.append(entry)
            continue

        key = entry.key

        # Apply inclusion / exclusion filters.
        if include is not None and key not in include:
            skipped += 1
            continue
        if key in exclude:
            skipped += 1
            continue

        # Apply optional transforms.
        new_key = options.key_transform(key) if options.key_transform else key
        new_value = (
            options.value_transform(key, entry.value)
            if options.value_transform
            else entry.value
        )

        new_entries.append(
            EnvEntry(
                key=new_key,
                value=new_value,
                comment=entry.comment,
                raw=entry.raw,
            )
        )
        copied += 1

    cloned = EnvFile(path=source.path, entries=new_entries)
    return CloneResult(env=cloned, total_copied=copied, total_skipped=skipped)
