# Agentic Framing of scim-sanity

## Overview

scim-sanity can be understood not only as a SCIM validation tool, but as a **verification oracle** within an iterative development loop, including workflows driven by ML agents.

The core idea is that modern systems—especially SaaS platforms—are increasingly constructed or modified by automated agents. These systems often need to implement SCIM servers for enterprise identity lifecycle provisioning.

scim-sanity provides an external, structured feedback mechanism to determine whether those implementations actually conform to expectations and interoperate with real identity providers.

## The Agentic Loop

A typical agent-driven workflow:

```
Build or modify SCIM server
        ↓
Deploy or run locally
        ↓
Call scim-sanity probe
        ↓
Parse structured results
        ↓
Identify highest-priority issue
        ↓
Apply fix
        ↓
Repeat
```

This loop allows convergence toward correct behavior.

## Role of scim-sanity

scim-sanity acts as:

- A **behavioral verifier** (not just schema validation)
- A **source of structured truth** external to the implementation
- A **feedback oracle** enabling iterative refinement

This is especially important because SCIM correctness depends on multi-step behavior and real-world interoperability conditions, not just static code validity.

## Current Capabilities Supporting This Model

- Live probing across SCIM lifecycle operations
- Structured validation output
- Prioritized findings
- Profile-based accommodations (e.g., Entra)
- Strict vs compat evaluation modes

## Missing Capabilities for Full Agentic Use

To fully support agent-driven development loops, additional capabilities are needed:

- Persistent run state
- Normalized issue fingerprints
- Run-to-run comparison (diffing)
- Regression detection

These would allow agents to measure progress over time rather than operate on single-run snapshots.

## Strategic Implication

This framing shifts scim-sanity from:

> a validation tool

into:

> a verification layer for identity lifecycle correctness in automated system construction

## Conclusion

Agents can generate SCIM implementations, but they cannot reliably validate them without an external oracle. scim-sanity fills that role.
