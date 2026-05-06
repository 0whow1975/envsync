"""Variable interpolation support for .env files.

Supports ${VAR} and $VAR style references within values.
"""
from __future__ import annotations

import re
from typing import Dict, Optional

from envsync.parser import EnvFile

_BRACE_RE = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}")
_BARE_RE = re.compile(r"\$([A-Za-z_][A-Za-z0-9_]*)")


def _resolve_value(
    value: str,
    context: Dict[str, str],
    default: str = "",
) -> str:
    """Replace all variable references in *value* using *context*."""

    def _replace(match: re.Match) -> str:  # type: ignore[type-arg]
        return context.get(match.group(1), default)

    result = _BRACE_RE.sub(_replace, value)
    result = _BARE_RE.sub(_replace, result)
    return result


def interpolate(
    env: EnvFile,
    extra: Optional[Dict[str, str]] = None,
    default: str = "",
) -> Dict[str, str]:
    """Return a dict of all keys in *env* with variable references resolved.

    Resolution order:
      1. Keys already resolved within the same file (top-to-bottom).
      2. Keys supplied in *extra* (e.g. OS environment).
      3. *default* for any reference that cannot be resolved.

    Parameters
    ----------
    env:
        Parsed :class:`~envsync.parser.EnvFile` to interpolate.
    extra:
        Optional additional mapping consulted when a reference is not found
        among the file's own keys.
    default:
        String substituted for unresolvable references (default ``""``).
    """
    extra = extra or {}
    resolved: Dict[str, str] = {}

    for key in env.keys():
        raw = env.get(key) or ""
        context = {**extra, **resolved}
        resolved[key] = _resolve_value(raw, context, default)

    return resolved
