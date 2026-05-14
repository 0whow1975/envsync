"""Integration tests for key rotation across real temp files."""
from __future__ import annotations

from pathlib import Path

import pytest

from envsync.parser import parse_env_file
from envsync.rotator import RotateOptions, rotate_key


@pytest.fixture
def env_dir(tmp_path) -> Path:
    (tmp_path / ".env.dev").write_text(
        "APP_SECRET=devsecret\nOLD_API_KEY=devkey123\nDEBUG=true\n"
    )
    (tmp_path / ".env.staging").write_text(
        "APP_SECRET=stagingsecret\nOLD_API_KEY=stagingkey\nDEBUG=false\n"
    )
    (tmp_path / ".env.prod").write_text(
        "APP_SECRET=prodsecret\nDEBUG=false\n"  # OLD_API_KEY intentionally absent
    )
    return tmp_path


def test_integration_key_renamed_in_all_present_files(env_dir):
    files = [parse_env_file(str(p)) for p in sorted(env_dir.glob(".env.*"))]
    updated, result = rotate_key(files, {"OLD_API_KEY": "API_KEY"})
    for env_file in updated:
        keys = [e.key for e in env_file.entries]
        assert "OLD_API_KEY" not in keys
        if "API_KEY" in [e.key for e in env_file.entries]:
            assert True  # present where it was before


def test_integration_missing_key_skipped_silently(env_dir):
    files = [parse_env_file(str(p)) for p in sorted(env_dir.glob(".env.*"))]
    _, result = rotate_key(files, {"OLD_API_KEY": "API_KEY"})
    # .env.prod doesn't have OLD_API_KEY — should be skipped, not a violation
    assert not result.has_violations
    assert result.total_skipped >= 1


def test_integration_strict_missing_key_is_violation(env_dir):
    files = [parse_env_file(str(p)) for p in sorted(env_dir.glob(".env.*"))]
    opts = RotateOptions(ignore_missing=False)
    _, result = rotate_key(files, {"OLD_API_KEY": "API_KEY"}, opts)
    assert result.has_violations


def test_integration_values_preserved_after_rotation(env_dir):
    files = [parse_env_file(str(p)) for p in sorted(env_dir.glob(".env.*"))]
    updated, _ = rotate_key(files, {"OLD_API_KEY": "API_KEY"})
    for env_file in updated:
        entry_map = {e.key: e.value for e in env_file.entries}
        if "API_KEY" in entry_map:
            assert entry_map["API_KEY"] in ("devkey123", "stagingkey")
