"""Tests for envsync.watcher."""
from __future__ import annotations

import time
from pathlib import Path
from typing import List

import pytest

from envsync.watcher import EnvWatcher, WatchEvent, WatchOptions


@pytest.fixture()
def env_files(tmp_path: Path):
    source = tmp_path / ".env.source"
    target = tmp_path / ".env.target"
    source.write_text("KEY1=value1\nKEY2=value2\n")
    target.write_text("KEY1=value1\nKEY2=value2\n")
    return source, target


def _collect_events(source: Path, target: Path, iterations: int) -> List[WatchEvent]:
    events: List[WatchEvent] = []
    opts = WatchOptions(poll_interval=0.0, max_iterations=iterations)
    watcher = EnvWatcher(source, target, on_change=events.append, options=opts)
    watcher.run()
    return events


def test_no_event_when_files_unchanged(env_files):
    source, target = env_files
    events = _collect_events(source, target, iterations=3)
    # First iteration always fires (hash goes from '' to real); subsequent ones should not
    assert len(events) == 1


def test_event_fired_on_initial_check(env_files):
    source, target = env_files
    events: List[WatchEvent] = []
    opts = WatchOptions(poll_interval=0.0, max_iterations=1)
    watcher = EnvWatcher(source, target, on_change=events.append, options=opts)
    watcher.run()
    assert len(events) == 1
    assert events[0].iteration == 0


def test_event_contains_diff(env_files):
    source, target = env_files
    events: List[WatchEvent] = []
    opts = WatchOptions(poll_interval=0.0, max_iterations=1)
    watcher = EnvWatcher(source, target, on_change=events.append, options=opts)
    watcher.run()
    diff = events[0].diff
    assert diff is not None
    assert not diff.has_changes()


def test_event_fired_when_target_changes(env_files):
    source, target = env_files
    events: List[WatchEvent] = []
    opts = WatchOptions(poll_interval=0.0, max_iterations=1)
    watcher = EnvWatcher(source, target, on_change=events.append, options=opts)
    # prime the hash
    watcher.check_once(iteration=0)
    events.clear()

    # mutate target
    target.write_text("KEY1=value1\nKEY2=changed\n")
    watcher.check_once(iteration=1)

    assert len(events) == 1
    assert events[0].diff.has_changes()


def test_event_paths_are_correct(env_files):
    source, target = env_files
    events: List[WatchEvent] = []
    opts = WatchOptions(poll_interval=0.0, max_iterations=1)
    watcher = EnvWatcher(source, target, on_change=events.append, options=opts)
    watcher.run()
    assert events[0].source_path == source
    assert events[0].target_path == target


def test_check_once_returns_none_when_no_change(env_files):
    source, target = env_files
    watcher = EnvWatcher(source, target, on_change=lambda e: None)
    watcher.check_once()  # prime
    result = watcher.check_once()
    assert result is None
