"""Format diff results for human-readable output, with optional secret masking."""

from __future__ import annotations

from envsync.diff import ChangeType, DiffEntry, DiffResult
from envsync.masker import SecretMasker

# ANSI colour codes
_RED = "\033[31m"
_GREEN = "\033[32m"
_YELLOW = "\033[33m"
_DIM = "\033[2m"
_RESET = "\033[0m"

_CHANGE_SYMBOL: dict[ChangeType, str] = {
    ChangeType.ADDED: "+",
    ChangeType.REMOVED: "-",
    ChangeType.MODIFIED: "~",
    ChangeType.UNCHANGED: " ",
}

_CHANGE_COLOR: dict[ChangeType, str] = {
    ChangeType.ADDED: _GREEN,
    ChangeType.REMOVED: _RED,
    ChangeType.MODIFIED: _YELLOW,
    ChangeType.UNCHANGED: _DIM,
}


def _format_entry(
    entry: DiffEntry,
    masker: SecretMasker | None,
    color: bool,
) -> str:
    symbol = _CHANGE_SYMBOL[entry.change_type]

    def _val(v: str | None) -> str:
        if v is None:
            return "(none)"
        if masker and masker.is_secret(entry.key):
            return masker.config.mask
        return v

    if entry.change_type == ChangeType.MODIFIED:
        line = f"{symbol} {entry.key}: {_val(entry.source_value)} -> {_val(entry.target_value)}"
    elif entry.change_type == ChangeType.ADDED:
        line = f"{symbol} {entry.key}={_val(entry.target_value)}"
    elif entry.change_type == ChangeType.REMOVED:
        line = f"{symbol} {entry.key}={_val(entry.source_value)}"
    else:
        line = f"{symbol} {entry.key}={_val(entry.source_value)}"

    if color:
        c = _CHANGE_COLOR[entry.change_type]
        return f"{c}{line}{_RESET}"
    return line


def format_diff(
    result: DiffResult,
    *,
    mask_secrets: bool = True,
    show_unchanged: bool = False,
    color: bool = True,
) -> str:
    """Render a DiffResult as a human-readable string.

    Args:
        result: The diff to render.
        mask_secrets: Whether to hide sensitive values.
        show_unchanged: Whether to include unchanged keys in the output.
        color: Whether to emit ANSI colour codes.

    Returns:
        A multi-line string ready to print to a terminal.
    """
    masker = SecretMasker() if mask_secrets else None
    lines: list[str] = []

    for entry in result.entries:
        if not show_unchanged and entry.change_type == ChangeType.UNCHANGED:
            continue
        lines.append(_format_entry(entry, masker, color))

    if not lines:
        return "No differences found."

    return "\n".join(lines)
