"""Formatting utilities for displaying diff results."""
from typing import Optional
from envsync.diff import DiffResult, DiffEntry, ChangeType
from envsync.masker import SecretMasker

COLORS = {
    "green": "\033[92m",
    "red": "\033[91m",
    "yellow": "\033[93m",
    "reset": "\033[0m",
    "dim": "\033[2m",
}


def _colorize(text: str, color: str, use_color: bool) -> str:
    if not use_color:
        return text
    return f"{COLORS.get(color, '')}{text}{COLORS['reset']}"


def _val(value: Optional[str], masker: Optional[SecretMasker], key: str) -> str:
    if value is None:
        return "(unset)"
    if masker and masker.is_secret(key):
        return masker.mask_value(value)
    return value


def _format_entry(
    entry: DiffEntry,
    masker: Optional[SecretMasker] = None,
    use_color: bool = True,
) -> str:
    key = entry.key
    if entry.change == ChangeType.ADDED:
        line = f"+ {key}={_val(entry.source_value, masker, key)}"
        return _colorize(line, "green", use_color)
    elif entry.change == ChangeType.REMOVED:
        line = f"- {key}={_val(entry.target_value, masker, key)}"
        return _colorize(line, "red", use_color)
    elif entry.change == ChangeType.CHANGED:
        src = _val(entry.source_value, masker, key)
        tgt = _val(entry.target_value, masker, key)
        line = f"~ {key}: {tgt} \u2192 {src}"
        return _colorize(line, "yellow", use_color)
    else:
        line = f"  {key}={_val(entry.source_value, masker, key)}"
        return _colorize(line, "dim", use_color)


def format_diff(
    diff: DiffResult,
    masker: Optional[SecretMasker] = None,
    show_unchanged: bool = False,
    use_color: bool = True,
) -> str:
    lines = []
    for entry in diff.entries:
        if entry.change == ChangeType.UNCHANGED and not show_unchanged:
            continue
        lines.append(_format_entry(entry, masker=masker, use_color=use_color))
    return "\n".join(lines)


def format_summary(diff: DiffResult, use_color: bool = True) -> str:
    """Return a one-line summary of the diff result counts by change type."""
    counts = {change: 0 for change in ChangeType}
    for entry in diff.entries:
        counts[entry.change] += 1

    parts = [
        _colorize(f"+{counts[ChangeType.ADDED]} added", "green", use_color),
        _colorize(f"-{counts[ChangeType.REMOVED]} removed", "red", use_color),
        _colorize(f"~{counts[ChangeType.CHANGED]} changed", "yellow", use_color),
        _colorize(f"{counts[ChangeType.UNCHANGED]} unchanged", "dim", use_color),
    ]
    return "  ".join(parts)
