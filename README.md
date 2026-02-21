# scim-sanity

Validate SCIM 2.0 payloads (static linting) and probe live SCIM servers for RFC 7643/7644 conformance. Supports User, Group, Agent, and AgenticApplication resources, including agentic identity types per `draft-abbey-scim-agent-extension-00`.

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/thomaselliottbetz/scim-sanity/main.svg)](https://results.pre-commit.ci/latest/github/thomaselliottbetz/scim-sanity/main)

## Features

**scim-sanity** is a **pragmatic, production-oriented SCIM conformance and interoperability harness**:
- **Payload validation (linting)** — Static SCIM JSON analysis before sending data to a server. Catches missing required attributes, immutable field violations, null value misuse, and schema URN errors.
- **Server conformance probe** — Run a 7-phase CRUD lifecycle test against a live SCIM endpoint. Tests discovery, User/Group/Agent/AgenticApplication operations, search, pagination, and error handling.
- **Agentic identity support** — Validates Agent and AgenticApplication resources per IETF `draft-abbey-scim-agent-extension-00`.
- **Strict and compat modes** — Strict mode (default) treats all spec deviations as failures. Compat mode downgrades known real-world deviations (e.g., `application/json` instead of `application/scim+json`) to warnings.
- It performs **behavioral, black-box testing** of SCIM servers via real CRUD, search, and lifecycle flows.
- It focuses on high-value, real-world failure modes and interoperability gaps. It is designed to **surface real-world integration failures**, not to provide formal certification or exhaustive proof of RFC compliance.
- **Minimal dependencies** — Requires only Click. The `requests` library is auto-detected and used when available for richer HTTP handling, but is not required.

## Installation

```bash
pip install scim-sanity
```

Or from source:

```bash
git clone https://github.com/thomaselliottbetz/scim-sanity.git
cd scim-sanity
python -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
```

## Payload Validation (Linting)

Statically validate (lint) SCIM resource payloads and PATCH operations before sending them to a server. Resource type is auto-detected from schema URNs. This is a spec-driven validator with linter-style ergonomics: fast, offline, and suitable for CI/CD gating.

```bash
# Validate a resource file
scim-sanity user.json

# Validate a PATCH operation
scim-sanity --patch patch.json

# Validate from stdin
echo '{"schemas":["urn:ietf:params:scim:schemas:core:2.0:User"],"userName":"user@example.com"}' | scim-sanity --stdin

# Use in CI/CD pipelines
scim-sanity payload.json || exit 1
```

### Validation Rules

**Required attributes:**
- User: `userName`
- Group: `displayName`
- Agent: `name`
- AgenticApplication: `name`

**What it checks:**
- Schema URN validity and presence
- Required attributes per resource type
- Immutable attributes (`id`, `meta`) not set by client
- Null values (use PATCH `remove` instead)
- PATCH operation structure (`op`, `path`, `value` correctness)
- Complex and multi-valued attribute structure

### Exit Codes

- `0` — Validation passed (or all probe tests passed)
- `1` — Validation failed, probe failures detected, or error

## Server Conformance Probe

Test a live SCIM server for RFC 7643/7644 conformance. The probe **creates, modifies, and deletes real resources** on the target server, then cleans up after itself.

⚠️ Warning: This tool performs destructive operations. Do not run against production tenants without explicit authorization.

```bash
# Basic probe with bearer token
scim-sanity probe https://example.com/scim/v2 --token <token> --i-accept-side-effects

# Basic auth
scim-sanity probe https://example.com/scim/v2 --username admin --password secret --i-accept-side-effects

# Compat mode (known deviations become warnings, not failures)
scim-sanity probe <url> --token <token> --compat --i-accept-side-effects

# JSON output for CI/CD
scim-sanity probe <url> --token <token> --json-output --i-accept-side-effects

# Test only a specific resource type
scim-sanity probe <url> --token <token> --resource Agent --i-accept-side-effects

# Self-signed certificates
scim-sanity probe <url> --token <token> --tls-no-verify --i-accept-side-effects

# Leave test resources on the server for inspection
scim-sanity probe <url> --token <token> --skip-cleanup --i-accept-side-effects

# Custom timeout and proxy
scim-sanity probe <url> --token <token> --timeout 60 --proxy http://proxy:8080 --i-accept-side-effects

# Custom CA bundle
scim-sanity probe <url> --token <token> --ca-bundle /path/to/ca-cert.pem --i-accept-side-effects
```

### Probe Options

| Option | Description |
|--------|-------------|
| `--token` | Bearer token for authentication |
| `--username` / `--password` | Basic auth credentials |
| `--i-accept-side-effects` | **Required.** Acknowledge that the probe creates/deletes resources |
| `--strict` / `--compat` | Strict (default) or compat validation mode |
| `--json-output` | Output results as JSON |
| `--resource` | Test a specific resource type (User, Group, Agent, AgenticApplication) |
| `--skip-cleanup` | Leave test resources on the server |
| `--tls-no-verify` | Skip TLS certificate verification |
| `--timeout` | Per-request timeout in seconds (default: 30) |
| `--proxy` | HTTP/HTTPS proxy URL |
| `--ca-bundle` | Path to custom CA certificate bundle |

### Safety Guardrails

The probe implements several safety measures to prevent accidental damage:

- **Explicit consent** — Refuses to run without `--i-accept-side-effects`. Prints a summary of planned operations.
- **Namespace isolation** — All test resources are prefixed with `scim-sanity-test-` to avoid collisions with real data.
- **Resource caps** — Hard limit of 10 agents in rapid lifecycle tests.
- **429 retry** — Automatically retries on 429 Too Many Requests, honoring `Retry-After` headers (max 3 retries).
- **500 transience detection** — When a POST returns 500, the probe retries once after a brief delay using the same request headers. If the retry succeeds, the result is recorded as a warning ("transient instability") and the CRUD lifecycle continues with the resource created by the retry. If both attempts fail, content-type rejection diagnosis runs before reporting the final failure.
- **Timeouts** — Per-request timeouts prevent hung runs.
- **Cleanup** — Deletes all created test resources in reverse order (groups before users). Skippable with `--skip-cleanup`.
- **Failure semantics** — If the process is interrupted, partial cleanup may occur; orphaned test resources are possible and should be removed manually.
- **Secret redaction** — Authorization headers are redacted in any JSON output or logs.

### Test Sequence

The probe runs 7 phases:

1. **Discovery** — GET `/ServiceProviderConfig`, `/Schemas`, `/ResourceTypes`. Validates Content-Type headers and response structure.
2. **User CRUD Lifecycle** — POST (201), GET (200), PUT (200 + verify change), PATCH active=false (200 + verify), DELETE (204), GET (404).
3. **Group CRUD Lifecycle** — Same pattern as User, plus PATCH add/remove members.
4. **Agent CRUD Lifecycle** — Same pattern. Skipped if server doesn't advertise Agent support in `/ResourceTypes`.
5. **AgenticApplication CRUD Lifecycle** — Same pattern. Skipped if unsupported.
5a. **Agent Rapid Lifecycle** — Create and immediately delete multiple agents (default 10) to test ephemeral provisioning patterns.
6. **Search** — ListResponse structure, filter queries, pagination parameters, `count=0` boundary case.
7. **Error Handling** — GET nonexistent resource (expect 404), POST invalid body (expect 400), POST missing required fields (expect 400). Validates SCIM error response schema.

### Strict vs Compat Mode

**Strict mode** (`--strict`, default) treats all RFC deviations as failures.

**Compat mode** (`--compat`) applies a curated **Deviation Policy**: known, widespread ecosystem deviations are downgraded to warnings instead of failures. This list is intentional and versioned.
Current compat warnings include:
- `application/json` instead of `application/scim+json`
- DELETE 204 with response body
- Location header mismatch with `meta.location`
- Missing error schema in error responses
- ETag/meta.version mismatch

Warnings appear in output but don't cause a non-zero exit code.

**Always failures (not compat-eligible):** Some deviations are reported as `FAIL` in both strict and compat mode because they fundamentally break RFC-compliant clients:
- Server rejects `Content-Type: application/scim+json` requests (e.g., with 500) but accepts `application/json` — diagnosed automatically and cited against RFC 7644 §8.2.

**Error response reporting:** When a server returns a 4xx or 5xx status for a resource endpoint, only the unexpected status code is reported. Predictable side-effects (missing `id`, `meta`, `schemas` in the error body) are suppressed to avoid obscuring the root cause with cascade noise.

#### Real-World Server Behavior

Enterprise SCIM servers often exhibit:

- **Rate limiting** (429 + Retry-After)
- **Eventual consistency** (a GET immediately after PUT may briefly return stale data)
- **Partial filter support** or restricted query capabilities

scim-sanity attempts to behave accordingly by retrying on 429, validating boundary cases, and clearly reporting unsupported or nonconformant behavior.

### JSON Output (Stable Interface)

```bash
scim-sanity probe <url> --token <token> --json-output --i-accept-side-effects
```

```json
{
  "version": "0.5.0",
  "mode": "compat",
  "summary": {
    "total": 35,
    "passed": 33,
    "failed": 0,
    "warnings": 2,
    "skipped": 0,
    "errors": 0
  },
  "results": [
    {"name": "GET /ServiceProviderConfig", "status": "pass", "phase": "Phase 1 — Discovery"},
    {"name": "GET /ServiceProviderConfig", "status": "warn", "message": "Content-Type should be application/scim+json, got 'application/json'", "phase": "Phase 1 — Discovery"}
  ]
}
```
The JSON schema is treated as a public interface and is stable within major versions.

## Payload Examples

### Valid User Resource

```json
{
  "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
  "userName": "john.doe@example.com",
  "name": {
    "givenName": "John",
    "familyName": "Doe"
  },
  "emails": [
    {
      "value": "john.doe@example.com",
      "type": "work",
      "primary": true
    }
  ],
  "active": true
}
```

### Valid Group Resource

```json
{
  "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Group"],
  "displayName": "Engineering Team",
  "members": [
    {
      "value": "user-id-123",
      "display": "John Doe",
      "type": "User"
    }
  ]
}
```

### Valid Agent Resource

```json
{
  "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Agent"],
  "name": "research-assistant"
}
```

### Valid AgenticApplication Resource

```json
{
  "schemas": ["urn:ietf:params:scim:schemas:core:2.0:AgenticApplication"],
  "name": "assistant-platform"
}
```

### Valid PATCH Operation

```json
{
  "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
  "Operations": [
    {
      "op": "replace",
      "path": "displayName",
      "value": "New Name"
    }
  ]
}
```

## Pre-commit Integration

```yaml
repos:
  - repo: local
    hooks:
      - id: scim-sanity
        name: Validate SCIM resources
        entry: python -m scim_sanity
        language: system
        types: [json]
        exclude: |
          (?x)^(
            .*/node_modules/.*|
            .*/\.venv/.*|
            .*/venv/.*|
            .*package\.json$|
            .*package-lock\.json$|
            .*tsconfig.*\.json$|
            .*jsconfig\.json$
          )$
        pass_filenames: true
        stages: [commit]
```

## Ansible Integration

Action plugin for SCIM validation in Ansible playbooks. See [ansible/README.md](ansible/README.md).

```yaml
- name: Validate SCIM payload
  scim_validate:
    payload: "{{ user_payload }}"
    operation: full
  register: validation_result
```

## Identity Provider Guides

- [Microsoft Entra ID Integration](docs/integrations/entra-id.md)
- [Google Workspace Integration](docs/integrations/google-workspace.md)

## Security and Compliance

- [Security and Compliance Guide](docs/security/compliance.md) — CIS and Microsoft Security Benchmark compliance

## Development

```bash
git clone https://github.com/thomaselliottbetz/scim-sanity.git
cd scim-sanity
python -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
pytest -v
```

## Contributing

Contributions via Pull Request.

## License

MIT License - see [LICENSE](LICENSE) file.

## References

- [RFC 7643 - SCIM: Core Schema](https://tools.ietf.org/html/rfc7643)
- [RFC 7644 - SCIM: Protocol](https://tools.ietf.org/html/rfc7644)
- [draft-abbey-scim-agent-extension-00](https://datatracker.ietf.org/doc/draft-abbey-scim-agent-extension/)
