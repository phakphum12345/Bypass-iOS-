#!/usr/bin/env python3

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass
class TaskPlan:
    task_id: str
    phase: int
    objective: str
    allowed_paths: list[str]
    planned_files: list[str] = field(default_factory=list)


@dataclass
class ProviderResult:
    passed: bool
    output: str = ""
    error: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


class TaskProvider(Protocol):
    def plan(self, task: dict[str, Any]) -> TaskPlan:
        ...


class GeneratorProvider(Protocol):
    def dry_run(
        self,
        plan: TaskPlan,
    ) -> ProviderResult:
        ...

    def execute(
        self,
        plan: TaskPlan,
    ) -> ProviderResult:
        ...


class RepairProvider(Protocol):
    def repair(
        self,
        plan: TaskPlan,
        failures: list[dict[str, Any]],
        attempt: int,
    ) -> ProviderResult:
        ...


class GitProvider(Protocol):
    def commit(
        self,
        message: str,
        allowed_paths: list[str],
    ) -> ProviderResult:
        ...

    def push(
        self,
        branch: str,
    ) -> ProviderResult:
        ...

    def open_pr(
        self,
        branch: str,
        base: str,
        title: str,
        body: str,
    ) -> ProviderResult:
        ...

    def ci_status(
        self,
        branch: str,
    ) -> ProviderResult:
        ...
