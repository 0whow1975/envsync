"""Key rotation: rename keys across multiple env files in one operation."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envsync.parser import EnvFile, EnvEntry


@dataclass
class RotateOptions:
    """Options controlling how key rotation is applied."""
    dry_run: bool = False
    ignore_missing: bool = True  # silently skip files that don't have the old key


@dataclass
class RotateViolation:
    path: str
    old_key: str
    reason: str

    def __str__(self) -> str:
        return f"{self.path}: cannot rotate '{self.old_key}' — {self.reason}"


@dataclass
class RotateResult:
    rotated: Dict[str, List[str]] = field(default_factory=dict)  # old_key -> [paths]
    skipped: Dict[str, List[str]] = field(default_factory=dict)  # old_key -> [paths]
    violations: List[RotateViolation] = field(default_factory=list)

    @property
    def total_rotated(self) -> int:
        return sum(len(v) for v in self.rotated.values())

    @property
    def total_skipped(self) -> int:
        return sum(len(v) for v in self.skipped.values())

    @property
    def has_violations(self) -> bool:
        return len(self.violations) > 0


def rotate_key(
    env_files: List[EnvFile],
    rename_map: Dict[str, str],
    options: Optional[RotateOptions] = None,
) -> tuple[List[EnvFile], RotateResult]:
    """Rename keys across *env_files* according to *rename_map* {old: new}.

    Returns updated copies of each file and a RotateResult summary.
    """
    opts = options or RotateOptions()
    result = RotateResult()
    updated_files: List[EnvFile] = []

    for env_file in env_files:
        existing_keys = {e.key for e in env_file.entries}
        new_entries: List[EnvEntry] = []
        file_changed = False

        for entry in env_file.entries:
            if entry.key in rename_map:
                new_key = rename_map[entry.key]
                if new_key in existing_keys and new_key != entry.key:
                    result.violations.append(
                        RotateViolation(env_file.path, entry.key, f"target key '{new_key}' already exists")
                    )
                    new_entries.append(entry)
                else:
                    new_entries.append(EnvEntry(key=new_key, value=entry.value, comment=entry.comment))
                    result.rotated.setdefault(entry.key, []).append(env_file.path)
                    file_changed = True
            else:
                new_entries.append(entry)

        # track keys that were not present in this file
        for old_key in rename_map:
            if old_key not in existing_keys:
                if not opts.ignore_missing:
                    result.violations.append(
                        RotateViolation(env_file.path, old_key, "key not found")
                    )
                else:
                    result.skipped.setdefault(old_key, []).append(env_file.path)

        if opts.dry_run or not file_changed:
            updated_files.append(env_file)
        else:
            updated_files.append(EnvFile(path=env_file.path, entries=new_entries))

    return updated_files, result
