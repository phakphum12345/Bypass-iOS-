#!/usr/bin/env python3

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from tools.orchestrator.source_discovery import (
    ROOT,
    discover_sources,
    manifest_dict,
)


DEFAULT_OUTPUT = (
    ROOT
    / "tools"
    / "orchestrator"
    / "source_bundle.json"
)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def build_bundle(
    source_roots: list[str] | None = None,
    extensions: list[str] | None = None,
    excludes: list[str] | None = None,
) -> dict[str, Any]:
    manifest = discover_sources(
        source_roots=source_roots,
        extensions=extensions,
        excludes=excludes,
    )

    files: list[dict[str, Any]] = []

    for source in manifest.files:
        path = ROOT / source.path
        raw = path.read_bytes()

        actual_sha = sha256_bytes(raw)

        if actual_sha != source.sha256:
            raise RuntimeError(
                f"Source changed during bundle creation: {source.path}"
            )

        try:
            content = raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise RuntimeError(
                f"Source is not valid UTF-8: {source.path}"
            ) from exc

        files.append(
            {
                "path": source.path,
                "extension": source.extension,
                "size": source.size,
                "sha256": source.sha256,
                "content": content,
            }
        )

    return {
        "version": 1,
        "project": manifest.project,
        "source_roots": manifest.source_roots,
        "extensions": manifest.extensions,
        "excludes": manifest.excludes,
        "file_count": len(files),
        "total_bytes": sum(
            item["size"]
            for item in files
        ),
        "files": files,
    }


def validate_bundle(
    bundle: dict[str, Any],
) -> dict[str, Any]:
    files = bundle.get("files")

    if not isinstance(files, list):
        return {
            "passed": False,
            "error": "Bundle files must be a list.",
        }

    errors: list[str] = []

    for item in files:
        path = item.get("path")
        content = item.get("content")
        expected = item.get("sha256")

        if not isinstance(path, str):
            errors.append("Invalid file path entry.")
            continue

        if not isinstance(content, str):
            errors.append(
                f"Missing content: {path}"
            )
            continue

        if not isinstance(expected, str):
            errors.append(
                f"Missing sha256: {path}"
            )
            continue

        actual = sha256_bytes(
            content.encode("utf-8")
        )

        if actual != expected:
            errors.append(
                f"SHA mismatch: {path}"
            )

    if errors:
        return {
            "passed": False,
            "error": "\n".join(errors),
        }

    return {
        "passed": True,
        "files": len(files),
    }


def save_bundle(
    bundle: dict[str, Any],
    output: Path,
) -> None:
    output = output.resolve()

    try:
        output.relative_to(
            ROOT.resolve()
        )
    except ValueError as exc:
        raise RuntimeError(
            f"Bundle output escapes repository: {output}"
        ) from exc

    output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output.write_text(
        json.dumps(
            bundle,
            indent=2,
            ensure_ascii=False,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Build a full source-content bundle from "
            "the recursively discovered source tree."
        )
    )

    parser.add_argument(
        "--root",
        action="append",
        dest="source_roots",
        default=None,
    )

    parser.add_argument(
        "--extension",
        action="append",
        dest="extensions",
        default=None,
    )

    parser.add_argument(
        "--exclude",
        action="append",
        dest="excludes",
        default=None,
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
    )

    args = parser.parse_args()

    bundle = build_bundle(
        source_roots=args.source_roots,
        extensions=args.extensions,
        excludes=args.excludes,
    )

    validation = validate_bundle(bundle)

    if not validation["passed"]:
        print(
            json.dumps(
                validation,
                indent=2,
            )
        )
        return 1

    save_bundle(
        bundle,
        args.output,
    )

    print("=" * 72)
    print("AUTONOMOUS SOURCE BUNDLE")
    print("=" * 72)
    print()
    print(
        f"Files : {bundle['file_count']}"
    )
    print(
        f"Bytes : {bundle['total_bytes']}"
    )
    print(
        f"Output: {args.output}"
    )
    print()
    print(
        "[PASS] bundle validation"
    )

    for item in bundle["files"]:
        print(
            f"[BUNDLE] {item['path']} "
            f"({item['size']} bytes)"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
