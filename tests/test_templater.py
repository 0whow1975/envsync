"""Tests for envsync.templater."""
from __future__ import annotations

from pathlib import Path

import pytest

from envsync.parser import EnvEntry, EnvFile
from envsync.schema import EnvSchema
from envsync.templater import TemplateOptions, generate_template, generate_template_from_schema, save_template


@pytest.fixture()
def plain_env() -> EnvFile:
    entries = [
        EnvEntry(key="APP_NAME", value="myapp", comment=None),
        EnvEntry(key="DEBUG", value="true", comment=None),
        EnvEntry(key="SECRET_KEY", value="super-secret", comment="# auth"),
        EnvEntry(key="DATABASE_URL", value="postgres://localhost/db", comment=None),
    ]
    return EnvFile(path=Path(".env"), entries=entries)


def test_generate_template_masks_secret_keys(plain_env: EnvFile) -> None:
    content = generate_template(plain_env)
    assert "SECRET_KEY=" in content
    assert "super-secret" not in content


def test_generate_template_masks_database_url(plain_env: EnvFile) -> None:
    content = generate_template(plain_env)
    assert "DATABASE_URL=" in content
    assert "postgres://localhost/db" not in content


def test_generate_template_keeps_plain_values(plain_env: EnvFile) -> None:
    content = generate_template(plain_env)
    assert "APP_NAME=myapp" in content
    assert "DEBUG=true" in content


def test_generate_template_includes_comments_by_default(plain_env: EnvFile) -> None:
    content = generate_template(plain_env)
    assert "# auth" in content


def test_generate_template_omits_comments_when_disabled(plain_env: EnvFile) -> None:
    opts = TemplateOptions(include_comments=False)
    content = generate_template(plain_env, opts)
    assert "# auth" not in content


def test_generate_template_custom_placeholder(plain_env: EnvFile) -> None:
    opts = TemplateOptions(placeholder="CHANGEME")
    content = generate_template(plain_env, opts)
    assert "SECRET_KEY=CHANGEME" in content


def test_generate_template_no_mask_keeps_all_values(plain_env: EnvFile) -> None:
    opts = TemplateOptions(mask_secrets=False)
    content = generate_template(plain_env, opts)
    assert "super-secret" in content
    assert "postgres://localhost/db" in content


def test_generate_template_ends_with_newline(plain_env: EnvFile) -> None:
    content = generate_template(plain_env)
    assert content.endswith("\n")


@pytest.fixture()
def simple_schema() -> EnvSchema:
    return EnvSchema(required_keys=["APP_NAME", "SECRET_KEY"], optional_keys=["DEBUG"])


def test_schema_template_contains_all_keys(simple_schema: EnvSchema) -> None:
    content = generate_template_from_schema(simple_schema)
    assert "APP_NAME=" in content
    assert "SECRET_KEY=" in content
    assert "DEBUG=" in content


def test_schema_template_includes_section_comments(simple_schema: EnvSchema) -> None:
    content = generate_template_from_schema(simple_schema)
    assert "# Required" in content
    assert "# Optional" in content


def test_schema_template_no_comments(simple_schema: EnvSchema) -> None:
    opts = TemplateOptions(include_comments=False)
    content = generate_template_from_schema(simple_schema, opts)
    assert "# Required" not in content
    assert "# Optional" not in content


def test_save_template_writes_file(tmp_path: Path) -> None:
    dest = tmp_path / "subdir" / ".env.template"
    save_template("KEY=value\n", dest)
    assert dest.exists()
    assert dest.read_text() == "KEY=value\n"
