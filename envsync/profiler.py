"""Profile an .env file and produce statistics about its contents."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from envsync.parser import EnvFile
from envsync.masker import SecretMasker, MaskConfig


@dataclass
class ProfileResult:
    path: str
    total_keys: int
    secret_keys: List[str]
    plain_keys: List[str]
    empty_keys: List[str]
    comment_lines: int
    blank_lines: int

    @property
    def secret_count(self) -> int:
        return len(self.secret_keys)

    @property
    def plain_count(self) -> int:
        return len(self.plain_keys)

    @property
    def empty_count(self) -> int:
        return len(self.empty_keys)

    def as_dict(self) -> dict:
        return {
            "path": self.path,
            "total_keys": self.total_keys,
            "secret_count": self.secret_count,
            "plain_count": self.plain_count,
            "empty_count": self.empty_count,
            "comment_lines": self.comment_lines,
            "blank_lines": self.blank_lines,
            "secret_keys": self.secret_keys,
            "plain_keys": self.plain_keys,
            "empty_keys": self.empty_keys,
        }

    def __str__(self) -> str:
        lines = [
            f"Profile: {self.path}",
            f"  Total keys   : {self.total_keys}",
            f"  Secrets      : {self.secret_count}",
            f"  Plain        : {self.plain_count}",
            f"  Empty values : {self.empty_count}",
            f"  Comment lines: {self.comment_lines}",
            f"  Blank lines  : {self.blank_lines}",
        ]
        return "\n".join(lines)


def profile_env(
    env: EnvFile,
    mask_config: MaskConfig | None = None,
) -> ProfileResult:
    """Analyse *env* and return a :class:`ProfileResult`."""
    masker = SecretMasker(mask_config or MaskConfig())

    secret_keys: List[str] = []
    plain_keys: List[str] = []
    empty_keys: List[str] = []
    comment_lines = 0
    blank_lines = 0

    for entry in env.entries:
        if entry.is_comment:
            comment_lines += 1
            continue
        if entry.is_blank:
            blank_lines += 1
            continue
        if entry.value == "":
            empty_keys.append(entry.key)
        if masker.is_secret(entry.key):
            secret_keys.append(entry.key)
        else:
            plain_keys.append(entry.key)

    total_keys = len(secret_keys) + len(plain_keys)

    return ProfileResult(
        path=env.path,
        total_keys=total_keys,
        secret_keys=secret_keys,
        plain_keys=plain_keys,
        empty_keys=empty_keys,
        comment_lines=comment_lines,
        blank_lines=blank_lines,
    )
