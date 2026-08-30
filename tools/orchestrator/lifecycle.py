#!/usr/bin/env python3

from __future__ import annotations


def all_phases_completed(
    registry: dict,
    state: dict,
) -> bool:
    registered = {
        phase["id"]
        for phase in registry.get("phases", [])
    }

    completed = set(
        state.get("completed_phases", [])
    )

    return bool(registered) and registered.issubset(completed)


def is_terminal_state(
    registry: dict,
    state: dict,
) -> bool:
    return all_phases_completed(registry, state)


def resolve_next_phase(
    registry: dict,
    state: dict,
):
    completed = set(
        state.get("completed_phases", [])
    )

    for phase in sorted(
        registry.get("phases", []),
        key=lambda item: item["id"],
    ):
        if phase["id"] not in completed:
            return phase

    return None
