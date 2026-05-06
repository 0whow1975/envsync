"""Snapshot support: save and restore .env file states for rollback."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from envsync.parser import EnvFile, parse_env_file


@dataclass
class Snapshot:
    """A point-in-time capture of an EnvFile's contents."""

    path: str
    captured_at: str
    entries: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "path": self.path,
            "captured_at": self.captured_at,
            "entries": self.entries,
        }

    @staticmethod
    def from_dict(data: dict) -> "Snapshot":
        snap = Snapshot(
            path=data["path"],
            captured_at=data["captured_at"],
        )
        snap.entries = data.get("entries", {})
        return snap


def take_snapshot(env_file: EnvFile) -> Snapshot:
    """Capture the current state of an EnvFile as a Snapshot."""
    captured_at = datetime.now(timezone.utc).isoformat()
    entries = {entry.key: entry.value for entry in env_file.entries if entry.key}
    return Snapshot(path=env_file.path, captured_at=captured_at, entries=entries)


def save_snapshot(snapshot: Snapshot, snapshot_dir: str) -> Path:
    """Persist a snapshot to *snapshot_dir* as a JSON file.

    The filename encodes the original env path and timestamp so multiple
    snapshots for the same file can coexist.
    """
    os.makedirs(snapshot_dir, exist_ok=True)
    safe_name = Path(snapshot.path).name.replace(".", "_")
    ts = snapshot.captured_at.replace(":", "-").replace("+", "Z")
    filename = f"{safe_name}__{ts}.json"
    dest = Path(snapshot_dir) / filename
    dest.write_text(json.dumps(snapshot.to_dict(), indent=2))
    return dest


def load_snapshot(snapshot_path: str) -> Snapshot:
    """Load a previously saved snapshot from disk."""
    data = json.loads(Path(snapshot_path).read_text())
    return Snapshot.from_dict(data)


def list_snapshots(snapshot_dir: str, env_filename: Optional[str] = None) -> List[Path]:
    """Return snapshot files in *snapshot_dir*, optionally filtered by env filename."""
    base = Path(snapshot_dir)
    if not base.exists():
        return []
    files = sorted(base.glob("*.json"))
    if env_filename:
        safe = env_filename.replace(".", "_")
        files = [f for f in files if f.name.startswith(safe + "__")]
    return files


def restore_snapshot(snapshot: Snapshot, dest_path: Optional[str] = None) -> Path:
    """Write snapshot entries back to *dest_path* (defaults to original path)."""
    target = Path(dest_path or snapshot.path)
    lines = [f"{k}={v}\n" for k, v in snapshot.entries.items()]
    target.write_text("".join(lines))
    return target
