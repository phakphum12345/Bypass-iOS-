#!/usr/bin/env python3

from __future__ import annotations

from typing import Callable


def repair_until_pass(
    validate: Callable[[], bool],
    repair: Callable[[], None],
    max_attempts: int = 3,
) -> dict:
    attempts = 0

    while True:
        if validate():
            return {
                "status": "passed",
                "attempts": attempts,
            }

        if attempts >= max_attempts:
            return {
                "status": "failed",
                "attempts": attempts,
            }

        attempts += 1
        repair()
