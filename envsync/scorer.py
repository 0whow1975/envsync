"""Score an .env file for quality/hygiene and return a structured result."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from envsync.parser import EnvFile
from envsync.masker import SecretMasker, MaskConfig


@dataclass
class ScoreIssue:
    key: str
    message: str
    penalty: int

    def __str__(self) -> str:
        return f"[{self.key}] {self.message} (penalty: {self.penalty})"


@dataclass
class ScoreResult:
    max_score: int
    issues: List[ScoreIssue] = field(default_factory=list)

    @property
    def penalty(self) -> int:
        return sum(i.penalty for i in self.issues)

    @property
    def score(self) -> int:
        return max(0, self.max_score - self.penalty)

    @property
    def grade(self) -> str:
        ratio = self.score / self.max_score if self.max_score else 0
        if ratio >= 0.9:
            return "A"
        if ratio >= 0.75:
            return "B"
        if ratio >= 0.6:
            return "C"
        if ratio >= 0.4:
            return "D"
        return "F"

    def as_dict(self) -> dict:
        return {
            "score": self.score,
            "max_score": self.max_score,
            "grade": self.grade,
            "issues": [str(i) for i in self.issues],
        }


def score_env(env: EnvFile, masker: SecretMasker | None = None) -> ScoreResult:
    """Analyse *env* and return a :class:`ScoreResult`."""
    if masker is None:
        masker = SecretMasker(MaskConfig())

    entries = [e for e in env.entries if not e.is_comment and not e.is_blank]
    max_score = max(len(entries) * 10, 10)
    result = ScoreResult(max_score=max_score)

    seen_keys: set[str] = set()
    for entry in entries:
        key = entry.key or ""

        # Duplicate key
        if key in seen_keys:
            result.issues.append(ScoreIssue(key, "Duplicate key", 5))
        seen_keys.add(key)

        # Empty value for a non-secret key
        value = entry.value or ""
        if not value.strip() and not masker.is_secret(key):
            result.issues.append(ScoreIssue(key, "Empty value for non-secret key", 3))

        # Key not uppercase
        if key and key != key.upper():
            result.issues.append(ScoreIssue(key, "Key is not uppercase", 2))

        # Key contains spaces
        if " " in key:
            result.issues.append(ScoreIssue(key, "Key contains whitespace", 4))

        # Secret key has a non-empty placeholder (warn if looks like a real value)
        if masker.is_secret(key) and value.strip().lower() in ("changeme", "secret", "password", "1234", "test"):
            result.issues.append(ScoreIssue(key, "Secret key has a weak/placeholder value", 8))

    return result
