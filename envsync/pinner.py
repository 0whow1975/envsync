"""Pin env file values to a locked snapshot, detecting drift from pinned state."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envsync.parser import EnvFile


@dataclass
class PinOptions:
    """Options controlling pin behaviour."""
    ignore_keys: List[str] = field(default_factory=list)
    case_sensitive: bool = True


@dataclass
class PinViolation:
    """A single key that has drifted from its pinned value."""
    key: str
    pinned_value: str
    current_value: Optional[str]  # None when the key is missing

    def __str__(self) -> str:
        if self.current_value is None:
            return f"{self.key}: pinned={self.pinned_value!r} (missing in current)"
        return f"{self.key}: pinned={self.pinned_value!r} current={self.current_value!r}"


@dataclass
class PinResult:
    """Result of comparing a live env file against a pinned baseline."""
    violations: List[PinViolation] = field(default_factory=list)
    checked_keys: int = 0

    @property
    def is_pinned(self) -> bool:
        """True when no drift was detected."""
        return len(self.violations) == 0

    @property
    def violation_count(self) -> int:
        return len(self.violations)

    def as_dict(self) -> dict:
        return {
            "is_pinned": self.is_pinned,
            "checked_keys": self.checked_keys,
            "violations": [
                {
                    "key": v.key,
                    "pinned_value": v.pinned_value,
                    "current_value": v.current_value,
                }
                for v in self.violations
            ],
        }


def pin_check(
    pinned: EnvFile,
    current: EnvFile,
    options: Optional[PinOptions] = None,
) -> PinResult:
    """Compare *current* against the *pinned* baseline and return drift info.

    Only keys present in *pinned* are checked; extra keys in *current* are
    silently ignored (use the comparator module if you need symmetrical diff).
    """
    if options is None:
        options = PinOptions()

    ignore = (
        {k.lower() for k in options.ignore_keys}
        if not options.case_sensitive
        else set(options.ignore_keys)
    )

    violations: List[PinViolation] = []
    checked = 0

    for entry in pinned.entries:
        if entry.comment or entry.key is None:
            continue

        key = entry.key
        cmp_key = key if options.case_sensitive else key.lower()

        if cmp_key in ignore:
            continue

        checked += 1
        current_entry = current.get(key)
        current_value = current_entry.value if current_entry is not None else None

        if current_value != entry.value:
            violations.append(
                PinViolation(
                    key=key,
                    pinned_value=entry.value or "",
                    current_value=current_value,
                )
            )

    return PinResult(violations=violations, checked_keys=checked)
