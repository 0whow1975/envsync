"""Cross-environment comparator: compare multiple env files at once."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envsync.parser import EnvFile
from envsync.diff import DiffResult, diff_env_files


@dataclass
class CompareOptions:
    """Options controlling comparison behaviour."""
    show_all_keys: bool = True   # include keys absent from some envs
    baseline: Optional[str] = None  # label of the env treated as reference


@dataclass
class EnvPair:
    label_a: str
    label_b: str
    diff: DiffResult


@dataclass
class CompareResult:
    """Holds pairwise diffs for every combination of envs."""
    pairs: List[EnvPair] = field(default_factory=list)
    all_keys: List[str] = field(default_factory=list)

    # label -> set of keys present in that env
    presence: Dict[str, List[str]] = field(default_factory=dict)

    def keys_missing_from(self, label: str) -> List[str]:
        """Return keys present in *some* env but absent in *label*."""
        present = set(self.presence.get(label, []))
        return [k for k in self.all_keys if k not in present]

    def keys_unique_to(self, label: str) -> List[str]:
        """Return keys that exist only in *label*."""
        others: set = set()
        for lbl, keys in self.presence.items():
            if lbl != label:
                others.update(keys)
        return [k for k in self.presence.get(label, []) if k not in others]


def compare_envs(
    envs: Dict[str, EnvFile],
    options: Optional[CompareOptions] = None,
) -> CompareResult:
    """Compare every pair of envs and return a :class:`CompareResult`."""
    options = options or CompareOptions()
    labels = list(envs.keys())

    all_keys_set: set = set()
    presence: Dict[str, List[str]] = {}
    for label, env in envs.items():
        env_keys = list(env.keys())
        presence[label] = env_keys
        all_keys_set.update(env_keys)

    all_keys = sorted(all_keys_set)

    pairs: List[EnvPair] = []
    baseline = options.baseline
    if baseline and baseline in labels:
        others = [l for l in labels if l != baseline]
        combos = [(baseline, other) for other in others]
    else:
        combos = [
            (labels[i], labels[j])
            for i in range(len(labels))
            for j in range(i + 1, len(labels))
        ]

    for label_a, label_b in combos:
        diff = diff_env_files(envs[label_a], envs[label_b])
        pairs.append(EnvPair(label_a=label_a, label_b=label_b, diff=diff))

    return CompareResult(pairs=pairs, all_keys=all_keys, presence=presence)
