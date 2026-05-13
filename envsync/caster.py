"""Type casting for .env values — infer or coerce Python types from string values."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from envsync.parser import EnvFile


_TRUE_VALUES = {"1", "true", "yes", "on"}
_FALSE_VALUES = {"0", "false", "no", "off"}


@dataclass
class CastOptions:
    cast_bools: bool = True
    cast_ints: bool = True
    cast_floats: bool = True
    none_strings: frozenset[str] = field(
        default_factory=lambda: frozenset({"null", "none", ""})
    )


@dataclass
class CastResult:
    key: str
    raw: str
    value: Any
    cast_type: str  # "str" | "int" | "float" | "bool" | "none"

    def __repr__(self) -> str:  # pragma: no cover
        return f"CastResult({self.key!r}, {self.value!r}, type={self.cast_type})"


def cast_value(raw: str, options: CastOptions | None = None) -> tuple[Any, str]:
    """Return *(value, type_name)* for *raw* according to *options*."""
    opts = options or CastOptions()

    lower = raw.strip().lower()

    if lower in opts.none_strings:
        return None, "none"

    if opts.cast_bools:
        if lower in _TRUE_VALUES:
            return True, "bool"
        if lower in _FALSE_VALUES:
            return False, "bool"

    if opts.cast_ints:
        try:
            return int(raw), "int"
        except ValueError:
            pass

    if opts.cast_floats:
        try:
            return float(raw), "float"
        except ValueError:
            pass

    return raw, "str"


def cast_env(env: EnvFile, options: CastOptions | None = None) -> list[CastResult]:
    """Cast every entry in *env* and return a list of :class:`CastResult`."""
    opts = options or CastOptions()
    results: list[CastResult] = []
    for entry in env.entries:
        if entry.key is None:
            continue
        value, cast_type = cast_value(entry.value or "", opts)
        results.append(
            CastResult(key=entry.key, raw=entry.value or "", value=value, cast_type=cast_type)
        )
    return results
