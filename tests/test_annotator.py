"""Tests for envsync.annotator."""
from __future__ import annotations

import pytest

from envsync.annotator import AnnotateOptions, annotate
from envsync.parser import EnvEntry, EnvFile


def _make_env(*pairs: tuple[str, str]) -> EnvFile:
    entries = [EnvEntry(key=k, value=v, comment="", raw=f"{k}={v}") for k, v in pairs]
    return EnvFile(path=".env", entries=entries)


@pytest.fixture()
def env() -> EnvFile:
    return _make_env(
        ("DB_HOST", "localhost"),
        ("DB_PORT", "5432"),
        ("SECRET_KEY", "s3cr3t"),
        ("DEBUG", "true"),
    )


@pytest.fixture()
def annotation_map() -> dict:
    return {
        "DB_HOST": "database hostname",
        "SECRET_KEY": "keep this secret!",
    }


def test_annotate_adds_comment_to_matching_key(env, annotation_map):
    result = annotate(env, AnnotateOptions(annotations=annotation_map))
    db_entry = next(e for e in result.entries if e.key == "DB_HOST")
    assert "database hostname" in db_entry.comment


def test_annotate_leaves_unmatched_keys_unchanged(env, annotation_map):
    result = annotate(env, AnnotateOptions(annotations=annotation_map))
    port_entry = next(e for e in result.entries if e.key == "DB_PORT")
    assert port_entry.comment == ""


def test_annotate_counts_annotated(env, annotation_map):
    result = annotate(env, AnnotateOptions(annotations=annotation_map))
    assert result.total_annotated == 2


def test_annotate_counts_skipped_when_comment_exists():
    entries = [
        EnvEntry(key="DB_HOST", value="localhost", comment="# existing", raw="DB_HOST=localhost")
    ]
    env = EnvFile(path=".env", entries=entries)
    result = annotate(env, AnnotateOptions(annotations={"DB_HOST": "new note"}, overwrite=False))
    assert result.total_skipped == 1
    assert result.total_annotated == 0


def test_annotate_overwrites_when_flag_set():
    entries = [
        EnvEntry(key="DB_HOST", value="localhost", comment="# old", raw="DB_HOST=localhost")
    ]
    env = EnvFile(path=".env", entries=entries)
    result = annotate(env, AnnotateOptions(annotations={"DB_HOST": "new note"}, overwrite=True))
    assert result.total_annotated == 1
    assert "new note" in result.entries[0].comment


def test_annotate_was_modified_true_when_changes(env, annotation_map):
    result = annotate(env, AnnotateOptions(annotations=annotation_map))
    assert result.was_modified is True


def test_annotate_was_modified_false_when_no_matches(env):
    result = annotate(env, AnnotateOptions(annotations={"NONEXISTENT": "note"}))
    assert result.was_modified is False


def test_annotate_to_env_file_preserves_path(env, annotation_map):
    result = annotate(env, AnnotateOptions(annotations=annotation_map))
    out = result.to_env_file("/tmp/out.env")
    assert out.path == "/tmp/out.env"
    assert len(out.entries) == len(env.entries)


def test_annotate_custom_prefix(env):
    result = annotate(
        env,
        AnnotateOptions(annotations={"DEBUG": "toggle debug mode"}, prefix="##"),
    )
    debug_entry = next(e for e in result.entries if e.key == "DEBUG")
    assert debug_entry.comment.startswith("##")


def test_annotate_empty_annotations_leaves_env_unchanged(env):
    result = annotate(env, AnnotateOptions(annotations={}))
    assert result.total_annotated == 0
    assert [e.key for e in result.entries] == [e.key for e in env.entries]
