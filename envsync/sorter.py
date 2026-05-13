"""Sort .env file entries alphabetically or by custom key order."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from envsync.parser import EnvEntry, EnvFile


@dataclass
class SortOptions:
    """Configuration for sorting behaviour."""

    reverse: bool = False
    # If provided, keys listed here come first (in order), rest follow alphabetically.
    priority_keys: List[str] = field(default_factory=list)
    case_sensitive: bool = False


@dataclass
class SortResult:
    """Outcome of a sort operation."""

    original: EnvFile
    sorted_env: EnvFile
    moved_count: int

    @property
    def was_sorted(self) -> bool:
        orig_keys = [e.key for e in self.original.entries if not e.is_comment and not e.is_blank]
        new_keys = [e.key for e in self.sorted_env.entries if not e.is_comment and not e.is_blank]
        return orig_keys != new_keys


def _sort_key(entry: EnvEntry, options: SortOptions, priority_index: dict) -> tuple:
    """Return a tuple used as the sort key for a single entry."""
    raw = entry.key
    normalised = raw if options.case_sensitive else raw.lower()
    priority = priority_index.get(raw, priority_index.get(raw.upper(), len(priority_index)))
    return (priority, normalised) if not options.reverse else (priority, [-ord(c) for c in normalised])


def sort_env(env: EnvFile, options: Optional[SortOptions] = None) -> SortResult:
    """Return a new EnvFile with entries sorted according to *options*.

    Comments and blank lines that immediately precede a key entry are kept
    attached to that entry so the file remains readable after sorting.
    """
    if options is None:
        options = SortOptions()

    priority_index: dict = {
        k: i for i, k in enumerate(options.priority_keys)
    }

    # Separate data entries from leading file-level comments/blanks.
    leading: List[EnvEntry] = []
    rest: List[EnvEntry] = list(env.entries)

    while rest and (rest[0].is_comment or rest[0].is_blank):
        leading.append(rest.pop(0))

    # Group each key entry with any comment/blank lines that precede it.
    groups: List[List[EnvEntry]] = []
    current_group: List[EnvEntry] = []
    for entry in rest:
        if entry.is_comment or entry.is_blank:
            current_group.append(entry)
        else:
            current_group.append(entry)
            groups.append(current_group)
            current_group = []
    # Trailing comments with no following key
    if current_group:
        groups.append(current_group)

    def group_key(group: List[EnvEntry]) -> tuple:
        key_entry = next((e for e in group if not e.is_comment and not e.is_blank), None)
        if key_entry is None:
            return (len(priority_index), "")
        return _sort_key(key_entry, options, priority_index)

    sorted_groups = sorted(groups, key=group_key)
    sorted_entries = leading + [e for g in sorted_groups for e in g]

    original_keys = [e.key for e in env.entries if not e.is_comment and not e.is_blank]
    new_keys = [e.key for e in sorted_entries if not e.is_comment and not e.is_blank]
    moved = sum(1 for a, b in zip(original_keys, new_keys) if a != b)

    sorted_env = EnvFile(path=env.path, entries=sorted_entries)
    return SortResult(original=env, sorted_env=sorted_env, moved_count=moved)
