"""Audit log for sync operations — records what changed, when, and by whom."""

from __future__ import annotations

import getpass
import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from envsync.diff import DiffResult, ChangeType


@dataclass
class AuditEntry:
    key: str
    change_type: str
    old_value: Optional[str]
    new_value: Optional[str]

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "change_type": self.change_type,
            "old_value": self.old_value,
            "new_value": self.new_value,
        }


@dataclass
class AuditRecord:
    timestamp: str
    user: str
    source: str
    target: str
    entries: List[AuditEntry] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "user": self.user,
            "source": self.source,
            "target": self.target,
            "entries": [e.to_dict() for e in self.entries],
        }


def build_audit_record(
    diff: DiffResult,
    source: str,
    target: str,
    user: Optional[str] = None,
    mask_values: bool = True,
) -> AuditRecord:
    """Build an AuditRecord from a DiffResult."""
    now = datetime.now(timezone.utc).isoformat()
    resolved_user = user or _current_user()

    entries: List[AuditEntry] = []
    for diff_entry in diff.entries:
        if diff_entry.change_type == ChangeType.UNCHANGED:
            continue
        old_val = diff_entry.old_value if not mask_values else _mask(diff_entry.old_value)
        new_val = diff_entry.new_value if not mask_values else _mask(diff_entry.new_value)
        entries.append(
            AuditEntry(
                key=diff_entry.key,
                change_type=diff_entry.change_type.value,
                old_value=old_val,
                new_value=new_val,
            )
        )

    return AuditRecord(
        timestamp=now,
        user=resolved_user,
        source=source,
        target=target,
        entries=entries,
    )


def write_audit_log(record: AuditRecord, path: str | Path) -> None:
    """Append an AuditRecord as a JSON line to the given log file."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record.to_dict()) + "\n")


def _mask(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    return "***"


def _current_user() -> str:
    try:
        return getpass.getuser()
    except Exception:
        return "unknown"
