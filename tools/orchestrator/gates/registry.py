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


COMMAND_GATES = {
    "dart_format": dart_format,
    "flutter_analyze": flutter_analyze,
    "flutter_test": flutter_test,
    "git_diff_check": git_diff_check,
    "contract_validation": contract_validation,
}


def run_command(command: list[str], cwd: Path):
    result = subprocess.run(
        command,
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    return {
        "command": command,
        "cwd": str(cwd.relative_to(ROOT)),
        "returncode": result.returncode,
        "passed": result.returncode == 0,
        "output": result.stdout,
    }
