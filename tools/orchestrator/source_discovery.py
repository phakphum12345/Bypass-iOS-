#!/usr/bin/env python3

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]

DEFAULT_SOURCE_ROOTS = [
    "flutter_app/lib",
    "flutter_app/test",
]

DEFAULT_EXTENSIONS = [
    ".dart",
]

DEFAULT_EXCLUDES = [
    "**/.git/**",
    "**/.dart_tool/**",
    "**/build/**",
    "**/.idea/**",
    "**/.vscode/**",
    "**/node_modules/**",
    "**/.venv/**",
    "**/__pycache__/**",
    "**/*.g.dart",
    "**/*.freezed.dart",
]


@dataclass(frozen=True)
class SourceFile:
    path: str
    absolute_path: str
    extension: str
    size: int
    sha256: str


@dataclass
class SourceManifest:
    version: int = 1
    project: str = "Bypass-iOS"
    source_roots: list[str] = field(default_factory=list)
    extensions: list[str] = field(default_factory=list)
    excludes: list[str] = field(default_factory=list)
    files: list[SourceFile] = field(default_factory=list)

    @property
    def file_count(self) -> int:
        return len(self.files)

    @property
    def total_bytes(self) -> int:
        return sum(
            source.size
            for source in self.files
        )


def normalize_relative_path(
    path: Path,
) -> str:
    try:
        return path.resolve().relative_to(
            ROOT.resolve()
        ).as_posix()
    except ValueError as exc:
        raise RuntimeError(
            f"Path escapes repository root: {path}"
        ) from exc


def matches_exclude(
    relative_path: str,
    excludes: list[str],
) -> bool:
    normalized = relative_path.lstrip("/")

    for pattern in excludes:
        pattern = pattern.replace("\\", "/")
        if fnmatch.fnmatch(
            normalized,
            pattern,
        ):
            return True

        # Support directory-style excludes such as:
        # **/build/**
        if pattern.endswith("/**"):
            prefix = pattern[:-3].rstrip("/")
            if (
                normalized == prefix
                or normalized.startswith(
                    prefix + "/"
                )
            ):
                return True

    return False


def file_sha256(
    path: Path,
) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)

    return digest.hexdigest()


def extension_allowed(
    path: Path,
    extensions: list[str],
) -> bool:
    normalized = {
        extension.lower()
        if extension.startswith(".")
        else "." + extension.lower()
        for extension in extensions
    }

    return path.suffix.lower() in normalized


def resolve_source_roots(
    source_roots: list[str],
) -> list[Path]:
    resolved: list[Path] = []

    for relative in source_roots:
        path = (
            ROOT / relative
        ).resolve()

        try:
            path.relative_to(
                ROOT.resolve()
            )
        except ValueError as exc:
            raise RuntimeError(
                f"Source root escapes repository: {relative}"
            ) from exc

        if not path.exists():
            raise RuntimeError(
                f"Source root does not exist: {relative}"
            )

        if not path.is_dir():
            raise RuntimeError(
                f"Source root is not a directory: {relative}"
            )

        resolved.append(path)

    return resolved


def discover_sources(
    source_roots: list[str] | None = None,
    extensions: list[str] | None = None,
    excludes: list[str] | None = None,
) -> SourceManifest:
    source_roots = (
        list(source_roots)
        if source_roots is not None
        else list(DEFAULT_SOURCE_ROOTS)
    )

    extensions = (
        list(extensions)
        if extensions is not None
        else list(DEFAULT_EXTENSIONS)
    )

    excludes = (
        list(excludes)
        if excludes is not None
        else list(DEFAULT_EXCLUDES)
    )

    roots = resolve_source_roots(
        source_roots
    )

    discovered: dict[str, SourceFile] = {}

    for root in roots:
        for path in sorted(
            root.rglob("*")
        ):
            if not path.is_file():
                continue

            relative = normalize_relative_path(
                path
            )

            if matches_exclude(
                relative,
                excludes,
            ):
                continue

            if not extension_allowed(
                path,
                extensions,
            ):
                continue

            stat = path.stat()

            source = SourceFile(
                path=relative,
                absolute_path=str(
                    path.resolve()
                ),
                extension=path.suffix.lower(),
                size=stat.st_size,
                sha256=file_sha256(path),
            )

            discovered[relative] = source

    return SourceManifest(
        source_roots=source_roots,
        extensions=extensions,
        excludes=excludes,
        files=[
            discovered[path]
            for path in sorted(discovered)
        ],
    )


