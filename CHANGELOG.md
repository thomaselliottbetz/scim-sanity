# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
- **Security and Compliance Documentation**: Added compliance guides referencing CIS and Microsoft Security Benchmarks
  - CIS Azure Foundations Benchmark compliance
  - CIS Google Workspace Benchmark compliance
  - Microsoft Cloud Security Benchmark compliance
  - Compliance validation workflows and reporting

### Documentation
- Added Ansible integration section to README
- Added integration guides in `docs/integrations/`
- Added security and compliance documentation in `docs/security/`
- Added reference materials for CIS and Microsoft benchmarks in `docs/reference/`

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
