"""Tag .env entries with user-defined labels for grouping and filtering."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, FrozenSet, List, Optional

from envsync.parser import EnvEntry, EnvFile


@dataclass
class TagOptions:
    """Options controlling tagging behaviour."""
    case_sensitive: bool = False
    allow_multiple: bool = True


@dataclass
class TagResult:
    """Outcome of a tagging operation."""
    tagged: Dict[str, FrozenSet[str]] = field(default_factory=dict)  # key -> tags
    skipped: List[str] = field(default_factory=list)

    @property
    def total_tagged(self) -> int:
        return len(self.tagged)

    @property
    def total_skipped(self) -> int:
        return len(self.skipped)


def _normalise(tag: str, case_sensitive: bool) -> str:
    return tag if case_sensitive else tag.lower()


def tag_entries(
    env: EnvFile,
    tag_map: Dict[str, List[str]],
    options: Optional[TagOptions] = None,
) -> TagResult:
    """Assign tags to env entries based on *tag_map* (key -> list[tag]).

    Keys present in *env* but absent from *tag_map* are recorded as skipped.
    """
    opts = options or TagOptions()
    result = TagResult()

    env_keys = {e.key for e in env.entries if not e.is_comment and e.key}

    for entry in env.entries:
        if entry.is_comment or not entry.key:
            continue
        if entry.key not in tag_map:
            result.skipped.append(entry.key)
            continue
        raw_tags = tag_map[entry.key]
        if not opts.allow_multiple:
            raw_tags = raw_tags[:1]
        normalised = frozenset(
            _normalise(t, opts.case_sensitive) for t in raw_tags
        )
        result.tagged[entry.key] = normalised

    return result


def filter_by_tag(
    env: EnvFile,
    tag_map: Dict[str, List[str]],
    tag: str,
    options: Optional[TagOptions] = None,
) -> List[EnvEntry]:
    """Return entries whose assigned tags include *tag*."""
    opts = options or TagOptions()
    needle = _normalise(tag, opts.case_sensitive)
    result = tag_entries(env, tag_map, opts)
    return [
        e for e in env.entries
        if not e.is_comment and e.key and needle in result.tagged.get(e.key, frozenset())
    ]
