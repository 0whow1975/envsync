"""Redactor module: strip or replace secret values before writing env files."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from envsync.parser import EnvFile, EnvEntry
from envsync.masker import SecretMasker, MaskConfig


@dataclass
class RedactOptions:
    placeholder: str = "REDACTED"
    mask_config: MaskConfig = field(default_factory=MaskConfig)
    redact_comments: bool = False


@dataclass
class RedactResult:
    original: EnvFile
    redacted: EnvFile
    redacted_keys: list[str] = field(default_factory=list)

    @property
    def total_redacted(self) -> int:
        return len(self.redacted_keys)


def redact(env: EnvFile, options: Optional[RedactOptions] = None) -> RedactResult:
    """Return a new EnvFile with secret values replaced by the placeholder."""
    if options is None:
        options = RedactOptions()

    masker = SecretMasker(options.mask_config)
    redacted_entries: list[EnvEntry] = []
    redacted_keys: list[str] = []

    for entry in env.entries:
        if entry.key is None:
            # comment or blank line
            if options.redact_comments:
                redacted_entries.append(EnvEntry(key=None, value=None, comment=""))
            else:
                redacted_entries.append(entry)
            continue

        if masker.is_secret(entry.key):
            new_entry = EnvEntry(
                key=entry.key,
                value=options.placeholder,
                comment=entry.comment,
            )
            redacted_entries.append(new_entry)
            redacted_keys.append(entry.key)
        else:
            redacted_entries.append(entry)

    redacted_file = EnvFile(path=env.path, entries=redacted_entries)
    return RedactResult(
        original=env,
        redacted=redacted_file,
        redacted_keys=redacted_keys,
    )


def redact_to_string(env: EnvFile, options: Optional[RedactOptions] = None) -> str:
    """Redact secrets and serialise the result back to .env text."""
    result = redact(env, options)
    lines: list[str] = []
    for entry in result.redacted.entries:
        if entry.key is None:
            lines.append(entry.comment or "")
        else:
            line = f"{entry.key}={entry.value}"
            if entry.comment:
                line += f"  # {entry.comment}"
            lines.append(line)
    return "\n".join(lines)
