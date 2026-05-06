"""Watch .env files for changes and trigger diff/sync actions."""
from __future__ import annotations

import time
import hashlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional

from envsync.parser import parse_env_file, EnvFile
from envsync.diff import diff_env_files, DiffResult


@dataclass
class WatchOptions:
    poll_interval: float = 1.0
    max_iterations: Optional[int] = None  # None = run forever


@dataclass
class WatchEvent:
    source_path: Path
    target_path: Path
    diff: DiffResult
    iteration: int


def _file_hash(path: Path) -> str:
    """Return MD5 hex digest of file contents."""
    try:
        return hashlib.md5(path.read_bytes()).hexdigest()
    except FileNotFoundError:
        return ""


class EnvWatcher:
    """Poll two .env files and invoke a callback when they diverge."""

    def __init__(
        self,
        source: Path,
        target: Path,
        on_change: Callable[[WatchEvent], None],
        options: Optional[WatchOptions] = None,
    ) -> None:
        self.source = Path(source)
        self.target = Path(target)
        self.on_change = on_change
        self.options = options or WatchOptions()
        self._last_hashes: tuple[str, str] = ("", "")

    def _hashes(self) -> tuple[str, str]:
        return _file_hash(self.source), _file_hash(self.target)

    def _changed(self) -> bool:
        current = self._hashes()
        if current != self._last_hashes:
            self._last_hashes = current
            return True
        return False

    def check_once(self, iteration: int = 0) -> Optional[WatchEvent]:
        """Check for changes once; return a WatchEvent if changed, else None."""
        if not self._changed():
            return None
        source_env: EnvFile = parse_env_file(self.source)
        target_env: EnvFile = parse_env_file(self.target)
        diff = diff_env_files(source_env, target_env)
        event = WatchEvent(
            source_path=self.source,
            target_path=self.target,
            diff=diff,
            iteration=iteration,
        )
        self.on_change(event)
        return event

    def run(self) -> None:
        """Block and poll until max_iterations is reached (or forever)."""
        iteration = 0
        while True:
            self.check_once(iteration)
            iteration += 1
            if (
                self.options.max_iterations is not None
                and iteration >= self.options.max_iterations
            ):
                break
            time.sleep(self.options.poll_interval)
