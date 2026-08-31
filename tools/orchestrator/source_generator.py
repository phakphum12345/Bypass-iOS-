#!/usr/bin/env python3

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]

DISCOVERY_MODULE = (
    "tools.orchestrator.source_discovery"
)

DEFAULT_MANIFEST = (
    ROOT
    / "tools"
    / "orchestrator"
    / "source_manifest.json"
)

DEFAULT_GENERATOR = (
    ROOT
    / "tools"
    / "codegen"
    / "generate.py"
)


def load_json(
    path: Path,
) -> dict[str, Any]:
    return json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )


def sha256(
    path: Path,
) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as handle:
        while True:
            chunk = handle.read(
                1024 * 1024
            )
            if not chunk:
                break
            digest.update(chunk)

    return digest.hexdigest()


def discover_manifest(
    manifest: Path,
) -> dict[str, Any]:
    command = [
        "python3",
        "-m",
        DISCOVERY_MODULE,
        "--manifest",
        str(manifest),
    ]

    result = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )

    if result.returncode != 0:
        raise RuntimeError(
            result.stdout
        )

    return load_json(manifest)


def validate_manifest(
    manifest: dict[str, Any],
) -> dict[str, Any]:
    required = [
        "version",
        "project",
        "source_roots",
        "extensions",
        "files",
    ]

    missing = [
        key
        for key in required
        if key not in manifest
    ]

    if missing:
        return {
            "passed": False,
            "error": (
                "Source manifest missing fields: "
                + ", ".join(missing)
            ),
        }

    if not isinstance(
        manifest["files"],
        list,
    ):
        return {
            "passed": False,
            "error": "manifest.files must be a list.",
        }

    return {
        "passed": True,
    }


def verify_manifest_files(
    manifest: dict[str, Any],
) -> dict[str, Any]:
    missing: list[str] = []
    drift: list[str] = []

    for item in manifest["files"]:
        relative = item["path"]
        expected = item["sha256"]

        path = ROOT / relative

        if not path.exists():
            missing.append(relative)
            continue

        if not path.is_file():
            missing.append(relative)
            continue

        actual = sha256(path)

        if actual != expected:
            drift.append(relative)

    if missing or drift:
        messages: list[str] = []

        if missing:
            messages.append(
                "Missing source files:\n"
                + "\n".join(
                    f"- {path}"
                    for path in missing
                )
            )

        if drift:
            messages.append(
                "Source files changed since discovery:\n"
                + "\n".join(
                    f"- {path}"
                    for path in drift
                )
            )

        return {
            "passed": False,
            "error": "\n".join(messages),
            "missing": missing,
            "drift": drift,
        }

    return {
        "passed": True,
        "verified_files": len(
            manifest["files"]
        ),
    }


def collect_source_files(
    manifest: dict[str, Any],
) -> list[str]:
    return [
        item["path"]
        for item in manifest["files"]
    ]


def build_generator_command(
    generator: Path,
    phase: int,
    files: list[str],
    dry_run: bool,
) -> list[str]:
    command = [
        "python3",
        str(generator.relative_to(ROOT)),
        "--phase",
        str(phase),
    ]

    if dry_run:
        command.append(
            "--dry-run"
        )

    if files:
        command.extend(
            [
                "--files",
                *files,
            ]
        )

    return command


def run_generator(
    phase: int,
    manifest: dict[str, Any],
    generator: Path = DEFAULT_GENERATOR,
    dry_run: bool = False,
) -> dict[str, Any]:
    validation = validate_manifest(
        manifest
    )

    if not validation["passed"]:
        return validation

    verification = verify_manifest_files(
        manifest
    )

    if not verification["passed"]:
        return verification

    files = collect_source_files(
        manifest
    )

    command = build_generator_command(
        generator=generator,
        phase=phase,
        files=files,
        dry_run=dry_run,
    )

    result = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )

    return {
        "passed": result.returncode == 0,
        "returncode": result.returncode,
        "dry_run": dry_run,
        "source_count": len(files),
        "files": files,
        "command": command,
        "output": result.stdout,
        "manifest": manifest,
    }


def summarize(
    result: dict[str, Any],
) -> None:
    print("=" * 72)
    print("AUTONOMOUS SOURCE → GENERATOR")
    print("=" * 72)
    print()

    print(
        "Mode         : "
        + (
            "dry-run"
            if result.get("dry_run")
            else "execute"
        )
    )

    print(
        "Source files : "
        + str(
            result.get(
                "source_count",
                0,
            )
        )
    )

    print(
        "Result       : "
        + (
            "PASS"
            if result["passed"]
            else "FAIL"
        )
    )

    print()

    if result.get("files"):
        print("Files:")
        for path in result["files"]:
            print(f"  [SOURCE] {path}")

    print()

    if result.get("output"):
        print("Generator output:")
        print(
            result["output"]
        )


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Discover source tree and feed "
            "all discovered source files to generator."
        )
    )

    parser.add_argument(
        "--phase",
        type=int,
        required=True,
    )

    parser.add_argument(
        "--manifest",
        type=Path,
        default=DEFAULT_MANIFEST,
    )

    parser.add_argument(
        "--generator",
        type=Path,
        default=DEFAULT_GENERATOR,
    )

    parser.add_argument(
        "--discover",
        action="store_true",
        help="Refresh the source manifest first.",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
    )

    args = parser.parse_args()

    manifest_path = (
        args.manifest
    )

    if args.discover:
        manifest = discover_manifest(
            manifest_path
        )
    else:
        if not manifest_path.exists():
            manifest = discover_manifest(
                manifest_path
            )
        else:
            manifest = load_json(
                manifest_path
            )

    result = run_generator(
        phase=args.phase,
        manifest=manifest,
        generator=args.generator,
        dry_run=args.dry_run,
    )

    summarize(result)

    return (
        0
        if result["passed"]
        else 1
    )


if __name__ == "__main__":
    raise SystemExit(main())
