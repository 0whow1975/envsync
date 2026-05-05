"""Tests for the export CLI sub-command."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from envsync.cli_export import cmd_export


def _write(path: Path, content: str) -> Path:
    path.write_text(content, encoding="utf-8")
    return path


@pytest.fixture()
def source_env(tmp_path) -> Path:
    return _write(
        tmp_path / "source.env",
        "APP_NAME=myapp\nSECRET_KEY=old_secret\nDB_HOST=localhost\n",
    )


@pytest.fixture()
def target_env(tmp_path) -> Path:
    return _write(
        tmp_path / "target.env",
        "APP_NAME=myapp\nSECRET_KEY=new_secret\nNEW_VAR=hello\n",
    )


class _Args:
    """Minimal stand-in for argparse.Namespace."""

    def __init__(self, source, target, output, fmt="json", include_unchanged=False, no_mask=False):
        self.source = source
        self.target = target
        self.output = output
        self.format = fmt
        self.include_unchanged = include_unchanged
        self.no_mask = no_mask


def test_cmd_export_returns_zero(tmp_path, source_env, target_env):
    out = tmp_path / "result.json"
    args = _Args(source_env, target_env, out)
    assert cmd_export(args) == 0


def test_cmd_export_creates_output_file(tmp_path, source_env, target_env):
    out = tmp_path / "result.json"
    cmd_export(_Args(source_env, target_env, out))
    assert out.exists()


def test_cmd_export_json_content(tmp_path, source_env, target_env):
    out = tmp_path / "result.json"
    cmd_export(_Args(source_env, target_env, out))
    data = json.loads(out.read_text())
    keys = [r["key"] for r in data]
    assert "SECRET_KEY" in keys
    assert "NEW_VAR" in keys


def test_cmd_export_csv_format(tmp_path, source_env, target_env):
    out = tmp_path / "result.csv"
    cmd_export(_Args(source_env, target_env, out, fmt="csv"))
    content = out.read_text()
    assert "key,change_type" in content


def test_cmd_export_masks_secrets_by_default(tmp_path, source_env, target_env):
    out = tmp_path / "result.json"
    cmd_export(_Args(source_env, target_env, out))
    data = json.loads(out.read_text())
    secret_row = next((r for r in data if r["key"] == "SECRET_KEY"), None)
    assert secret_row is not None
    assert secret_row.get("new_value") != "new_secret"


def test_cmd_export_no_mask_exposes_values(tmp_path, source_env, target_env):
    out = tmp_path / "result.json"
    cmd_export(_Args(source_env, target_env, out, no_mask=True))
    data = json.loads(out.read_text())
    secret_row = next((r for r in data if r["key"] == "SECRET_KEY"), None)
    assert secret_row["new_value"] == "new_secret"
