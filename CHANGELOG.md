# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.7.2] - 2026-04-10

### Added
- **Web GUI profile selector** — Probe page now exposes a profile dropdown (`entra`, `fortiauthenticator`) and a conditional user domain field (shown when `entra` is selected). Selecting a profile auto-enables compat mode; a hint is shown if compat is manually disabled while a profile is active.
- **Web GUI Advanced section** — Collapsed by default; exposes proxy URL and CA bundle path fields for environments that require them. Most users do not need these options.

### Fixed
- **`run_probe_api()` missing `proxy` and `ca_bundle` parameters** — both options were silently dropped when calling the probe via the web API; they are now accepted and forwarded to `SCIMClient()`.
- **`api.py` and TypeScript client** — `ProbeRequest` updated to accept `proxy` and `ca_bundle` in both the Pydantic model and the TypeScript interface.

### Changed
- **`--proxy` CLI help text** — now explicitly notes that `HTTPS_PROXY`/`HTTP_PROXY` env vars are not inherited.
- **README Probe Options** — `--proxy` and `--ca-bundle` entries note that most users don't need them; `--ca-bundle` entry mentions `REQUESTS_CA_BUNDLE`/`SSL_CERT_FILE` env vars for container deployments.

### Tests
- Added signature regression test for `proxy` and `ca_bundle` parameters in `run_probe_api()`.

## [0.7.1] - 2026-04-08

### Added
- **`fortiauthenticator` profile** — documents 5 known FortiAuthenticator RFC deviations (wrong Content-Type, missing meta timestamps, missing Location on 201, missing `status` in error bodies, non-compliant discovery endpoints). No payload injection required; use with `--compat`. Validated against v8.0.1 build0033 (GA).
- **`PROFILE_INJECTIONS` registry** — data-driven injection descriptions in `scim-sanity profiles <name>` output, replacing a hardcoded Entra-only block. Scales to all current and future profiles.

### Fixed
- **`run_probe_api` missing `user_domain` parameter** — the web API entry point was not forwarding `user_domain` to profile field generation, so `--user-domain` had no effect when called via the REST API.
- **Proxy suppression when `--proxy` is not set** — `requests` was picking up `HTTPS_PROXY`/`HTTP_PROXY` environment variables and macOS system proxies unexpectedly. Now explicitly suppressed unless `--proxy` is passed. **Note:** if you previously relied on `HTTPS_PROXY`/`HTTP_PROXY` env vars to reach your SCIM target, pass `--proxy` explicitly instead.

### Changed
- **`--compat` help text** — now describes what compat mode does and points to `scim-sanity profiles <name>` for per-server detail.
- **Fix Summary labels in web GUI** — "Trouble:" and "Rationale:" labels added to match CLI output format.
- Spelling normalization: "prioritised" → "prioritized" across docs.

## [0.7.0] - 2026-04-05

### Added
- **Named server profiles** (`--profile entra`) — inject non-RFC payload fields required by specific servers. Profiles are applied before `--extra-user-fields` overrides, so explicit flags always win.
- **`scim-sanity profiles` subcommand** — list all profiles (`scim-sanity profiles`) or show full detail for a specific profile (`scim-sanity profiles entra`): required fields, known RFC deviations with RFC citations, recommended command, and external references.
- **`entra` profile** for Microsoft Entra ID SCIM server — automatically injects `password`, `mailNickname`, enterprise extension schema, and `urn:ietf:params:scim:schemas:extension:Microsoft:Entra:2.0:User` for Users; `mailEnabled`, `mailNickname`, `securityEnabled`, and `urn:ietf:params:scim:schemas:extension:Microsoft:Entra:2.0:Group` for Groups. Documents 12 known Entra RFC deviations.
- **`--extra-user-fields`** CLI option — merge arbitrary JSON fields into user creation payloads without writing a profile (e.g. `--extra-user-fields '{"password":"secret"}'`).
- **`--user-domain`** CLI option — override the domain portion of generated `userName` values. Required for servers (including Entra) that validate `userName` against a list of verified tenant domains.
- **Named Fix Summary patterns for Entra deviations** — E1 (PUT 405), E1b (stale state after failed PUT), E2 (PATCH 204), E3 (lowercase `meta.resourceType`), E4 (nonexistent resource returns 400 not 404), E5 (group member referential integrity). Eliminates `[?]` catch-all entries when probing Entra with `--compat`.
- **Combined message+phase matching in Fix Summary** — `_KNOWN_ISSUES` entries can now match on both `message` substring and `phase` prefix simultaneously, enabling precise targeting of failures that share a generic message (e.g. "Expected 200, got 400") across multiple phases.

