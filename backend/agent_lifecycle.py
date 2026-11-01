"""In-memory, fail-closed lifecycle contract for the optional host agent.

This module models lifecycle state only. It does not start processes, install
services, bind sockets, persist state, or authorize device operations.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class AgentState(str, Enum):
    STOPPED = "STOPPED"
    STARTING = "STARTING"
    RUNNING = "RUNNING"
    STOPPING = "STOPPING"
    FAILED = "FAILED"


_ALLOWED_TRANSITIONS = {
    AgentState.STOPPED: {AgentState.STARTING},
    AgentState.STARTING: {AgentState.RUNNING, AgentState.STOPPING, AgentState.FAILED},
    AgentState.RUNNING: {AgentState.STOPPING, AgentState.FAILED},
    AgentState.STOPPING: {AgentState.STOPPED, AgentState.FAILED},
    AgentState.FAILED: {AgentState.STOPPED},
}


@dataclass
class AgentLifecycle:
    """Small deterministic state machine; callers supply external observations."""

    state: AgentState = AgentState.STOPPED
    failure_code: str | None = None

    def transition(self, target: AgentState, *, failure_code: str | None = None) -> None:
        if target not in _ALLOWED_TRANSITIONS[self.state]:
            raise ValueError(f"invalid_agent_transition:{self.state.value}:{target.value}")
        if target is AgentState.FAILED:
            if not failure_code or not failure_code.replace("_", "").isalnum():
                raise ValueError("failure_code_required")
            self.failure_code = failure_code[:64]
        else:
            if failure_code is not None:
                raise ValueError("failure_code_only_valid_for_failed_state")
            self.failure_code = None
        self.state = target

    def health(self) -> dict[str, object]:
        return {
            "schema_version": "1.0",
            "component": "host_diagnostics_agent",
            "state": self.state.value,
            "ready": self.state is AgentState.RUNNING,
            "failure_code": self.failure_code,
            "operation_performed": False,
            "authorization_granted": False,
        }
