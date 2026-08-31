#!/usr/bin/env python3

from pathlib import Path
import argparse
import hashlib
import json
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
SCHEMA = ROOT / "tools/codegen/schema.json"
TEMPLATE_ROOT = ROOT / "tools/codegen/templates"
MANIFEST = ROOT / "tools/codegen/generated_manifest.json"


def load_schema():
    with SCHEMA.open("r", encoding="utf-8") as f:
        return json.load(f)


def run(cmd, cwd=None):
    print()
    print(">>>", " ".join(cmd), flush=True)

    result = subprocess.run(
        cmd,
        cwd=cwd or ROOT,
    )

    if result.returncode != 0:
        print()
        print("GENERATION FAILED")
        sys.exit(result.returncode)


def sha256(data):
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def ensure_dirs():
    core = ROOT / "flutter_app/lib/core"

    for name in [
        "models",
        "contracts",
        "services",
        "engine",
        "pipeline",
        "security",
    ]:
        (core / name).mkdir(parents=True, exist_ok=True)

    (ROOT / "flutter_app/test").mkdir(parents=True, exist_ok=True)
    TEMPLATE_ROOT.mkdir(parents=True, exist_ok=True)


def all_files(schema):
    output_root = ROOT / schema["output_root"]

    groups = [
        "models",
        "contracts",
        "services",
        "engine",
        "pipeline",
        "security",
    ]

    result = []

    for group in groups:
        for name in schema.get(group, []):
            if not name.endswith(".dart"):
                name += ".dart"

            relative = Path(group) / name
            result.append(output_root / relative)

    return result


def template_for(path):
    relative = path.relative_to(ROOT / "flutter_app/lib/core")
    return TEMPLATE_ROOT / relative.with_suffix(".dart.tmpl")


def bootstrap_templates(paths):
    """
    First run creates canonical templates from the already validated
    Phase 3/4 implementation.

    After that, templates become the generation source.
    """
    print()
    print("===== TEMPLATE SOURCE =====")

    for path in paths:
        template = template_for(path)
        template.parent.mkdir(parents=True, exist_ok=True)

        if not template.exists():
            if not path.exists():
                print(f"[ERROR] Cannot bootstrap missing source: {path}")
                sys.exit(1)

            template.write_text(
                path.read_text(encoding="utf-8"),
                encoding="utf-8",
            )

            print(f"[BOOTSTRAP] {template.relative_to(ROOT)}")
        else:
            print(f"[READY]     {template.relative_to(ROOT)}")


def generate(paths):
    print()
    print("===== GENERATING =====")

    manifest = {
        "project": "bypass_architecture_reference",
        "version": "phase5",
        "generator": "deterministic-template-v1",
        "files": {},
    }

    for path in paths:
        template = template_for(path)

        if not template.exists():
            print(f"[ERROR] Missing template: {template}")
            sys.exit(1)

        content = template.read_text(encoding="utf-8")

        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

        digest = sha256(content)

        relative = str(path.relative_to(ROOT))
        manifest["files"][relative] = {
            "template": str(template.relative_to(ROOT)),
            "sha256": digest,
            "bytes": len(content.encode("utf-8")),
        }

        print(f"[GENERATED] {relative}")

    MANIFEST.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    print()
    print(f"Generated {len(paths)} architecture files.")
    print(f"Manifest: {MANIFEST.relative_to(ROOT)}")


def verify(paths):
    print()
    print("===== DETERMINISTIC VERIFY =====")

    if not MANIFEST.exists():
        print("[ERROR] Generated manifest missing.")
        sys.exit(1)

    data = json.loads(MANIFEST.read_text(encoding="utf-8"))

    failures = 0

    for path in paths:
        relative = str(path.relative_to(ROOT))
        expected = data["files"].get(relative)

        if expected is None:
            print(f"[FAIL] missing manifest entry: {relative}")
            failures += 1
            continue

        if not path.exists():
            print(f"[FAIL] generated file missing: {relative}")
            failures += 1
            continue

        actual = path.read_text(encoding="utf-8")
        digest = sha256(actual)

        if digest != expected["sha256"]:
            print(f"[FAIL] hash mismatch: {relative}")
            failures += 1
        else:
            print(f"[PASS] {relative}")

    if failures:
        print()
        print(f"DETERMINISTIC VERIFY FAILED: {failures} issue(s)")
        sys.exit(1)

    print()
    print("DETERMINISTIC VERIFY PASSED")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Deterministic Phase 5 architecture generator"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate generation inputs without writing generated files.",
    )
    parser.add_argument(
        "--phase",
        type=int,
        default=5,
        help="Generation phase. Only phase 5 is currently supported.",
    )
    parser.add_argument(
        "--files",
        nargs="*",
        default=None,
        help="Optional generated file paths to scope generation.",
    )
    return parser.parse_args()


def main():
    print("=" * 70)
    print("PHASE 5 — REAL DETERMINISTIC CODE GENERATION")
    print("=" * 70)

    args = parse_args()

    if args.phase != 5:
        print(f"Unsupported generation phase: {args.phase}")
        return 2

    schema = load_schema()

    print(f"Project : {schema['project']}")
    print(f"Version : {schema['version']}")
    print(f"Output  : {schema['output_root']}")

    paths = all_files(schema)

    if args.files:
        requested = {
            Path(item).as_posix()
            for item in args.files
        }
        paths = [
            path
            for path in paths
            if path.relative_to(ROOT).as_posix() in requested
        ]

        if not paths:
            print()
            print("No requested generated files matched the schema.")
            return 2

    if args.dry_run:
        print()
        print("[DRY-RUN] Directory creation skipped")
        print("===== DRY RUN =====")
        for path in paths:
            print(f"[WOULD GENERATE] {path.relative_to(ROOT)}")
        print()
        print(f"Dry-run complete: {len(paths)} file(s).")
        return 0

    print()
    print("[1/7] Preparing directories")
    ensure_dirs()

    print()
    print("[2/7] Preparing canonical templates")
    bootstrap_templates(paths)

    print()
    print("[3/7] Generating architecture")
    generate(paths)

    print()
    print("[4/7] Deterministic verification")
    verify(paths)

    print()
    print("[5/7] Dart format")
    run([
        "dart",
        "format",
        "flutter_app/lib",
        "flutter_app/test",
    ])

    print()
    print("[6/7] Flutter analyze")
    run(
        ["flutter", "analyze"],
        cwd=ROOT / "flutter_app",
    )

    print()
    print("[7/7] Flutter tests")
    run(
        ["flutter", "test"],
        cwd=ROOT / "flutter_app",
    )

    print()
    print("=" * 70)
    print("PHASE 5 REAL CODEGEN: PASS")
    print("=" * 70)


if __name__ == "__main__":
    main()
