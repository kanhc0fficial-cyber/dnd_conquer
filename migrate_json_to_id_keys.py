#!/usr/bin/env python3
"""
Convert package JSON files from root array form to id-keyed object form.

Example:
  [
    {"id": "card_char_shadowheart", "name": "..."},
    {"id": "card_char_gale", "name": "..."}
  ]

becomes:
  {
    "card_char_shadowheart": {"id": "card_char_shadowheart", "name": "..."},
    "card_char_gale": {"id": "card_char_gale", "name": "..."}
  }

By default this script only reports what it would do. Pass --apply to write.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parent
PKG_DIR = BASE_DIR / "package"


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def dump_json(path: Path, data: Any) -> None:
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def validate_id_array(data: Any) -> tuple[bool, str]:
    if not isinstance(data, list):
        return False, "root is not an array"
    if not data:
        return False, "root array is empty"

    seen: set[str] = set()
    for idx, item in enumerate(data):
        if not isinstance(item, dict):
            return False, f"item {idx} is not an object"
        item_id = item.get("id")
        if not isinstance(item_id, str) or not item_id:
            return False, f"item {idx} has no string id"
        if item_id in seen:
            return False, f"duplicate id {item_id!r}"
        seen.add(item_id)
    return True, "ok"


def convert(data: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {item["id"]: item for item in data}


def backup_file(path: Path, backup_dir: Path) -> Path:
    backup_dir.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = backup_dir / f"{path.name}.{stamp}.bak"
    backup_path.write_bytes(path.read_bytes())
    return backup_path


def iter_target_files(names: list[str]) -> list[Path]:
    if names:
        return [PKG_DIR / name for name in names]
    return sorted(p for p in PKG_DIR.glob("*.json") if p.is_file())


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Convert package/*.json root arrays into id-keyed objects."
    )
    parser.add_argument(
        "files",
        nargs="*",
        help="Specific package JSON filenames to migrate. Default: all package/*.json",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Actually write migrated files. Without this flag, only reports changes.",
    )
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Do not create backups when --apply is used.",
    )
    parser.add_argument(
        "--backup-dir",
        default=str(BASE_DIR / "migration_backups"),
        help="Directory for backups. Default: ./migration_backups",
    )
    args = parser.parse_args()

    if not PKG_DIR.is_dir():
        print(f"[error] package directory not found: {PKG_DIR}")
        return 1

    targets = iter_target_files(args.files)
    changed = 0
    skipped = 0

    for path in targets:
        if path.parent.resolve() != PKG_DIR.resolve() or path.suffix.lower() != ".json":
            print(f"[skip] {path}: not a package root JSON file")
            skipped += 1
            continue
        if not path.exists():
            print(f"[skip] {path.name}: file not found")
            skipped += 1
            continue

        try:
            data = load_json(path)
        except Exception as exc:
            print(f"[skip] {path.name}: cannot read JSON: {exc}")
            skipped += 1
            continue

        ok, reason = validate_id_array(data)
        if not ok:
            print(f"[skip] {path.name}: {reason}")
            skipped += 1
            continue

        converted = convert(data)
        print(f"[migrate] {path.name}: {len(data)} array items -> {len(converted)} id keys")

        if args.apply:
            if not args.no_backup:
                backup_path = backup_file(path, Path(args.backup_dir))
                print(f"         backup: {backup_path}")
            dump_json(path, converted)
            print("         written")
        changed += 1

    mode = "applied" if args.apply else "dry-run"
    print(f"[done] mode={mode}, migratable={changed}, skipped={skipped}")
    if not args.apply and changed:
        print("       rerun with --apply to write changes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
