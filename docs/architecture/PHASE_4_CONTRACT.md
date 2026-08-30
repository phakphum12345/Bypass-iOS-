# Bypass-iOS — Phase 4 Decision Pipeline Contract

## Purpose

Phase 4 integrates the Phase 3 domain models and services into one
explicit decision pipeline.

## Pipeline

Device
→ Policy
→ Authorization
→ Entitlement
→ Decision
→ Evidence

## Security Rule

A denied authorization result remains denied.

The client cannot override server authorization.

## Evidence Rule

Pipeline evaluation produces evidence for the relevant decision stages.

## Scope

Phase 4 integrates the defensive architecture only.

No platform-security bypass functionality is implemented.

## Validation

Validation is performed during FINAL GATE.
