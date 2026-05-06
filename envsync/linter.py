"""Lint .env files for common issues like duplicate keys, empty values, and bad formatting."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List

from envsync.parser import EnvFile


class LintSeverity(str, Enum):
    WARNING = "warning"
    ERROR = "error"


@dataclass
class LintIssue:
    line: int
    key: str
    message: str
    severity: LintSeverity

    def __str__(self) -> str:
        return f"[{self.severity.value.upper()}] line {self.line}: {self.key} — {self.message}"


@dataclass
class LintResult:
    issues: List[LintIssue] = field(default_factory=list)

    @property
    def is_clean(self) -> bool:
        return len(self.issues) == 0

    @property
    def errors(self) -> List[LintIssue]:
        return [i for i in self.issues if i.severity == LintSeverity.ERROR]

    @property
    def warnings(self) -> List[LintIssue]:
        return [i for i in self.issues if i.severity == LintSeverity.WARNING]

    def __str__(self) -> str:
        if self.is_clean:
            return "No lint issues found."
        return "\n".join(str(i) for i in self.issues)


def lint_env_file(env: EnvFile) -> LintResult:
    """Run all lint checks on an EnvFile and return a LintResult."""
    result = LintResult()
    seen_keys: dict[str, int] = {}

    for entry in env.entries:
        lineno = entry.line if hasattr(entry, "line") else 0
        key = entry.key

        # Duplicate key check
        if key in seen_keys:
            result.issues.append(LintIssue(
                line=lineno,
                key=key,
                message=f"duplicate key (first seen on line {seen_keys[key]})",
                severity=LintSeverity.ERROR,
            ))
        else:
            seen_keys[key] = lineno

        # Empty value check
        if entry.value == "":
            result.issues.append(LintIssue(
                line=lineno,
                key=key,
                message="value is empty",
                severity=LintSeverity.WARNING,
            ))

        # Key naming convention (should be UPPER_SNAKE_CASE)
        if not key.isupper() or " " in key:
            result.issues.append(LintIssue(
                line=lineno,
                key=key,
                message="key should be UPPER_SNAKE_CASE",
                severity=LintSeverity.WARNING,
            ))

    return result
