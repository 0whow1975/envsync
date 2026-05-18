"""Alias support: map one or more keys to a canonical name across env files."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envsync.parser import EnvEntry, EnvFile


@dataclass
class AliasOptions:
    """Configuration for alias resolution."""
    alias_map: Dict[str, str]  # alias -> canonical
    overwrite: bool = False    # overwrite canonical if it already exists
    remove_alias: bool = True  # delete the alias key after copying


@dataclass
class AliasViolation:
    alias: str
    canonical: str
    reason: str

    def __str__(self) -> str:
        return f"{self.alias} -> {self.canonical}: {self.reason}"


@dataclass
class AliasResult:
    entries: List[EnvEntry]
    resolved: List[str] = field(default_factory=list)
    skipped: List[AliasViolation] = field(default_factory=list)

    @property
    def total_resolved(self) -> int:
        return len(self.resolved)

    @property
    def total_skipped(self) -> int:
        return len(self.skipped)

    def to_env_file(self, path: str) -> EnvFile:
        from envsync.parser import EnvFile
        return EnvFile(path=path, entries=self.entries)


def resolve_aliases(env: EnvFile, options: AliasOptions) -> AliasResult:
    """Resolve alias keys to their canonical names in *env*.

    For each alias->canonical pair:
    - If the alias key exists and canonical does not (or overwrite=True),
      copy the value to the canonical key.
    - If remove_alias=True, drop the alias entry from the output.
    """
    index: Dict[str, EnvEntry] = {
        e.key: e for e in env.entries if e.key is not None
    }
    resolved: List[str] = []
    skipped: List[AliasViolation] = []
    mutations: Dict[str, EnvEntry] = {}  # key -> new entry
    removals: set = set()

    for alias, canonical in options.alias_map.items():
        if alias not in index:
            skipped.append(AliasViolation(alias, canonical, "alias key not found"))
            continue
        if canonical in index and not options.overwrite:
            skipped.append(
                AliasViolation(alias, canonical, "canonical already exists and overwrite=False")
            )
            continue
        source = index[alias]
        mutations[canonical] = EnvEntry(
            key=canonical,
            value=source.value,
            comment=source.comment,
            raw=f"{canonical}={source.value}",
        )
        if options.remove_alias:
            removals.add(alias)
        resolved.append(alias)

    out: List[EnvEntry] = []
    seen_canonical = set()
    for entry in env.entries:
        key = entry.key
        if key in removals:
            continue
        if key in mutations and key not in seen_canonical:
            out.append(mutations[key])
            seen_canonical.add(key)
            continue
        out.append(entry)

    # append any canonical keys that were not already in the file
    for canonical, entry in mutations.items():
        if canonical not in seen_canonical:
            out.append(entry)

    return AliasResult(entries=out, resolved=resolved, skipped=skipped)
