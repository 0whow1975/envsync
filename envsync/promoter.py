"""Promote .env values from one environment to another with optional filtering."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, List, Optional

from envsync.diff import DiffResult, ChangeType, diff_env_files
from envsync.parser import EnvFile
from envsync.syncer import SyncOptions, Syncer, SyncResult


@dataclass
class PromoteOptions:
    """Options controlling which keys are promoted and how."""

    # Only promote keys whose names match this predicate (None = promote all)
    key_filter: Optional[Callable[[str], bool]] = None

    # Change types to include; defaults to ADDED and CHANGED only
    include_change_types: List[ChangeType] = field(
        default_factory=lambda: [ChangeType.ADDED, ChangeType.CHANGED]
    )

    # When True, also overwrite keys that are REMOVED in source (i.e. delete them)
    allow_removals: bool = False

    # Passed through to the underlying Syncer
    dry_run: bool = False


@dataclass
class PromoteResult:
    """Outcome of a promotion operation."""

    sync_result: SyncResult
    skipped_keys: List[str]

    @property
    def promoted_count(self) -> int:
        return self.sync_result.total_changes

    @property
    def skipped_count(self) -> int:
        return len(self.skipped_keys)


def promote(
    source: EnvFile,
    target: EnvFile,
    options: Optional[PromoteOptions] = None,
) -> PromoteResult:
    """Promote changes from *source* into *target* according to *options*.

    Returns a :class:`PromoteResult` describing what was (or would be) changed.
    """
    if options is None:
        options = PromoteOptions()

    full_diff: DiffResult = diff_env_files(source, target)

    allowed_types = set(options.include_change_types)
    if options.allow_removals:
        allowed_types.add(ChangeType.REMOVED)

    skipped: List[str] = []
    filtered_entries = []

    for entry in full_diff.entries:
        if entry.change_type == ChangeType.UNCHANGED:
            filtered_entries.append(entry)
            continue
        if entry.change_type not in allowed_types:
            skipped.append(entry.key)
            continue
        if options.key_filter is not None and not options.key_filter(entry.key):
            skipped.append(entry.key)
            continue
        filtered_entries.append(entry)

    from envsync.diff import DiffResult as DR
    filtered_diff = DR(entries=filtered_entries)

    sync_opts = SyncOptions(dry_run=options.dry_run)
    syncer = Syncer(source, target, sync_opts)
    sync_result = syncer.apply(filtered_diff)

    return PromoteResult(sync_result=sync_result, skipped_keys=skipped)
