#!/usr/bin/env python3
"""
Discover source/test targets for a folder-level coverage harness.

Default behavior targets JS/TS repositories, but the include/exclude rules are configurable
via a JSON config file.

Example:
  python discover_targets.py --root /repo --config config.json --output discovery.json
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import os
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable, List, Dict, Set


DEFAULT_CONFIG = {
    "source_globs": [
        "src/**/*.ts",
        "src/**/*.tsx",
        "src/**/*.js",
        "src/**/*.jsx",
    ],
    "test_globs": [
        "**/*.test.ts",
        "**/*.spec.ts",
        "**/*.test.tsx",
        "**/*.spec.tsx",
        "**/*.test.js",
        "**/*.spec.js",
        "**/*.test.jsx",
        "**/*.spec.jsx",
        "tests/**/*.ts",
        "tests/**/*.tsx",
        "tests/**/*.js",
        "tests/**/*.jsx",
    ],
    "exclude_globs": [
        "**/node_modules/**",
        "**/dist/**",
        "**/build/**",
        "**/.next/**",
        "**/coverage/**",
    ],
    "mapping_strategy": "hybrid"
}


@dataclass
class Target:
    target_id: str
    source_files: List[str]
    test_files: List[str]
    candidate_score: float
    mapping_notes: List[str]


def load_config(path: str | None) -> dict:
    if not path:
        return DEFAULT_CONFIG
    with open(path, "r", encoding="utf-8") as f:
        user_cfg = json.load(f)
    merged = DEFAULT_CONFIG.copy()
    merged.update(user_cfg)
    return merged


def normalize(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def matches_any(rel_path: str, patterns: Iterable[str]) -> bool:
    return any(fnmatch.fnmatch(rel_path, p) for p in patterns)


def collect_files(root: Path, include_globs: List[str], exclude_globs: List[str]) -> List[Path]:
    files: List[Path] = []
    seen: Set[Path] = set()
    for pattern in include_globs:
        for p in root.glob(pattern):
            if not p.is_file():
                continue
            rel = p.relative_to(root).as_posix()
            if matches_any(rel, exclude_globs):
                continue
            if p not in seen:
                seen.add(p)
                files.append(p)
    return sorted(files)


def stem_variants(path: Path) -> Set[str]:
    """
    Generate name variants used for weak source/test matching.
    """
    name = path.name
    stem = path.stem
    suffixless = name
    variants = {stem, suffixless}
    replacements = [
        ".test", ".spec", ".stories", ".cy", ".unit", ".integration",
    ]
    for rep in replacements:
        variants.add(stem.replace(rep, ""))
        variants.add(name.replace(rep, ""))
    if stem.endswith(".d"):
        variants.add(stem[:-2])
    return {v for v in variants if v}


def map_tests_to_source(source: Path, tests: List[Path]) -> tuple[list[Path], float, list[str]]:
    src_stems = stem_variants(source)
    src_parent = source.parent
    matches: list[Path] = []
    notes: list[str] = []
    score = 0.0

    for test in tests:
        test_variants = stem_variants(test)
        shared = src_stems.intersection(test_variants)
        if shared:
            matches.append(test)
            score += 0.7
            notes.append(f"name-match:{test.name}")
            continue

        # colocated folder hint
        if test.parent == src_parent or src_parent in test.parents:
            if source.stem in test.name or source.name in test.name:
                matches.append(test)
                score += 0.5
                notes.append(f"colocated-hint:{test.name}")

    # de-duplicate while preserving order
    deduped = []
    seen = set()
    for m in matches:
        if m not in seen:
            seen.add(m)
            deduped.append(m)

    score = min(score, 1.0) if deduped else 0.0
    if not deduped:
        notes.append("no-test-match-found")
    return deduped, score, notes


def build_targets(root: Path, cfg: dict) -> list[Target]:
    sources = collect_files(root, cfg["source_globs"], cfg["exclude_globs"])
    tests = collect_files(root, cfg["test_globs"], cfg["exclude_globs"])

    targets: list[Target] = []
    for src in sources:
        mapped_tests, score, notes = map_tests_to_source(src, tests)
        target_id = normalize(src, root).replace("/", "__")
        targets.append(
            Target(
                target_id=target_id,
                source_files=[normalize(src, root)],
                test_files=[normalize(t, root) for t in mapped_tests],
                candidate_score=round(score, 2),
                mapping_notes=notes,
            )
        )
    return targets


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True, help="Repository root")
    parser.add_argument("--config", help="Optional JSON config")
    parser.add_argument("--output", help="Where to write discovery manifest JSON")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = Path(args.root).resolve()
    if not root.exists() or not root.is_dir():
        raise SystemExit(f"Invalid root folder: {root}")

    cfg = load_config(args.config)
    targets = build_targets(root, cfg)
    manifest = {
        "root": root.as_posix(),
        "config": cfg,
        "target_count": len(targets),
        "targets": [asdict(t) for t in targets],
    }

    if args.output:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    else:
        print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