def manifest_dict(
    manifest: SourceManifest,
) -> dict[str, Any]:
    return {
        "version": manifest.version,
        "project": manifest.project,
        "source_roots": manifest.source_roots,
        "extensions": manifest.extensions,
        "excludes": manifest.excludes,
        "file_count": manifest.file_count,
        "total_bytes": manifest.total_bytes,
        "files": [
            asdict(source)
            for source in manifest.files
        ],
    }


def save_manifest(
    manifest: SourceManifest,
    output: Path,
) -> None:
    output = output.resolve()

    try:
        output.relative_to(
            ROOT.resolve()
        )
    except ValueError as exc:
        raise RuntimeError(
            f"Manifest output escapes repository: {output}"
        ) from exc

    output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output.write_text(
        json.dumps(
            manifest_dict(manifest),
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def load_manifest(
    path: Path,
) -> dict[str, Any]:
    return json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )


def compare_manifests(
    previous: dict[str, Any],
    current: SourceManifest,
) -> dict[str, list[str]]:
    old_files = {
        item["path"]: item
        for item in previous.get(
            "files",
            [],
        )
    }

    new_files = {
        item.path: item
        for item in current.files
    }

    added = sorted(
        set(new_files) - set(old_files)
    )

    deleted = sorted(
        set(old_files) - set(new_files)
    )

    changed = sorted(
        path
        for path in set(old_files) & set(new_files)
        if old_files[path].get("sha256")
        != new_files[path].sha256
    )

    unchanged = sorted(
        path
        for path in set(old_files) & set(new_files)
        if old_files[path].get("sha256")
        == new_files[path].sha256
    )

    return {
        "added": added,
        "changed": changed,
        "deleted": deleted,
        "unchanged": unchanged,
    }


def print_manifest(
    manifest: SourceManifest,
) -> None:
    print("=" * 72)
    print("AUTONOMOUS SOURCE DISCOVERY")
    print("=" * 72)
    print()

    print("Source roots:")
    for root in manifest.source_roots:
        print(f"  [ROOT] {root}")

    print()
    print("Extensions:")
    for extension in manifest.extensions:
        print(f"  [EXT ] {extension}")

    print()
    print(
        f"Files discovered : {manifest.file_count}"
    )
    print(
        f"Total bytes      : {manifest.total_bytes}"
    )

    print()

    for source in manifest.files:
        print(
            f"[SOURCE] {source.path}"
        )
        print(
            f"         sha256={source.sha256}"
        )
        print(
            f"         size={source.size}"
        )


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Autonomous recursive source discovery "
            "and manifest generator."
        )
    )

    parser.add_argument(
        "--root",
        action="append",
        dest="source_roots",
        default=None,
        help=(
            "Repository-relative source root. "
            "May be supplied multiple times."
        ),
    )

    parser.add_argument(
        "--extension",
        action="append",
        dest="extensions",
        default=None,
        help=(
            "Allowed source extension. "
            "May be supplied multiple times."
        ),
    )

    parser.add_argument(
        "--exclude",
        action="append",
        dest="excludes",
        default=None,
        help=(
            "Exclude glob. "
            "May be supplied multiple times."
        ),
    )

    parser.add_argument(
        "--manifest",
        type=Path,
        default=(
            ORCH_MANIFEST
            if "ORCH_MANIFEST" in globals()
            else ROOT
            / "tools"
            / "orchestrator"
            / "source_manifest.json"
        ),
    )

    parser.add_argument(
        "--no-save",
        action="store_true",
    )

    args = parser.parse_args()

    manifest = discover_sources(
        source_roots=args.source_roots,
        extensions=args.extensions,
        excludes=args.excludes,
    )

    print_manifest(manifest)

    if not args.no_save:
        save_manifest(
            manifest,
            args.manifest,
        )

        print()
        print(
            f"[PASS] manifest: {args.manifest}"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
