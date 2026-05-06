"""Tests for envsync.interpolator."""
from __future__ import annotations

import textwrap
import pytest

from envsync.parser import parse_env_file
from envsync.interpolator import interpolate, _resolve_value


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _env(content: str):
    """Parse an inline .env string into an EnvFile."""
    import tempfile, pathlib
    with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as fh:
        fh.write(textwrap.dedent(content))
        path = pathlib.Path(fh.name)
    return parse_env_file(path)


# ---------------------------------------------------------------------------
# _resolve_value unit tests
# ---------------------------------------------------------------------------

def test_resolve_brace_syntax():
    assert _resolve_value("${HOST}:5432", {"HOST": "localhost"}) == "localhost:5432"


def test_resolve_bare_syntax():
    assert _resolve_value("$USER@example.com", {"USER": "alice"}) == "alice@example.com"


def test_resolve_missing_uses_default():
    assert _resolve_value("${MISSING}", {}, default="UNKNOWN") == "UNKNOWN"


def test_resolve_no_references_unchanged():
    assert _resolve_value("plain-value", {"X": "y"}) == "plain-value"


# ---------------------------------------------------------------------------
# interpolate integration tests
# ---------------------------------------------------------------------------

def test_interpolate_returns_all_keys():
    env = _env("""
        HOST=localhost
        PORT=5432
    """)
    result = interpolate(env)
    assert set(result.keys()) == {"HOST", "PORT"}


def test_interpolate_resolves_forward_reference_within_file():
    env = _env("""
        HOST=db.local
        DSN=postgres://${HOST}/mydb
    """)
    result = interpolate(env)
    assert result["DSN"] == "postgres://db.local/mydb"


def test_interpolate_uses_extra_context():
    env = _env("""
        GREETING=Hello $NAME
    """)
    result = interpolate(env, extra={"NAME": "World"})
    assert result["GREETING"] == "Hello World"


def test_interpolate_file_keys_override_extra():
    """Keys defined earlier in the file take precedence over *extra*."""
    env = _env("""
        BASE=from_file
        URL=${BASE}/path
    """)
    result = interpolate(env, extra={"BASE": "from_extra"})
    assert result["URL"] == "from_file/path"


def test_interpolate_unresolvable_replaced_with_default():
    env = _env("""
        URL=https://${UNKNOWN_HOST}/api
    """)
    result = interpolate(env, default="MISSING")
    assert result["URL"] == "https://MISSING/api"


def test_interpolate_empty_default_for_unresolvable():
    env = _env("""
        TAG=${VERSION}
    """)
    result = interpolate(env)
    assert result["TAG"] == ""
