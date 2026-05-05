"""Validation utilities for .env files and sync operations."""

from dataclasses import dataclass, field
from typing import List, Optional
from envsync.parser import EnvFile


@dataclass
class ValidationIssue:
    key: str
    message: str
    severity: str = "error"  # "error" | "warning"

    def __str__(self) -> str:
        return f"[{self.severity.upper()}] {self.key}: {self.message}"


@dataclass
class ValidationResult:
    issues: List[ValidationIssue] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return not any(i.severity == "error" for i in self.issues)

    @property
    def errors(self) -> List[ValidationIssue]:
        return [i for i in self.issues if i.severity == "error"]

    @property
    def warnings(self) -> List[ValidationIssue]:
        return [i for i in self.issues if i.severity == "warning"]


class EnvValidator:
    """Validates EnvFile instances against configurable rules."""

    def __init__(
        self,
        required_keys: Optional[List[str]] = None,
        allow_empty_values: bool = True,
        max_key_length: int = 128,
    ) -> None:
        self.required_keys: List[str] = required_keys or []
        self.allow_empty_values = allow_empty_values
        self.max_key_length = max_key_length

    def validate(self, env_file: EnvFile) -> ValidationResult:
        result = ValidationResult()

        present_keys = set(env_file.keys())

        for key in self.required_keys:
            if key not in present_keys:
                result.issues.append(
                    ValidationIssue(key=key, message="Required key is missing", severity="error")
                )

        for entry in env_file.entries:
            if entry.key is None:
                continue

            if len(entry.key) > self.max_key_length:
                result.issues.append(
                    ValidationIssue(
                        key=entry.key,
                        message=f"Key exceeds maximum length of {self.max_key_length}",
                        severity="error",
                    )
                )

            if not self.allow_empty_values and entry.value == "":
                result.issues.append(
                    ValidationIssue(
                        key=entry.key,
                        message="Empty value is not allowed",
                        severity="warning",
                    )
                )

            if " " in entry.key:
                result.issues.append(
                    ValidationIssue(
                        key=entry.key,
                        message="Key contains whitespace",
                        severity="error",
                    )
                )

        return result
