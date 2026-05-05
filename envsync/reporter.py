"""Report generation for env diff and sync operations."""
from dataclasses import dataclass
from typing import Optional
from envsync.diff import DiffResult, ChangeType
from envsync.masker import SecretMasker
from envsync.formatter import format_diff


@dataclass
class ReportOptions:
    mask_secrets: bool = True
    show_unchanged: bool = False
    use_color: bool = True
    summary_only: bool = False


@dataclass
class Report:
    title: str
    body: str
    summary: str

    def __str__(self) -> str:
        parts = [self.title, self.body, self.summary]
        return "\n".join(p for p in parts if p)


def _build_summary(diff: DiffResult) -> str:
    added = len(diff.by_type(ChangeType.ADDED))
    removed = len(diff.by_type(ChangeType.REMOVED))
    changed = len(diff.by_type(ChangeType.CHANGED))
    unchanged = len(diff.by_type(ChangeType.UNCHANGED))
    parts = []
    if added:
        parts.append(f"+{added} added")
    if removed:
        parts.append(f"-{removed} removed")
    if changed:
        parts.append(f"~{changed} changed")
    if unchanged:
        parts.append(f"={unchanged} unchanged")
    if not parts:
        return "No differences found."
    return "Summary: " + ", ".join(parts)


def generate_report(
    diff: DiffResult,
    source_path: str,
    target_path: str,
    masker: Optional[SecretMasker] = None,
    options: Optional[ReportOptions] = None,
) -> Report:
    if options is None:
        options = ReportOptions()

    title = f"Diff Report: {source_path} → {target_path}"

    if options.summary_only:
        body = ""
    else:
        body = format_diff(
            diff,
            masker=masker if options.mask_secrets else None,
            show_unchanged=options.show_unchanged,
            use_color=options.use_color,
        )

    summary = _build_summary(diff)
    return Report(title=title, body=body, summary=summary)
