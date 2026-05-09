"""Rename keys across .env files with optional dry-run support."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from envsync.parser import EnvFile, EnvEntry


@dataclass
class RenameOptions:
    dry_run: bool = False
    ignore_missing: bool = False


@dataclass
class RenameResult:
    old_key: str
    new_key: str
    renamed: List[str] = field(default_factory=list)   # paths where rename occurred
    skipped: List[str] = field(default_factory=list)   # paths where key was absent

    @property
    def total_renamed(self) -> int:
        return len(self.renamed)

    @property
    def total_skipped(self) -> int:
        return len(self.skipped)


def rename_key(
    env_files: List[EnvFile],
    old_key: str,
    new_key: str,
    options: Optional[RenameOptions] = None,
) -> RenameResult:
    """Rename *old_key* to *new_key* in every supplied EnvFile.

    If *options.dry_run* is True the EnvFile objects are left unchanged and
    only the result metadata is populated.
    """
    if options is None:
        options = RenameOptions()

    result = RenameResult(old_key=old_key, new_key=new_key)

    for env_file in env_files:
        entry: Optional[EnvEntry] = env_file.get(old_key)

        if entry is None:
            if not options.ignore_missing:
                result.skipped.append(env_file.path)
            continue

        if not options.dry_run:
            new_entries = []
            for e in env_file.entries:
                if e.key == old_key:
                    new_entries.append(EnvEntry(key=new_key, value=e.value, comment=e.comment))
                else:
                    new_entries.append(e)
            # Mutate the entries list in-place so callers see the change.
            env_file.entries[:] = new_entries

        result.renamed.append(env_file.path)

    return result
