# Ownership Model

## Purpose

Define who controls the software project, who may authorize work on a device, and who may administer organization-managed devices. These are separate authority domains.

## Roles

### Project Owner
The Project Owner controls this repository and product lifecycle: source code, architecture, API configuration, release decisions, project roles, pull-request approval, and merge authorization. Project ownership does not grant authority over Apple security controls or devices belonging to other people.

### Device Owner
The Device Owner is the person or organization with a legitimate ownership or delegated authority relationship to a device. They may request diagnostics, review evidence, grant or withdraw consent for supported operations, and use official recovery channels. A device reference alone is not proof of ownership.

### Organization Administrator
An Organization Administrator acts only within a verified organization's delegated device-management scope. They may administer organization membership, policies, and managed devices where the organization has documented authority. This role cannot override Apple-controlled security states or grant authority outside the organization's scope.

### Technician / Operator
A Technician may perform assigned diagnostics and approved support workflows. They cannot grant themselves roles, change ownership, approve their own high-impact operation, or override a server decision.

## Separation of duties

- Repository administration is not device authorization.
- Device possession or USB connection is not proof of ownership.
- A Device Owner's consent is scoped, explicit, revocable, and time-bounded.
- Organization authority must be verified and scoped to the relevant device.
- High-impact recovery requires a fresh authorization check and human confirmation.
- The server is authoritative; the Flutter client only presents requests and results.

## Evidence required

Ownership and delegated authority must be established by a future trusted provider using a documented verification process. Until that provider exists, ownership is UNKNOWN and sensitive operations are DENY. Never collect Apple Account passwords, passcodes, recovery keys, or other secrets as proof.

## Current implementation status

This document defines the target model. Phase 1 has no production identity or ownership provider. Phase 2 adds read-only diagnostics and must not infer ownership from diagnostic results.