### Fixed
- **DELETE request header rejection** — Some servers (including Entra) reject DELETE requests that include `Accept: application/scim+json`, returning 400. The HTTP client no longer sends `Accept` or `Content-Type` headers on DELETE requests.
- **DELETE body false positive** — The "DELETE 204 response should have no body" validator check was firing on non-204 error responses (`if body` instead of `elif body`). Fixed so the check only triggers when the status is actually 204.
- **Group PATCH used `active` attribute** — The probe was sending `PATCH active=false` to Groups. RFC 7643 §4.2 does not define `active` on Group resources. Groups now use `PATCH displayName` instead.
- **Case-insensitive `Resources` key in ResourceTypes discovery** — Entra returns `"resources"` (lowercase) in its ResourceTypes response. The discovery parser now falls back to the lowercase key when `"Resources"` is absent, preventing User/Group CRUD phases from being incorrectly skipped.

## [0.6.0] - 2026-03-27

### Added
- **Web GUI** (`scim-sanity web`) — optional browser-based interface built with React and the AWS Cloudscape Design System. Install with `pip install 'scim-sanity[web]'`.
  - **Validate page** — interactive payload linter with JSON editor, operation toggle (full/PATCH), example dropdown, and error table
  - **Probe page** — configure and run a live SCIM server conformance probe; results grouped by phase with expandable sections and Fix Summary
  - **Examples page** — browsable RFC example payload library with resource type and validity filters; "Load in Validator" navigates to the Validate page with the payload pre-loaded
- `scim_sanity/api.py` — FastAPI REST layer (`POST /api/validate`, `POST /api/probe`, `GET /api/examples`) wrapping the core library
- `scim_sanity/examples.py` — curated catalog of 16 SCIM payloads (10 valid, 6 invalid/educational) covering User, Group, Agent, AgenticApplication, and PATCH operations
- `[web]` optional dependency group in `pyproject.toml` (`fastapi`, `uvicorn`)
- `ValidationError.to_dict()` for JSON serialization of validation errors
- `run_probe_api()` in `probe/runner.py` — returns structured dict for API use; `build_results_dict()` extracted from `_print_json()` as shared helper

### Changed
- CLI `--version` now reports `0.6.0`

## [0.5.5] - 2026-02-24

### Added
- Planned Improvements section in README (PATCH filter expressions, Phase 1/6 depth, GitHub Action, Docker image)

### Added
- **RFC citations on all failure messages** — every error message now cites the specific RFC clause it enforces (e.g. `RFC 7644 §8.1`, `RFC 7643 §3.1`), so developers know exactly where to look
- **Verdict line** — a plain-English result at the end of terminal output: "N root causes account for the failures. Resolve P1 first." or "All tests passed."
- **PASS annotations on verification steps** — GET after PUT, GET after PATCH, DELETE, and GET after DELETE now show a brief note on what was verified (e.g. "active=false confirmed", "404 confirmed — resource no longer exists")
- **Catch-all Fix Summary entry** — failures that don't match any known root cause pattern now surface as a `?` entry rather than falling through silently
- **`pass_message` parameter on `_validation_results`** — allows callers to attach a verification note to PASS results

## [0.5.4] - 2026-02-24

### Added
- Probe terminal output now shows a header line under the title with scim-sanity version, validation mode, and run timestamp
- Same fields (`scim_sanity_version`, `mode`, `timestamp`) added to JSON output as top-level keys

### Changed
- "Configuration" pseudo-phase removed from results — mode is now shown in the header and no longer counted as a passed test

### Fixed
- `__init__.py` `__version__` was stale (0.5.1); now kept in sync with pyproject.toml

## [0.5.3] - 2026-02-23

### Added
- **Fix Summary** in terminal output: when failures are present, a prioritised block lists each distinct root cause with `Trouble:`, `Fix:`, and `Rationale:` labels, grouping related failures to reduce noise
- **`issues` array in JSON output**: machine-readable equivalent of the Fix Summary, with `priority`, `title`, `fix`, and `rationale` fields per issue
- **Content-Type validation on list responses**: `validate_list_response` now checks `Content-Type: application/scim+json` on ListResponse replies, consistent with all other response validators

### Changed
- Terminal output color scheme: removed green/yellow/cyan ANSI colors; PASS is bold, WARN/SKIP are dim, FAIL remains red — reduces visual noise on varied terminal themes
- Documentation substantially revised: README reordered to lead with probe; integration guides (Entra ID, Google Workspace) corrected for SCIM client/server framing; compliance docs rewritten to remove unsupported CIS/MCSB control mapping claims

## [0.5.1] - 2026-02-21

### Fixed
- `--proxy` and `--ca-bundle` were accepted by the CLI but silently ignored — they are now correctly passed through to the HTTP client
- `--version` flag now works correctly
- Click is now a required dependency rather than optional, eliminating a class of subtle CLI divergence bugs

## [0.5.0] - 2026-02-19

### Added
- **Transient 500 detection**: When a POST returns 500, the probe retries once after a brief delay using identical request headers. If the retry succeeds, the result is emitted as a `WARN` ("transient instability") and the CRUD lifecycle continues with the retry response, giving a full conformance picture despite the initial failure. If both attempts fail, content-type rejection diagnosis runs next.
- **Content-Type request rejection diagnosis**: When a POST consistently returns 500, the probe retries with `Content-Type: application/json`. If that succeeds, the failure is reported as a `FAIL` with a specific RFC 7644 §8.2 citation: *"Server rejected Content-Type: application/scim+json but accepted application/json"*. Any resource created during diagnosis is cleaned up immediately.
- `extra_headers` parameter on `SCIMClient.post()`, consistent with `put()` and `patch()`.

