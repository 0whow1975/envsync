"""Apply a set of key-value patches to an EnvFile without a full sync."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envsync.parser import EnvEntry, EnvFile


@dataclass
class PatchOptions:
    """Controls how patches are applied."""

    overwrite_existing: bool = True
    add_missing: bool = True
    dry_run: bool = False


@dataclass
class PatchResult:
    """Outcome of a patch operation."""

    patched: List[str] = field(default_factory=list)
    skipped: List[str] = field(default_factory=list)
    env_file: Optional[EnvFile] = None

    @property
    def total_patched(self) -> int:
        return len(self.patched)

    @property
    def total_skipped(self) -> int:
        return len(self.skipped)

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"PatchResult(patched={self.total_patched}, skipped={self.total_skipped})"
        )


def patch_env(
    env: EnvFile,
    patches: Dict[str, str],
    options: Optional[PatchOptions] = None,
) -> PatchResult:
    """Return a new EnvFile with *patches* applied according to *options*.

    The original *env* object is never mutated.
    """
    if options is None:
        options = PatchOptions()

    existing_keys = {e.key for e in env.entries}
    result = PatchResult()

    # Build a mutable copy of entries as a dict keyed by position / key.
    entries: List[EnvEntry] = [EnvEntry(e.key, e.value, e.comment) for e in env.entries]
    key_to_index: Dict[str, int] = {e.key: i for i, e in enumerate(entries)}

    for key, value in patches.items():
        if key in existing_keys:
            if options.overwrite_existing:
                if not options.dry_run:
                    entries[key_to_index[key]] = EnvEntry(key, value, entries[key_to_index[key]].comment)
                result.patched.append(key)
            else:
                result.skipped.append(key)
        else:
            if options.add_missing:
                if not options.dry_run:
                    entries.append(EnvEntry(key, value))
                result.patched.append(key)
            else:
                result.skipped.append(key)

    result.env_file = EnvFile(path=env.path, entries=entries)
    return result
