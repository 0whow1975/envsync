"""Sync .env files based on diff results."""

from pathlib import Path
from typing import Optional

from envsync.diff import ChangeType, DiffResult
from envsync.parser import EnvFile, parse_env_file


class SyncOptions:
    """Configuration options for syncing."""

    def __init__(
        self,
        add_missing: bool = True,
        remove_extra: bool = False,
        update_changed: bool = True,
        dry_run: bool = False,
    ):
        self.add_missing = add_missing
        self.remove_extra = remove_extra
        self.update_changed = update_changed
        self.dry_run = dry_run


class SyncResult:
    """Result of a sync operation."""

    def __init__(self):
        self.added: list[str] = []
        self.removed: list[str] = []
        self.updated: list[str] = []
        self.skipped: list[str] = []

    @property
    def total_changes(self) -> int:
        return len(self.added) + len(self.removed) + len(self.updated)

    def __repr__(self) -> str:
        return (
            f"SyncResult(added={len(self.added)}, removed={len(self.removed)}, "
            f"updated={len(self.updated)}, skipped={len(self.skipped)})"
        )


def sync_env_files(
    diff: DiffResult,
    target_path: Path,
    options: Optional[SyncOptions] = None,
) -> SyncResult:
    """Apply diff changes to the target .env file."""
    if options is None:
        options = SyncOptions()

    result = SyncResult()
    target_env = parse_env_file(target_path)
    lines = _read_lines(target_path)

    for entry in diff.entries:
        if entry.change_type == ChangeType.ADDED and options.add_missing:
            lines.append(f"{entry.key}={entry.source_value or ''}\n")
            result.added.append(entry.key)
        elif entry.change_type == ChangeType.REMOVED and options.remove_extra:
            lines = [l for l in lines if not l.startswith(f"{entry.key}=")]
            result.removed.append(entry.key)
        elif entry.change_type == ChangeType.CHANGED and options.update_changed:
            lines = [
                f"{entry.key}={entry.source_value or ''}\n"
                if l.startswith(f"{entry.key}=")
                else l
                for l in lines
            ]
            result.updated.append(entry.key)
        else:
            if entry.change_type != ChangeType.UNCHANGED:
                result.skipped.append(entry.key)

    if not options.dry_run:
        target_path.write_text("".join(lines))

    return result


def _read_lines(path: Path) -> list[str]:
    """Read file lines, ensuring trailing newline on last line."""
    if not path.exists():
        return []
    content = path.read_text()
    lines = content.splitlines(keepends=True)
    if lines and not lines[-1].endswith("\n"):
        lines[-1] += "\n"
    return lines
