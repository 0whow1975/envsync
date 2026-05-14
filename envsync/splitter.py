"""Split an EnvFile into multiple files by key prefix or tag."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from envsync.parser import EnvEntry, EnvFile


@dataclass
class SplitOptions:
    """Options controlling how an EnvFile is split."""

    delimiter: str = "_"
    # If provided, only these prefixes are extracted; others go to the remainder.
    include_prefixes: Optional[List[str]] = None
    # When True the prefix is stripped from the key in the output file.
    strip_prefix: bool = False


@dataclass
class SplitResult:
    """Result of a split operation."""

    groups: Dict[str, EnvFile] = field(default_factory=dict)
    # Keys that did not match any prefix.
    remainder: EnvFile = field(default_factory=lambda: EnvFile(path=Path("remainder.env"), entries=[]))

    @property
    def total_groups(self) -> int:
        return len(self.groups)

    @property
    def total_keys(self) -> int:
        return sum(len(ef.entries) for ef in self.groups.values()) + len(self.remainder.entries)


def _prefix_of(key: str, delimiter: str) -> Optional[str]:
    """Return the first segment before *delimiter*, or None if no delimiter present."""
    if delimiter in key:
        return key.split(delimiter, 1)[0]
    return None


def split_env(env: EnvFile, options: Optional[SplitOptions] = None) -> SplitResult:
    """Partition *env* entries into groups by key prefix.

    Parameters
    ----------
    env:
        The source :class:`EnvFile` to split.
    options:
        Behavioural options; defaults are used when *None*.

    Returns
    -------
    SplitResult
        A mapping of prefix -> EnvFile plus a remainder EnvFile for unmatched entries.
    """
    opts = options or SplitOptions()
    groups: Dict[str, List[EnvEntry]] = {}
    remainder: List[EnvEntry] = []

    for entry in env.entries:
        prefix = _prefix_of(entry.key, opts.delimiter)
        if prefix is None:
            remainder.append(entry)
            continue
        if opts.include_prefixes is not None and prefix not in opts.include_prefixes:
            remainder.append(entry)
            continue

        new_key = entry.key[len(prefix) + len(opts.delimiter):] if opts.strip_prefix else entry.key
        new_entry = EnvEntry(key=new_key, value=entry.value, comment=entry.comment)
        groups.setdefault(prefix, []).append(new_entry)

    result_groups: Dict[str, EnvFile] = {
        prefix: EnvFile(
            path=env.path.with_name(f"{prefix.lower()}.env"),
            entries=entries,
        )
        for prefix, entries in groups.items()
    }

    return SplitResult(
        groups=result_groups,
        remainder=EnvFile(path=env.path.with_name("remainder.env"), entries=remainder),
    )
