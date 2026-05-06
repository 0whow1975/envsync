"""Optional hooks that can be registered with EnvWatcher for side-effects."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from envsync.watcher import WatchEvent


# Type alias for hook callables
WatchHook = Callable[[WatchEvent], None]


def log_to_file_hook(log_path: Path) -> WatchHook:
    """Return a hook that appends a JSON line to *log_path* on each change."""

    def _hook(event: WatchEvent) -> None:
        record = {
            "timestamp": datetime.now(tz=timezone.utc).isoformat(),
            "source": str(event.source_path),
            "target": str(event.target_path),
            "iteration": event.iteration,
            "added": len(event.diff.by_type("added")),
            "removed": len(event.diff.by_type("removed")),
            "changed": len(event.diff.by_type("changed")),
            "unchanged": len(event.diff.by_type("unchanged")),
        }
        with log_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record) + "\n")

    return _hook


def alert_on_removed_keys_hook(
    alert_fn: Callable[[str], None] | None = None,
) -> WatchHook:
    """Return a hook that calls *alert_fn* when keys are removed from target."""
    _alert = alert_fn or print

    def _hook(event: WatchEvent) -> None:
        removed = event.diff.by_type("removed")
        for entry in removed:
            _alert(
                f"[envsync ALERT] key '{entry.key}' removed from "
                f"{event.target_path} (iteration={event.iteration})"
            )

    return _hook


def compose_hooks(*hooks: WatchHook) -> WatchHook:
    """Combine multiple hooks into a single callable."""

    def _combined(event: WatchEvent) -> None:
        for hook in hooks:
            hook(event)

    return _combined
