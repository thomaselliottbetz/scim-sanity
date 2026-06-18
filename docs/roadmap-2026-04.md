# Roadmap — April 2026

## Overview

scim-sanity is evolving from a single-run conformance probe into a **stateful verification layer for SCIM interoperability**.

This document captures forward-looking direction independent of the current README roadmap.

---

## Core Product Evolution (Priority)

### 1. Persistent Run State

Introduce storage for probe runs:

- run metadata (target, mode, profile, timestamp, version)
- structured results
- retrieval of prior runs

**Purpose:** enable longitudinal analysis and convergence tracking.

---

### 2. Issue Fingerprints (Root-Cause Identity)

Define canonical issue identifiers.

Examples:
- WRONG_CONTENT_TYPE_RESPONSE
- MISSING_META_TIMESTAMPS
- LOCATION_HEADER_MISMATCH

Each includes:
- identifier
- category
- severity (P1–P5)
- remediation guidance

**Purpose:** collapse many failures into a small set of root causes.

---

### 3. Run Diffing / Regression Detection

Compare runs to identify:

- regressions
- fixes
- unchanged issues

Outputs:
- what improved
- what regressed
- what remains

**Purpose:** enable CI gating and iterative workflows.

---

### 4. Machine-Actionable Output

Extend result schema:

- attach fingerprints
- include category + priority
- structured remediation hints
- separate root causes from cascade failures

**Purpose:** enable programmatic consumption (pipelines, agents).

---

### 5. Packaging for Execution

#### Docker image

docker run scim-sanity probe <url> ...

#### GitHub Action
- payload linting
- probe execution

**Purpose:** reduce friction in CI/CD and orchestration.

---

## Protocol Coverage Expansion

### 6. Search Resource Validation

- validate individual resources in ListResponse.Resources

---

### 7. Discovery Schema Validation

- validate /Schemas and /ResourceTypes
- ensure consistency with implemented resources

---

### 8. PATCH Expansion

Current state:
- simple paths only

Future:
- filter-based paths
- multi-operation PATCH
- edge-case path resolution
- PATCH-specific error behavior

**Note:** prioritize based on observed real-world failures.

---

## Compatibility Intelligence (Emerging)

### 9. Expanded Profiles

- extend beyond current servers
- encode deviations explicitly
- separate:
  - request accommodations
  - response tolerances

---

### 10. Cross-Client Compatibility

Longer-term:

- identify patterns across identity providers
- surface compatibility signals:
  - likely to interoperate
  - known failure modes

---

## Direction

scim-sanity is moving toward:

> a verification layer that enables SCIM implementations to converge toward real interoperability through repeated, measurable feedback

---

## Priority Summary

1. State
2. Fingerprints
3. Diffing
4. Machine output
5. Packaging
6. Protocol depth (including PATCH)
7. Compatibility intelligence

---

## Why this exists separately

This roadmap reflects forward-looking product direction and may diverge from the README, which is optimized for current capabilities and users.
