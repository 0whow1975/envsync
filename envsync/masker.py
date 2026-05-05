"""Secret masking support for sensitive environment variable values."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Iterable

# Default patterns that indicate a value is likely a secret
DEFAULT_SECRET_PATTERNS: list[str] = [
    r".*secret.*",
    r".*password.*",
    r".*passwd.*",
    r".*token.*",
    r".*api[_-]?key.*",
    r".*private[_-]?key.*",
    r".*auth.*",
    r".*credential.*",
]

MASK_PLACEHOLDER = "***"


@dataclass
class MaskConfig:
    """Configuration for the secret masker."""

    patterns: list[str] = field(default_factory=lambda: list(DEFAULT_SECRET_PATTERNS))
    mask: str = MASK_PLACEHOLDER
    case_sensitive: bool = False


class SecretMasker:
    """Masks sensitive values in environment variable entries."""

    def __init__(self, config: MaskConfig | None = None) -> None:
        self.config = config or MaskConfig()
        flags = 0 if self.config.case_sensitive else re.IGNORECASE
        self._compiled = [
            re.compile(pattern, flags) for pattern in self.config.patterns
        ]

    def is_secret(self, key: str) -> bool:
        """Return True if the key matches any secret pattern."""
        return any(pattern.fullmatch(key) for pattern in self._compiled)

    def mask_value(self, key: str, value: str) -> str:
        """Return masked placeholder if key is a secret, otherwise the original value."""
        if self.is_secret(key):
            return self.config.mask
        return value

    def mask_dict(self, env: dict[str, str]) -> dict[str, str]:
        """Return a new dict with secret values replaced by the mask placeholder."""
        return {k: self.mask_value(k, v) for k, v in env.items()}

    def add_pattern(self, pattern: str) -> None:
        """Add a custom pattern to the masker at runtime."""
        flags = 0 if self.config.case_sensitive else re.IGNORECASE
        self.config.patterns.append(pattern)
        self._compiled.append(re.compile(pattern, flags))


def mask_keys(keys: Iterable[str], config: MaskConfig | None = None) -> list[str]:
    """Convenience function: return a list of keys that would be masked."""
    masker = SecretMasker(config)
    return [k for k in keys if masker.is_secret(k)]
