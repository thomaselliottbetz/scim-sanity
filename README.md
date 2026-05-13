# scim-sanity

**SCIM 2.0 conformance testing and payload validation** — from the terminal, a browser, or your own tooling.

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/thomaselliottbetz/scim-sanity/main.svg)](https://results.pre-commit.ci/latest/github/thomaselliottbetz/scim-sanity/main)

scim-sanity tests SCIM 2.0 server conformance. Point the probe at a live server and get a prioritized list of RFC 7643/7644 violations with fix guidance. Lint payloads statically without a live server. Named server profiles (starting with Microsoft Entra ID) handle the non-RFC fields real servers require so the probe can reach the interesting conformance tests rather than stopping at resource creation.

## Three ways to use it


|              | CLI                              | Web GUI                                    | REST API                                       |
| ------------ | -------------------------------- | ------------------------------------------ | ---------------------------------------------- |
| **Best for** | Probing servers and linting payloads | Interactive exploration and demos | Embedding validation in your own tooling |
| **Requires** | `pip install scim-sanity`        | `pip install 'scim-sanity[web]'`           | `pip install 'scim-sanity[web]'`               |
| **Start**    | `scim-sanity probe <url> ...`    | `scim-sanity web`                          | `scim-sanity web`                              |


Quick reference for targeting a known server:

```bash
scim-sanity profiles              # list servers with built-in profiles
scim-sanity profiles entra        # show Entra deviations, required fields, recommended command
```

---

## Installation

Core CLI (validate and probe, no additional dependencies beyond Click):

```bash
pip install scim-sanity
```

With the optional web GUI and REST API:

```bash
pip install 'scim-sanity[web]'
```

From source:

```bash
git clone https://github.com/thomaselliottbetz/scim-sanity.git
cd scim-sanity
python -m venv venv
source venv/bin/activate
pip install -e ".[web,dev]"
```

---

## Web GUI

scim-sanity includes an optional browser-based interface built with React and the [AWS Cloudscape Design System](https://cloudscape.design/). Install with `pip install 'scim-sanity[web]'`, then:

```bash
scim-sanity web
```

Open **[http://127.0.0.1:8000](http://127.0.0.1:8000)** in your browser. Options:

```bash
scim-sanity web --port 8080 --host 0.0.0.0
```

### Pages


| Page         | Path        | Description                                                                                                                                                                    |
| ------------ | ----------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Validate** | `/validate` | Paste or load a SCIM JSON payload and validate it against RFC 7643/7644 rules. Supports full resources and PATCH operations. Load any example from the built-in library.       |
| **Probe**    | `/probe`    | Configure and run a live server conformance probe. Results are grouped by test phase with status indicators and a prioritized Fix Summary when failures are present.           |
| **Examples** | `/examples` | Browse 16 curated RFC example payloads. Filter by resource type (User, Group, Agent, AgenticApplication, PATCH) or validity. Load any example directly into the Validate page. |


---

## REST API

When `scim-sanity web` is running, the same engine that powers the CLI and GUI is also available as a REST API at `http://127.0.0.1:8000`. This is for teams who want to embed SCIM validation or conformance testing into their own tooling — custom CI pipelines, internal dashboards, test frameworks, deployment gates — without shelling out to the CLI.

### Interactive documentation

Three documentation interfaces are served automatically:

- **[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)** — Swagger UI. Lists all endpoints, shows request and response schemas, and lets you execute live calls directly from the browser. Paste a payload into `/api/validate` and run it, or fire a probe at a real server, without writing any code. The fastest way to understand what the API does and verify it works against your environment.
- **[http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)** — ReDoc. A clean, single-page reference layout presenting the same schema information in a format better suited to reading than experimenting. Useful when you want to understand the full response structure before integrating.
- **[http://127.0.0.1:8000/openapi.json](http://127.0.0.1:8000/openapi.json)** — The raw OpenAPI 3.1 specification. Download this to import the API into Postman or Insomnia, generate a typed client in any language, or integrate scim-sanity into API gateways and toolchains that consume OpenAPI specs. The schema is stable within major versions.

Swagger UI — three endpoints, no internal routes exposed

*Swagger UI (`/docs`) — all three endpoints with schemas and a live "Try it out" button.*

ReDoc — Probe endpoint with full schema and response sample

*ReDoc (`/redoc`) — typed schema fields, defaults, and a real probe response sample side by side.*

### Endpoints

#### `GET /api/examples`

Returns the full catalog of curated example payloads.

```bash
curl http://127.0.0.1:8000/api/examples
```

```json
[
  {
    "id": "valid-user-minimal",
    "name": "Minimal valid User",
    "description": "Smallest valid User payload — only the required userName attribute.",
    "resource_type": "User",
    "valid": true,
    "payload": {
      "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
      "userName": "john.doe@example.com"
    }
  }
]
```

#### `POST /api/validate`

Validates a SCIM payload. Auto-detects resource type from schema URNs.

```bash
curl -X POST http://127.0.0.1:8000/api/validate \
  -H "Content-Type: application/json" \
  -d '{
    "payload": {
      "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
      "id": "123",
      "name": {"givenName": "John"}
    },
    "patch": false
  }'
```

```json
{
  "valid": false,
  "errors": [
    {
      "message": "Missing required attribute: 'userName'",
      "path": "userName",
      "schema": "urn:ietf:params:scim:schemas:core:2.0:User"
    },
    {
      "message": "Immutable attribute 'id' should not be set by client",
      "path": "id",
      "schema": "urn:ietf:params:scim:schemas:core:2.0:User"
    }
  ]
}
```

Set `"patch": true` to validate a PATCH operation body instead of a full resource.

#### `POST /api/probe`

Runs the full conformance probe against a live SCIM server. Returns structured results identical to the `--json-output` CLI flag.

```bash
curl -X POST http://127.0.0.1:8000/api/probe \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com/scim/v2",
    "token": "your-bearer-token",
    "mode": "strict",
    "i_accept_side_effects": true
  }'
```

```json
{
  "scim_sanity_version": "0.7.0",
  "mode": "strict",
  "timestamp": "2026-02-24 09:15:00",
  "summary": {
    "total": 32,
    "passed": 30,
    "failed": 1,
    "warnings": 1,
    "skipped": 0,
    "errors": 0
  },
  "issues": [
    {
      "priority": "P1",
      "title": "Wrong Content-Type on SCIM responses",
      "fix": "Set Content-Type: application/scim+json on all responses served from /scim/v2/",
      "rationale": "Compliant clients inspect Content-Type before parsing — every response is rejected regardless of whether the body is otherwise correct.",
      "affected_tests": 1
    }
  ],
  "results": [
    {
      "name": "GET /ServiceProviderConfig",
      "status": "fail",
      "message": "Content-Type should be application/scim+json, got 'application/json'",
      "phase": "Phase 1 — Discovery"
    }
  ]
}
```

Full probe request parameters:


| Parameter               | Type       | Description                                                                          |
| ----------------------- | ---------- | ------------------------------------------------------------------------------------ |
| `url`                   | string     | SCIM base URL (required)                                                             |
| `token`                 | string     | Bearer token for authentication                                                      |
| `username` / `password` | string     | Basic auth credentials                                                               |
| `mode`                  | `"strict"` | `"compat"`                                                                           |
| `resource`              | string     | Limit to one resource type: `User`, `Group`, `Agent`, `AgenticApplication`           |
| `i_accept_side_effects` | boolean    | **Required `true`.** Acknowledges that the probe creates and deletes real resources. |
| `tls_no_verify`         | boolean    | Skip TLS certificate verification                                                    |
| `skip_cleanup`          | boolean    | Leave test resources on the server after the run                                     |
| `timeout`               | integer    | Per-request timeout in seconds (default: 30)                                         |
| `proxy`                 | string     | HTTP/HTTPS proxy URL                                                                 |
| `ca_bundle`             | string     | Path to custom CA certificate bundle                                                 |
| `profile`               | string     | Named server profile (e.g. `"entra"`) — injects required non-RFC payload fields      |
| `extra_user_fields`     | object     | Extra fields merged into user creation payloads                                      |
| `user_domain`           | string     | Domain for generated `userName` values (e.g. `"tenant.onmicrosoft.com"`)             |


### Stability

The REST API response schema is treated as a public interface and is stable within major versions.

---

## Server Conformance Probe

Test a live SCIM server for RFC 7643/7644 conformance. The probe **creates, modifies, and deletes real resources** on the target server, then cleans up after itself.

⚠️ Warning: This tool performs destructive operations. Do not run against production tenants without explicit authorization.

### Server Profiles

Some SCIM servers require non-RFC payload fields that would cause failures without extra configuration. Profiles inject these fields automatically so the probe can reach the interesting conformance tests rather than stopping at user creation.

```bash
# List available profiles
scim-sanity profiles

# Show full details for a profile: required fields, known deviations, recommended command
scim-sanity profiles entra
```

Available profiles:


| Profile              | Server                         | What it injects                                                                                                                                                          |
| -------------------- | ------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `entra`              | Microsoft Entra ID SCIM server | `password`, `mailNickname`, enterprise + Microsoft Entra extension schemas for Users; `mailEnabled`, `mailNickname`, `securityEnabled`, Entra Group extension for Groups |
| `fortiauthenticator` | FortiAuthenticator SCIM server | None — use `--compat` for response-envelope deviations (e.g. Content-Type, missing meta timestamps)                                                                      |


Use `--profile` with `--compat` for the most useful output against known non-conformant servers — profiles handle the request side, compat mode handles the response side:

Note: FortiAuthenticator deployments may use basic auth; use `--username/--password` instead of `--token` when applicable.

```bash
# Microsoft Entra ID
scim-sanity probe https://graph.microsoft.com/rp/scim \
  --token <bearer-token> \
  --profile entra \
  --user-domain <tenant>.onmicrosoft.com \
  --compat \
  --i-accept-side-effects
```

`--extra-user-fields` lets you inject arbitrary fields without a named profile:

```bash
scim-sanity probe <url> --token <token> \
  --extra-user-fields '{"password":"Str0ng!Pass"}' \
  --i-accept-side-effects
```

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


| Option                      | Description                                                                                                                                                                                                                          |
| --------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `--token`                   | Bearer token for authentication                                                                                                                                                                                                      |
| `--username` / `--password` | Basic auth credentials                                                                                                                                                                                                               |
| `--i-accept-side-effects`   | **Required.** Acknowledge that the probe creates/deletes resources                                                                                                                                                                   |
| `--strict` / `--compat`     | Strict (default) or compat validation mode                                                                                                                                                                                           |
| `--json-output`             | Output results as JSON                                                                                                                                                                                                               |
| `--resource`                | Test a specific resource type (User, Group, Agent, AgenticApplication)                                                                                                                                                               |
| `--skip-cleanup`            | Leave test resources on the server                                                                                                                                                                                                   |
| `--tls-no-verify`           | Skip TLS certificate verification                                                                                                                                                                                                    |
| `--timeout`                 | Per-request timeout in seconds (default: 30)                                                                                                                                                                                         |
| `--proxy`                   | HTTP/HTTPS proxy URL. scim-sanity does not inherit `HTTPS_PROXY`/`HTTP_PROXY` env vars — pass this flag explicitly if your target requires a proxy. Most users probing a local or staging server do not need this.                   |
| `--ca-bundle`               | Path to custom CA certificate bundle. Most users can use `--tls-no-verify` instead during development. For container deployments, `REQUESTS_CA_BUNDLE` and `SSL_CERT_FILE` env vars are also honoured by the underlying HTTP client. |
| `--profile`                 | Named server profile (e.g. `entra`) — injects required non-RFC fields                                                                                                                                                                |
| `--extra-user-fields`       | Extra JSON fields merged into user creation payloads                                                                                                                                                                                 |
| `--user-domain`             | Domain for generated `userName` values (e.g. `tenant.onmicrosoft.com`)                                                                                                                                                               |


### Safety Guardrails

The probe implements several safety measures to prevent accidental damage:

- **Explicit consent** — Refuses to run without `--i-accept-side-effects`.
- **Namespace isolation** — All test resources are prefixed with `scim-sanity-test-` to avoid collisions with real data.
- **Resource caps** — Hard limit of 10 agents in rapid lifecycle tests.
- **429 retry** — Automatically retries on 429 Too Many Requests, honoring `Retry-After` headers (max 3 retries).
- **500 transience detection** — When a POST returns 500, the probe retries once after a brief delay using the same request headers. If the retry succeeds, the result is recorded as a warning ("transient instability") and the CRUD lifecycle continues with the resource created by the retry. If both attempts fail, content-type rejection diagnosis runs before reporting the final failure.
- **Timeouts** — Per-request timeouts prevent hung runs.
- **Cleanup** — Deletes all created test resources in reverse order (groups before users). Skippable with `--skip-cleanup`.
- **Failure semantics** — If the process is interrupted, partial cleanup may occur; orphaned test resources are possible and should be removed manually.
- **Secret redaction** — Authorization headers are redacted in any JSON output or logs.

### Test Sequence

The probe runs 7 phases. Each phase tests specific RFC clauses against real HTTP traffic — no mocking.

1. **Discovery** (RFC 7644 §4)
  - GET `/ServiceProviderConfig`, `/Schemas`, `/ResourceTypes`
  - Asserts: HTTP 200, `Content-Type: application/scim+json`, parseable JSON body
  - A server that omits these endpoints forces clients to hardcode assumptions about server capabilities
2. **User CRUD Lifecycle** (RFC 7644 §3.3, §3.4.1, §3.5.1, §3.6; RFC 7643 §4.1)
  - POST → asserts 201, `Content-Type: application/scim+json`, `Location` header, `id`, `meta.created`, `meta.lastModified`
  - GET by id → asserts 200, same Content-Type and meta fields
  - PUT → asserts 200, same Content-Type and meta fields
  - GET after PUT → asserts the updated field value persisted
  - PATCH `active=false` → asserts 200 or 204
  - GET after PATCH → asserts `active` is `false`
  - DELETE → asserts 204 No Content (RFC 7644 §3.6)
  - GET after DELETE → asserts 404
3. **Group CRUD Lifecycle** (RFC 7644 §3.3; RFC 7643 §4.2)
  - Same sequence as User
  - Additional PATCH: add a member, then remove all members — asserts 200 each
4. **Agent CRUD Lifecycle** (draft-abbey-scim-agent-extension-00)
  - Same sequence as User
  - Skipped if server does not advertise Agent support in `/ResourceTypes`
5. **AgenticApplication CRUD Lifecycle** (draft-abbey-scim-agent-extension-00)
  - Same sequence as User
  - Skipped if server does not advertise AgenticApplication support

5a. **Agent Rapid Lifecycle** (draft-abbey-scim-agent-extension-00)

- Create and immediately delete multiple agents (default 10) to test ephemeral provisioning at machine speed
- Skipped if server does not support Agents

1. **Search** (RFC 7644 §3.4.2, §8.1)
  - GET `/Users` → asserts ListResponse envelope (`schemas`, `totalResults`, `Resources`), `Content-Type: application/scim+json`
  - GET `/Users?filter=...` → asserts 200 (or 400 if partial filter support)
  - GET `/Users?startIndex=1&count=1` → asserts pagination parameters honored
  - GET `/Users?count=0` → asserts `totalResults` present with empty `Resources`
2. **Error Handling** (RFC 7644 §3.12)
  - GET nonexistent resource → asserts 404 with SCIM error schema (`schemas`, `status`)
  - POST invalid JSON body → asserts 400 with SCIM error schema
  - POST missing required field (`userName`) → asserts 400 with SCIM error schema

### Strict vs Compat Mode

**Strict mode** (`--strict`, default) treats all RFC deviations as failures.

**Compat mode** (`--compat`) applies a curated **Deviation Policy**: known, widespread ecosystem deviations are downgraded to warnings instead of failures. This list is intentional and versioned.

> **Compat mode and profiles are complementary, not alternatives.** Compat mode governs how scim-sanity interprets *responses* — it tolerates known deviations in what the server sends back. Profiles govern what scim-sanity *sends* — they inject non-RFC fields required to successfully create resources on servers with non-standard requirements. For known non-conformant servers like Entra, use both together: `--profile entra --compat`.

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

### Fix Summary

When failures are present, the probe appends a prioritized **Fix Summary** after the results. Each entry has three lines:

```
  [P1] Trouble: Wrong Content-Type on SCIM responses (12 tests affected)
       Fix: Set Content-Type: application/scim+json on all responses served from /scim/v2/
       Rationale: Compliant clients inspect Content-Type before parsing — every response
                  is rejected regardless of whether the body is otherwise correct.
```

Issues use a two-tier naming scheme: `P`-prefixed entries (P1–P5) are general RFC conformance issues applicable to any SCIM server; `E`-prefixed entries (E1, E2, …) are named deviations specific to a known server, surfaced when a profile is active. `E1b` and similar suffixes denote cascade effects of a parent deviation. Issues are ordered by severity (P1 most critical). The fix summary is omitted when all tests pass. In JSON output mode, the same information is available as an `issues` array. Priority rankings are debatable — feedback and dispute are welcome.

### JSON Output (Stable Interface)

```bash
scim-sanity probe <url> --token <token> --json-output --i-accept-side-effects
```

```json
{
  "scim_sanity_version": "0.7.0",
  "mode": "strict",
  "timestamp": "2026-02-24 09:15:00",
  "summary": {
    "total": 32,
    "passed": 14,
    "failed": 15,
    "warnings": 0,
    "skipped": 3,
    "errors": 0
  },
  "issues": [
    {
      "priority": "P1",
      "title": "Wrong Content-Type on SCIM responses",
      "rationale": "Compliant clients inspect Content-Type before parsing — every response is rejected regardless of whether the body is otherwise correct.",
      "fix": "Set Content-Type: application/scim+json on all responses served from /scim/v2/",
      "affected_tests": 12
    }
  ],
  "results": [
    {
      "name": "GET /ServiceProviderConfig",
      "status": "fail",
      "message": "Content-Type should be application/scim+json, got 'text/html; charset=utf-8'",
      "phase": "Phase 1 — Discovery"
    }
  ]
}
```

---

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

### What the linter catches

Given a payload with a missing required field and a client-set immutable attribute:

```json
{
  "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
  "id": "123",
  "name": {"givenName": "John"}
}
```

```
Found 3 error(s):

❌ Missing required attribute: 'userName' (schema: urn:ietf:params:scim:schemas:core:2.0:User) at userName
❌ User resource missing required attribute: 'userName'
❌ Immutable attribute 'id' should not be set by client (mutability: readOnly) at id
```

### Minimal valid examples

**User**

```json
{
  "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
  "userName": "john.doe@example.com"
}
```

**Group**

```json
{
  "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Group"],
  "displayName": "Engineering Team"
}
```

**Agent**

```json
{
  "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Agent"],
  "name": "automation-agent"
}
```

**PATCH operation**

```json
{
  "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
  "Operations": [{"op": "replace", "path": "displayName", "value": "New Name"}]
}
```

---

## Integrations

---

## Identity Provider Guides

- [Microsoft Entra ID Integration](docs/integrations/entra-id.md) — includes Entra as SCIM server (new in 0.7.0), known deviations, and `--profile entra` usage
- [Google Workspace Integration](docs/integrations/google-workspace.md)

## Security and Compliance

- [Security and Compliance Guide](docs/security/compliance.md)

---

## Development

```bash
git clone https://github.com/thomaselliottbetz/scim-sanity.git
cd scim-sanity
python -m venv venv
source venv/bin/activate
pip install -e ".[web,dev]"
pytest -v
```

### Web GUI development

Two processes run during development:

```bash
# Terminal 1 — Python API (auto-reloads on source changes)
pip install -e ".[web]"
uvicorn scim_sanity.api:app --reload --port 8000

# Terminal 2 — Vite dev server with hot reload
cd web
npm install
npm run dev          # http://localhost:5173, proxies /api/* to :8000
```

To build the frontend for production:

```bash
cd web
npm run build        # outputs to web/dist/
```

The built static files are served automatically by `scim-sanity web` — no separate frontend process needed.

---

## Planned Improvements

**PATCH filter expression testing** (RFC 7644 §3.5.2) — The probe currently tests simple PATCH paths (`active`, `members`). Complex filter-based paths such as `emails[type eq "work"].value` are a known interop pain point and are not yet covered.

**Phase 1 schema content validation** — Discovery endpoint tests currently verify HTTP 200 and correct Content-Type but do not validate that the returned schema bodies are well-formed or consistent with the resources the server actually implements.

**Phase 6 resource body validation** — The search phase validates the ListResponse envelope structure but does not inspect individual resources within the `Resources` array. A server returning well-formed envelopes with non-conformant resource bodies would currently pass.

**GitHub Action** — A ready-to-use GitHub Action for linting SCIM payload files in CI/CD pipelines without requiring a local Python environment.

**Docker image** — A zero-setup container image for running the probe against any reachable SCIM endpoint without installing Python or pip.

---

## Related Projects

**[entra-google-security-bridge](https://github.com/thomaselliottbetz/entra-google-security-bridge)** — Post-provisioning security monitoring and attribute synchronization for hybrid Microsoft Entra ID + Google Workspace environments. Covers what scim-sanity doesn't: once provisioning is verified as spec-compliant, this tool handles ongoing risky sign-in detection, guest user auditing, OAuth token scanning, and OU synchronization driven by Entra ID attribute changes.

## Contributing

Contributions via Pull Request.

## License

MIT License - see [LICENSE](LICENSE) file.

## References

- [RFC 7643 - SCIM: Core Schema](https://tools.ietf.org/html/rfc7643)
- [RFC 7644 - SCIM: Protocol](https://tools.ietf.org/html/rfc7644)
- [draft-abbey-scim-agent-extension-00](https://datatracker.ietf.org/doc/draft-abbey-scim-agent-extension/)

