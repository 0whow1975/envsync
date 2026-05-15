"""Sanitize .env values by applying configurable cleaning rules."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from envsync.parser import EnvEntry, EnvFile


@dataclass
class SanitizeOptions:
    """Options controlling which sanitization rules are applied."""
    strip_whitespace: bool = True
    remove_null_bytes: bool = True
    collapse_newlines: bool = True
    max_value_length: int | None = None  # None means no limit
    redact_patterns: List[str] = field(default_factory=list)  # regex patterns


@dataclass
class SanitizeResult:
    """Result of a sanitize operation."""
    original: EnvFile
    entries: List[EnvEntry]
    sanitized_keys: List[str] = field(default_factory=list)

    @property
    def was_modified(self) -> bool:
        return len(self.sanitized_keys) > 0

    @property
    def total_sanitized(self) -> int:
        return len(self.sanitized_keys)

    def to_env_file(self) -> EnvFile:
        import copy
        result = copy.copy(self.original)
        result.entries = self.entries
        return result


def _sanitize_entry(
    entry: EnvEntry,
    options: SanitizeOptions,
    sanitized_keys: List[str],
) -> EnvEntry:
    import re

    if entry.is_comment or entry.key is None:
        return entry

    original_value = entry.value or ""
    value = original_value

    if options.strip_whitespace:
        value = value.strip()

    if options.remove_null_bytes:
        value = value.replace("\x00", "")

    if options.collapse_newlines:
        value = re.sub(r"[\r\n]+", " ", value).strip()

    if options.max_value_length is not None and len(value) > options.max_value_length:
        value = value[: options.max_value_length]

    for pattern in options.redact_patterns:
        value = re.sub(pattern, "***", value)

    if value != original_value:
        sanitized_keys.append(entry.key)
        return EnvEntry(
            key=entry.key,
            value=value,
            comment=entry.comment,
            is_comment=entry.is_comment,
            raw=entry.raw,
        )

    return entry


def sanitize_env(
    env: EnvFile,
    options: SanitizeOptions | None = None,
) -> SanitizeResult:
    """Apply sanitization rules to all entries in *env*."""
    if options is None:
        options = SanitizeOptions()

    sanitized_keys: List[str] = []
    cleaned: List[EnvEntry] = [
        _sanitize_entry(e, options, sanitized_keys) for e in env.entries
    ]

    return SanitizeResult(
        original=env,
        entries=cleaned,
        sanitized_keys=sanitized_keys,
    )
