"""Generate .env template files from existing env files or schemas."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from envsync.parser import EnvFile, EnvEntry
from envsync.masker import SecretMasker, MaskConfig
from envsync.schema import EnvSchema


@dataclass
class TemplateOptions:
    mask_secrets: bool = True
    include_comments: bool = True
    placeholder: str = ""
    mask_config: MaskConfig = field(default_factory=MaskConfig)


def _entry_to_template_line(entry: EnvEntry, masker: SecretMasker, opts: TemplateOptions) -> str:
    """Convert an EnvEntry to a template line, masking secret values."""
    if masker.is_secret(entry.key) and opts.mask_secrets:
        value = opts.placeholder
    else:
        value = entry.value
    return f"{entry.key}={value}"


def generate_template(
    env_file: EnvFile,
    opts: Optional[TemplateOptions] = None,
) -> str:
    """Generate a template string from an EnvFile.

    Secret values are replaced with a placeholder; plain values are kept.
    Comments and blank lines are preserved when include_comments is True.
    """
    if opts is None:
        opts = TemplateOptions()

    masker = SecretMasker(opts.mask_config)
    lines: list[str] = []

    for entry in env_file.entries:
        if entry.comment and opts.include_comments:
            lines.append(entry.comment)
        lines.append(_entry_to_template_line(entry, masker, opts))

    return "\n".join(lines) + "\n"


def generate_template_from_schema(
    schema: EnvSchema,
    opts: Optional[TemplateOptions] = None,
) -> str:
    """Generate a blank template from a schema listing required and optional keys."""
    if opts is None:
        opts = TemplateOptions()

    lines: list[str] = []

    if schema.required_keys and opts.include_comments:
        lines.append("# Required")
    for key in schema.required_keys:
        lines.append(f"{key}={opts.placeholder}")

    if schema.optional_keys:
        if opts.include_comments:
            lines.append("")
            lines.append("# Optional")
        for key in schema.optional_keys:
            lines.append(f"{key}={opts.placeholder}")

    return "\n".join(lines) + "\n"


def save_template(content: str, dest: Path) -> None:
    """Write template content to *dest*, creating parent directories as needed."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(content, encoding="utf-8")
