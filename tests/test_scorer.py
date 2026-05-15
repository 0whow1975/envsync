"""Tests for envsync.scorer."""
from __future__ import annotations

import pytest

from envsync.parser import EnvFile, EnvEntry
from envsync.masker import SecretMasker, MaskConfig
from envsync.scorer import score_env, ScoreResult


def _make_env(*pairs: tuple[str, str]) -> EnvFile:
    entries = [
        EnvEntry(key=k, value=v, raw=f"{k}={v}", is_comment=False, is_blank=False)
        for k, v in pairs
    ]
    return EnvFile(path=".env", entries=entries)


@pytest.fixture()
def masker() -> SecretMasker:
    return SecretMasker(MaskConfig())


def test_score_result_returns_score_result(masker):
    env = _make_env(("APP_NAME", "myapp"), ("DEBUG", "false"))
    result = score_env(env, masker)
    assert isinstance(result, ScoreResult)


def test_perfect_env_has_no_issues(masker):
    env = _make_env(("APP_NAME", "myapp"), ("LOG_LEVEL", "info"))
    result = score_env(env, masker)
    assert result.issues == []


def test_perfect_env_grade_is_a(masker):
    env = _make_env(("APP_NAME", "myapp"), ("LOG_LEVEL", "info"))
    result = score_env(env, masker)
    assert result.grade == "A"


def test_lowercase_key_adds_issue(masker):
    env = _make_env(("app_name", "myapp"))
    result = score_env(env, masker)
    messages = [i.message for i in result.issues]
    assert any("uppercase" in m for m in messages)


def test_empty_value_non_secret_adds_issue(masker):
    env = _make_env(("LOG_LEVEL", ""))
    result = score_env(env, masker)
    messages = [i.message for i in result.issues]
    assert any("Empty value" in m for m in messages)


def test_duplicate_key_adds_issue(masker):
    env = _make_env(("APP_NAME", "a"), ("APP_NAME", "b"))
    result = score_env(env, masker)
    messages = [i.message for i in result.issues]
    assert any("Duplicate" in m for m in messages)


def test_weak_secret_value_adds_issue(masker):
    env = _make_env(("SECRET_KEY", "changeme"))
    result = score_env(env, masker)
    messages = [i.message for i in result.issues]
    assert any("weak" in m.lower() or "placeholder" in m.lower() for m in messages)


def test_score_is_reduced_by_penalties(masker):
    env = _make_env(("app_name", "myapp"))  # lowercase key → penalty 2
    result = score_env(env, masker)
    assert result.score < result.max_score


def test_score_never_goes_below_zero(masker):
    # pile on many issues for a single-entry env
    env = _make_env(("secret", "changeme"))  # lowercase + weak secret value
    result = score_env(env, masker)
    assert result.score >= 0


def test_as_dict_contains_expected_keys(masker):
    env = _make_env(("APP_NAME", "myapp"))
    d = score_env(env, masker).as_dict()
    assert {"score", "max_score", "grade", "issues"} <= d.keys()


def test_key_with_space_adds_issue(masker):
    env = _make_env(("APP NAME", "value"))
    result = score_env(env, masker)
    messages = [i.message for i in result.issues]
    assert any("whitespace" in m for m in messages)
