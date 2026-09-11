# System Overview

## Architecture

USER
  ↓
FLUTTER EXTERNAL TOOL
  ↓
API GATEWAY
  ↓
DEVICE SERVICE
  ↓
DEVICE REGISTRY
  ↓
DEVICE INTELLIGENCE
  ↓
ELIGIBILITY
  ↓
AUTHORIZATION
  ↓
ENTITLEMENT
  ↓
SERVICE WORKFLOW
  ↓
AUDIT / EVIDENCE

## Runtime Flow

Request
→ Validate
→ Identify
→ Evaluate Capability
→ Evaluate Policy
→ Authorize
→ Resolve Entitlement
→ Execute permitted workflow
→ Record Evidence

Any failed security prerequisite results in DENY.

## Production Scaling

Event
→ Queue
→ Stateless Worker Pool
→ Execution
→ Evidence
→ Final Gate

Workers are stateless so the execution layer can scale horizontally.