### Fixed
- **False positive on Group PATCH verification**: The `active=false` PATCH follow-up GET check incorrectly applied to Group resources. `active` is not a Group attribute per RFC 7643 §4.2, so a conformant server that doesn't store it on Groups was incorrectly reported as failing. For Groups, the follow-up GET now only verifies the server responds 200; the `active` field check is correctly limited to resource types that define it (User, Agent, AgenticApplication).

### Changed
- **Error response cascade noise suppression**: When `validate_resource_response` receives a 4xx or 5xx status, it now returns after reporting only the unexpected status code. Previously, predictable side-effects of an error response (missing `id`, `meta`, `schemas`) were reported as additional failures, obscuring the root cause.
- **Phase 7 400 error response validation**: The "invalid body" and "missing userName" error handling tests now validate the full SCIM error response schema (schema URN, `status` field) in addition to checking the HTTP status code, consistent with the existing 404 test. Servers that return unstructured 400 bodies are now correctly flagged.

## [0.4.0] - 2026-01-15

### Added
- **Server conformance probe** (`scim-sanity probe`): 7-phase live SCIM server testing via real CRUD, search, and error-handling flows
  - Phase 1: Discovery — GET `/ServiceProviderConfig`, `/Schemas`, `/ResourceTypes`
  - Phase 2–5: User, Group, Agent, AgenticApplication CRUD lifecycles (POST→GET→PUT→PATCH→DELETE→404)
  - Phase 5a: Agent rapid lifecycle — create and immediately delete multiple agents to test ephemeral provisioning
  - Phase 6: Search — ListResponse structure, filter queries, pagination, `count=0` boundary case
  - Phase 7: Error handling — 404 on nonexistent resource, 400 on invalid body, 400 on missing required fields
- **Strict and compat validation modes** — strict (default) treats all RFC deviations as failures; compat mode downgrades known real-world deviations (wrong Content-Type, missing Location header, ETag mismatch, DELETE body) to warnings
- **JSON output** (`--json-output`) with stable schema for CI/CD integration
- **Resource type filtering** (`--resource`) to test a single resource type
- **TLS options**: `--tls-no-verify` and `--ca-bundle` for self-signed certificate environments
- **Proxy support** via `--proxy`
- **Authorization header redaction** in JSON output and logs

## [0.3.0] - 2026-01-02

### Added
- **Ansible Action Plugin**: Added `scim_validate` action plugin for SCIM validation in Ansible playbooks
  - Supports inline payloads and file paths
  - Validates full resources and PATCH operations
  - Returns structured validation results for conditional workflows
- **Identity Management Integration Guides**: Added documentation for Microsoft Entra ID and Google Workspace integration
  - Pre-provisioning validation workflows
  - CI/CD integration examples
  - Common SCIM operations and error handling
- **Security and Compliance Documentation**: Added compliance guide describing scim-sanity's actual compliance contributions (payload correctness, deprovisioning validation, audit trail detection)

### Documentation
- Added Ansible integration section to README
- Added integration guides in `docs/integrations/`
- Added security and compliance documentation in `docs/security/`

## [0.2.1] - 2025-12-15

### Changed
- Updated CI to remove Python 3.7 and 3.8 (EOL) from test matrix
- Updated minimum Python version requirement to 3.9

## [0.2.0] - 2024-12-15

### Added
- **Agent and AgenticApplication resource support**: Added validation for Agent and AgenticApplication resource types as defined in IETF draft-abbey-scim-agent-extension-00
  - Validates Agent resources with required `name` attribute
  - Validates AgenticApplication resources with required `name` attribute
  - Auto-detects resource type from schema URIs (no flags needed)
  - Supports all Agent schema attributes (owner, subject, protocols, applications, etc.)
- **Pre-commit hook integration**: Added `.pre-commit-config.yaml` for automatic validation on git commits
  - Validates all JSON files on commit
  - Excludes common configuration files and dependency directories
  - Ideal for IaC repositories and security automation pipelines
- Comprehensive test suite for Agent and AgenticApplication resources

### Changed
- Updated CLI and documentation to reflect Agent/AgenticApplication support
- Enhanced error messages to include new resource types
- Improved schema registry to support Agent extension schemas

### Documentation
- Added "Pre-commit Integration" section to README
- Added "Agent and AgenticApplication Support" section with use cases and examples
- Added pre-commit.ci badge
- Updated all descriptions and docstrings to include Agent/AgenticApplication support

## [0.1.0] - Initial Release

### Added
- Core SCIM 2.0 User resource validation
- Core SCIM 2.0 Group resource validation
- Enterprise User Extension schema support
- PATCH operation validation
- Command-line interface with color output
- Comprehensive error messages with location information
- Support for validation via file or stdin
