"""Export diff results and reports to various file formats."""

from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Literal

from envsync.diff import DiffResult
from envsync.masker import SecretMasker

ExportFormat = Literal["json", "csv", "dotenv"]


@dataclass
class ExportOptions:
    format: ExportFormat = "json"
    mask_secrets: bool = True
    include_unchanged: bool = False


def _entry_to_dict(entry, masker: SecretMasker | None) -> dict:
    value = entry.value
    if masker and entry.key and masker.is_secret(entry.key):
        value = masker.mask_value(value) if value is not None else None
    return {
        "key": entry.key,
        "change_type": entry.change_type.value,
        "old_value": entry.old_value,
        "new_value": value,
    }


def export_diff(
    diff: DiffResult,
    destination: Path,
    options: ExportOptions | None = None,
    masker: SecretMasker | None = None,
) -> None:
    """Export a DiffResult to *destination* in the requested format."""
    if options is None:
        options = ExportOptions()

    entries = diff.entries
    if not options.include_unchanged:
        entries = [e for e in entries if e.change_type.value != "unchanged"]

    rows = [_entry_to_dict(e, masker if options.mask_secrets else None) for e in entries]

    destination.parent.mkdir(parents=True, exist_ok=True)

    if options.format == "json":
        destination.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    elif options.format == "csv":
        with destination.open("w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=["key", "change_type", "old_value", "new_value"])
            writer.writeheader()
            writer.writerows(rows)
    elif options.format == "dotenv":
        lines = []
        for row in rows:
            val = row["new_value"] if row["new_value"] is not None else row["old_value"]
            lines.append(f"{row['key']}={val or ''}")
        destination.write_text("\n".join(lines) + "\n", encoding="utf-8")
    else:
        raise ValueError(f"Unsupported export format: {options.format}")
