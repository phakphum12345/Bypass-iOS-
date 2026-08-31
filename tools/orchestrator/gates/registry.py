from __future__ import annotations

from pathlib import Path
import subprocess

from .contract import contract_validation


ROOT = Path(__file__).resolve().parents[3]
FLUTTER_APP = ROOT / "flutter_app"


def dart_format():
    return {
        "command": [
            "dart",
            "format",
            "--output=none",
            "--set-exit-if-changed",
            "lib",
            "test",
        ],
        "cwd": FLUTTER_APP,
    }


def flutter_analyze():
    return {
        "command": ["flutter", "analyze"],
        "cwd": FLUTTER_APP,
    }


def flutter_test():
    return {
        "command": ["flutter", "test"],
        "cwd": FLUTTER_APP,
    }


def git_diff_check():
    return {
        "command": ["git", "diff", "--check"],
        "cwd": ROOT,
    }


def validate_documentation():
    required = [
        ROOT / "docs/architecture/DECISION_PIPELINE.md",
        ROOT / "docs/architecture/EVIDENCE_AUDIT.md",
        ROOT / "docs/architecture/PHASE_3_CONTRACT.md",
        ROOT / "docs/architecture/PHASE_4_CONTRACT.md",
        ROOT / "docs/architecture/PHASE_5_CONTRACT.md",
        ROOT / "docs/architecture/PHASE_6_CONTRACT.md",
        ROOT / "docs/architecture/PHASE_7_CONTRACT.md",
        ROOT / "docs/architecture/PHASE_8_CONTRACT.md",
        ROOT / "docs/architecture/PHASE_9_RELEASE_CONTRACT.md",
        ROOT / "docs/architecture/SECURITY_BOUNDARIES.md",
    ]

    missing = [
        str(path.relative_to(ROOT))
        for path in required
        if not path.is_file() or not path.read_text().strip()
    ]

    if missing:
        return {
            "passed": False,
            "output": (
                "Missing or empty documentation:\n"
                + "\n".join(f"- {item}" for item in missing)
            ),
        }

    competing = list((ROOT / "flutter_app").glob("**/architecture"))

    if competing:
        return {
            "passed": False,
            "output": (
                "Competing Flutter-local architecture tree found:\n"
                + "\n".join(
                    str(path.relative_to(ROOT))
                    for path in competing
                )
            ),
        }

    return {
        "passed": True,
        "output": "Canonical architecture documentation validated.",
    }


def documentation_validation():
    return {
        "command": ["documentation-validation"],
        "cwd": ROOT,
        "validator": validate_documentation,
    }


def web_build():
    return {
        "command": [
            "flutter",
            "build",
            "web",
            "--release",
        ],
        "cwd": FLUTTER_APP,
    }


def linux_build():
    return {
        "command": [
            "flutter",
            "build",
            "linux",
            "--release",
        ],
        "cwd": FLUTTER_APP,
    }


def validate_security():
    required_files = [
        ROOT / "flutter_app/lib/core/security/security_boundary.dart",
        ROOT / "flutter_app/lib/core/pipeline/decision_pipeline.dart",
    ]

    missing = [
        str(path.relative_to(ROOT))
        for path in required_files
        if not path.is_file()
    ]

    if missing:
        return {
            "passed": False,
            "output": (
                "Missing security files:\n"
                + "\n".join(f"- {item}" for item in missing)
            ),
        }

    boundary = required_files[0].read_text()
    pipeline = required_files[1].read_text()

    required_tokens = [
        "authorization.isAuthorized",
        "entitlement.isActive",
        "decision.allowed",
    ]

    missing_tokens = [
        token
        for token in required_tokens
        if token not in boundary
    ]

    if "security_boundary" not in pipeline:
        missing_tokens.append("security_boundary")

    if missing_tokens:
        return {
            "passed": False,
            "output": (
                "Security boundary markers missing:\n"
                + "\n".join(f"- {item}" for item in missing_tokens)
            ),
        }

    return {
        "passed": True,
        "output": "Security boundary markers validated.",
    }


def security_validation():
    return {
        "command": ["security-validation"],
        "cwd": ROOT,
        "validator": validate_security,
    }


def git_sync_check():
    fetch = subprocess.run(
        ["git", "fetch", "origin", "main"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )

    if fetch.returncode != 0:
        return {
            "command": ["git", "fetch", "origin", "main"],
            "cwd": ROOT,
            "returncode": fetch.returncode,
            "passed": False,
            "output": fetch.stdout,
        }

    local = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )

    remote = subprocess.run(
        ["git", "rev-parse", "origin/main"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )

    if local.returncode != 0 or remote.returncode != 0:
        return {
            "command": ["git", "rev-parse"],
            "cwd": ROOT,
            "returncode": 1,
            "passed": False,
            "output": local.stdout + remote.stdout,
        }

    local_sha = local.stdout.strip()
    remote_sha = remote.stdout.strip()

    return {
        "command": ["git", "rev-parse", "HEAD", "origin/main"],
        "cwd": ROOT,
        "returncode": 0 if local_sha == remote_sha else 1,
        "passed": local_sha == remote_sha,
        "output": (
            f"HEAD={local_sha}\n"
            f"origin/main={remote_sha}\n"
        ),
    }


COMMAND_GATES = {
    "dart_format": dart_format,
    "flutter_analyze": flutter_analyze,
    "flutter_test": flutter_test,
    "git_diff_check": git_diff_check,
    "contract_validation": contract_validation,
    "documentation_validation": documentation_validation,
    "web_build": web_build,
    "linux_build": linux_build,
    "security_validation": security_validation,
    "git_sync_check": git_sync_check,
}


def run_command(command: list[str], cwd: Path):
    result = subprocess.run(
        command,
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )

    return {
        "command": command,
        "cwd": str(cwd.relative_to(ROOT)),
        "returncode": result.returncode,
        "passed": result.returncode == 0,
        "output": result.stdout,
    }
