"""Tests for envsync.caster."""

from __future__ import annotations

import pytest

from envsync.caster import CastOptions, CastResult, cast_env, cast_value
from envsync.parser import EnvEntry, EnvFile


# ---------------------------------------------------------------------------
# cast_value
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("raw", ["true", "True", "TRUE", "yes", "1", "on"])
def test_cast_value_true_variants(raw: str) -> None:
    value, cast_type = cast_value(raw)
    assert value is True
    assert cast_type == "bool"


@pytest.mark.parametrize("raw", ["false", "False", "FALSE", "no", "0", "off"])
def test_cast_value_false_variants(raw: str) -> None:
    value, cast_type = cast_value(raw)
    assert value is False
    assert cast_type == "bool"


def test_cast_value_integer() -> None:
    value, cast_type = cast_value("42")
    assert value == 42
    assert cast_type == "int"


def test_cast_value_negative_integer() -> None:
    value, cast_type = cast_value("-7")
    assert value == -7
    assert cast_type == "int"


def test_cast_value_float() -> None:
    value, cast_type = cast_value("3.14")
    assert abs(value - 3.14) < 1e-9
    assert cast_type == "float"


def test_cast_value_plain_string() -> None:
    value, cast_type = cast_value("hello")
    assert value == "hello"
    assert cast_type == "str"


@pytest.mark.parametrize("raw", ["", "null", "none", "None", "NULL"])
def test_cast_value_none_strings(raw: str) -> None:
    value, cast_type = cast_value(raw)
    assert value is None
    assert cast_type == "none"


def test_cast_value_bool_disabled() -> None:
    opts = CastOptions(cast_bools=False)
    value, cast_type = cast_value("true", opts)
    assert cast_type == "str"
    assert value == "true"


def test_cast_value_int_disabled() -> None:
    opts = CastOptions(cast_ints=False)
    value, cast_type = cast_value("99", opts)
    # floats still enabled → 99 parses as float
    assert cast_type == "float"
    assert value == 99.0


def test_cast_value_all_numeric_disabled() -> None:
    opts = CastOptions(cast_ints=False, cast_floats=False)
    value, cast_type = cast_value("3.14", opts)
    assert cast_type == "str"


# ---------------------------------------------------------------------------
# cast_env
# ---------------------------------------------------------------------------


def _make_env(*pairs: tuple[str, str]) -> EnvFile:
    entries = [EnvEntry(key=k, value=v, raw=f"{k}={v}") for k, v in pairs]
    return EnvFile(path=".env", entries=entries)


def test_cast_env_returns_cast_results() -> None:
    env = _make_env(("PORT", "8080"), ("DEBUG", "true"), ("APP_NAME", "myapp"))
    results = cast_env(env)
    assert len(results) == 3
    assert all(isinstance(r, CastResult) for r in results)


def test_cast_env_correct_types() -> None:
    env = _make_env(("PORT", "8080"), ("DEBUG", "false"), ("RATIO", "0.5"))
    by_key = {r.key: r for r in cast_env(env)}
    assert by_key["PORT"].cast_type == "int"
    assert by_key["DEBUG"].cast_type == "bool"
    assert by_key["RATIO"].cast_type == "float"


def test_cast_env_skips_comment_entries() -> None:
    comment = EnvEntry(key=None, value=None, raw="# comment")
    env = EnvFile(path=".env", entries=[comment])
    results = cast_env(env)
    assert results == []
