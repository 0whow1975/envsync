"""Strip comments and blank lines from .env files, with optional dry-run support."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from envsync.parser import EnvEntry, EnvFile


@dataclass
class StripOptions:
    remove_comments: bool = True
    remove_blank_lines: bool = True
    dry_run: bool = False


@dataclass
class StripResult:
    original: EnvFile
    stripped: EnvFile
    removed_comments: List[EnvEntry] = field(default_factory=list)
    removed_blanks: int = 0

    @property
    def was_modified(self) -> bool:
        return bool(self.removed_comments) or self.removed_blanks > 0

    @property
    def total_removed(self) -> int:
        return len(self.removed_comments) + self.removed_blanks

    def to_env_file(self) -> EnvFile:
        """Return the result env file (original if dry_run had no effect)."""
        return self.stripped

    def summary(self) -> str:
        parts = []
        if self.removed_comments:
            parts.append(f"{len(self.removed_comments)} comment(s) removed")
        if self.removed_blanks:
            parts.append(f"{self.removed_blanks} blank line(s) removed")
        if not parts:
            return "No changes."
        return ", ".join(parts) + "."


def strip_env(env: EnvFile, options: StripOptions | None = None) -> StripResult:
    """Strip comments and/or blank lines from *env* according to *options*."""
    if options is None:
        options = StripOptions()

    kept: List[EnvEntry] = []
    removed_comments: List[EnvEntry] = []
    removed_blanks = 0

    for entry in env.entries:
        is_comment = entry.key is None and entry.raw.lstrip().startswith("#")
        is_blank = entry.key is None and entry.raw.strip() == ""

        if is_comment and options.remove_comments:
            removed_comments.append(entry)
        elif is_blank and options.remove_blank_lines:
            removed_blanks += 1
        else:
            kept.append(entry)

    stripped = EnvFile(path=env.path, entries=kept)
    return StripResult(
        original=env,
        stripped=stripped,
        removed_comments=removed_comments,
        removed_blanks=removed_blanks,
    )
