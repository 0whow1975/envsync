"""Group env entries by prefix or custom mapping."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

from envsync.parser import EnvEntry, EnvFile


@dataclass
class GroupOptions:
    separator: str = "_"
    fallback_group: str = "misc"
    custom_mapper: Optional[Callable[[EnvEntry], str]] = None
    case_sensitive: bool = False


@dataclass
class GroupResult:
    groups: Dict[str, List[EnvEntry]] = field(default_factory=dict)

    @property
    def total_groups(self) -> int:
        return len(self.groups)

    @property
    def total_keys(self) -> int:
        return sum(len(v) for v in self.groups.values())

    def keys_in_group(self, name: str) -> List[str]:
        normalised = name if self.groups else name
        return [e.key for e in self.groups.get(normalised, [])]

    def group_names(self) -> List[str]:
        return sorted(self.groups.keys())


def _default_prefix(entry: EnvEntry, separator: str, case_sensitive: bool) -> str:
    key = entry.key if case_sensitive else entry.key.upper()
    if separator in key:
        return key.split(separator, 1)[0]
    return ""


def group_env(
    env: EnvFile,
    options: Optional[GroupOptions] = None,
) -> GroupResult:
    """Partition *env* entries into named groups.

    By default the group name is derived from the key prefix before the first
    ``separator`` character.  Supply ``options.custom_mapper`` to override the
    grouping logic entirely.
    """
    if options is None:
        options = GroupOptions()

    result: Dict[str, List[EnvEntry]] = {}

    for entry in env.entries:
        if entry.is_comment or entry.key is None:
            continue

        if options.custom_mapper is not None:
            group = options.custom_mapper(entry)
        else:
            prefix = _default_prefix(entry, options.separator, options.case_sensitive)
            group = prefix if prefix else options.fallback_group

        if not options.case_sensitive:
            group = group.upper()

        result.setdefault(group, []).append(entry)

    return GroupResult(groups=result)
