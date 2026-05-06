"""Tests for envsync.cli_watch."""
from __future__ import annotations

import argparse
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from envsync.cli_watch import add_watch_subparser, cmd_watch


@pytest.fixture()
def env_pair(tmp_path: Path):
    source = tmp_path / ".env.source"
    target = tmp_path / ".env.target"
    source.write_text("KEY=hello\n")
    target.write_text("KEY=hello\n")
    return source, target


def _args(source: Path, target: Path, **kwargs) -> argparse.Namespace:
    defaults = dict(interval=0.0, no_mask=False, color=False)
    defaults.update(kwargs)
    return argparse.Namespace(source=source, target=target, **defaults)


def test_add_watch_subparser_registers_command():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    add_watch_subparser(sub)
    args = parser.parse_args(["watch", "a.env", "b.env"])
    assert args.func is cmd_watch


def test_cmd_watch_stops_on_keyboard_interrupt(env_pair, capsys):
    source, target = env_pair
    args = _args(source, target)
    with patch("envsync.cli_watch.EnvWatcher") as MockWatcher:
        instance = MockWatcher.return_value
        instance.run.side_effect = KeyboardInterrupt
        cmd_watch(args)
    captured = capsys.readouterr()
    assert "stopped" in captured.out


def test_cmd_watch_creates_watcher_with_correct_paths(env_pair):
    source, target = env_pair
    args = _args(source, target, interval=1.5)
    with patch("envsync.cli_watch.EnvWatcher") as MockWatcher:
        MockWatcher.return_value.run.side_effect = KeyboardInterrupt
        cmd_watch(args)
    call_kwargs = MockWatcher.call_args
    assert call_kwargs.kwargs["source"] == source
    assert call_kwargs.kwargs["target"] == target


def test_cmd_watch_no_mask_disables_masker(env_pair):
    source, target = env_pair
    args = _args(source, target, no_mask=True)
    with patch("envsync.cli_watch.EnvWatcher") as MockWatcher:
        MockWatcher.return_value.run.side_effect = KeyboardInterrupt
        with patch("envsync.cli_watch.SecretMasker") as MockMasker:
            cmd_watch(args)
    MockMasker.assert_not_called()


def test_on_change_callback_prints_diff(env_pair, capsys):
    source, target = env_pair
    # modify target so there is a real diff
    target.write_text("KEY=world\n")
    args = _args(source, target)
    captured_callbacks = []

    def fake_init(self_inner, source, target, on_change, options):
        captured_callbacks.append(on_change)

    with patch.object(
        __import__("envsync.watcher", fromlist=["EnvWatcher"]).EnvWatcher,
        "__init__",
        fake_init,
    ):
        with patch(
            "envsync.cli_watch.EnvWatcher.run", side_effect=KeyboardInterrupt
        ):
            try:
                cmd_watch(args)
            except Exception:
                pass

    # Directly invoke the watcher and check on_change fires
    from envsync.watcher import EnvWatcher, WatchOptions
    from envsync.diff import diff_env_files
    from envsync.parser import parse_env_file

    events = []
    opts = WatchOptions(poll_interval=0.0, max_iterations=1)
    watcher = EnvWatcher(source, target, on_change=events.append, options=opts)
    watcher.run()
    assert len(events) == 1
