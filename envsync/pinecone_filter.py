"""Filter .env entries by key pattern, prefix, or tag set."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional, Set

from envsync.parser import EnvEntry, EnvFile


@dataclass
class FilterOptions:
    prefixes: List[str] = field(default_factory=list)
    patterns: List[str] = field(default_factory=list)
    tags: Set[str] = field(default_factory=set)
    invert: bool = False
    case_sensitive: bool = False


@dataclass
class FilterResult:
    matched: List[EnvEntry]
    excluded: List[EnvEntry]

    @property
    def total_matched(self) -> int:
        return len(self.matched)

    @property
    def total_excluded(self) -> int:
        return len(self.excluded)


def _matches(entry: EnvEntry, opts: FilterOptions) -> bool:
    key = entry.key if opts.case_sensitive else entry.key.lower()

    for prefix in opts.prefixes:
        p = prefix if opts.case_sensitive else prefix.lower()
        if key.startswith(p):
            return True

    for pattern in opts.patterns:
        flags = 0 if opts.case_sensitive else re.IGNORECASE
        if re.search(pattern, entry.key, flags):
            return True

    if opts.tags:
        entry_tags: Set[str] = set(getattr(entry, "tags", None) or [])
        if entry_tags & opts.tags:
            return True

    return False


def filter_env(env: EnvFile, opts: Optional[FilterOptions] = None) -> FilterResult:
    """Return entries that match (or don't match when inverted) the filter."""
    if opts is None:
        opts = FilterOptions()

    has_criteria = bool(opts.prefixes or opts.patterns or opts.tags)

    matched: List[EnvEntry] = []
    excluded: List[EnvEntry] = []

    for entry in env.entries:
        if entry.is_comment or not entry.key:
            excluded.append(entry)
            continue

        hit = _matches(entry, opts) if has_criteria else True
        if opts.invert:
            hit = not hit

        if hit:
            matched.append(entry)
        else:
            excluded.append(entry)

    return FilterResult(matched=matched, excluded=excluded)
