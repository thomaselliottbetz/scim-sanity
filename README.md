# scim-sanity

SCIM 2.0 payload validation tool for pre-provisioning validation of User, Group, Agent, and AgenticApplication resources. Includes Ansible action plugin integration, identity provider guides (Entra ID, Google Workspace), and security compliance documentation (CIS and Microsoft Security Benchmarks).

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/thomaselliottbetz/scim-sanity/main.svg)](https://results.pre-commit.ci/latest/github/thomaselliottbetz/scim-sanity/main)

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
pip install -e .
```

## Usage

```bash
scim-sanity [options] [file]
python3 -m scim_sanity [options] [file]
```

### Options

- `<file>` - Path to JSON file containing SCIM resource or PATCH operation
- `--patch` - Validate as SCIM PATCH operation
- `--stdin` - Read JSON from standard input
- `-h, --help` - Show help

### Examples

```bash
# Validate User resource
scim-sanity user.json

# Validate PATCH operation
scim-sanity --patch patch.json

# Validate from stdin
echo '{"schemas":["urn:ietf:params:scim:schemas:core:2.0:User"],"userName":"user@example.com"}' | scim-sanity --stdin

# Validate in CI/CD
scim-sanity payload.json || exit 1

# Validate in Ansible playbook
- name: Validate SCIM payload
  scim_validate:
    payload: "{{ user_payload }}"
    operation: full
  register: validation_result
```

### Exit Codes

- `0` - Validation passed
- `1` - Validation failed or error occurred

## Validation Rules

### Required Attributes
- User: `userName`
- Group: `displayName`
- Agent: `name`
- AgenticApplication: `name`

### Schema Validation
- Validates schema URNs (User, Group, Agent, AgenticApplication, enterprise extension)
- Auto-detects resource type from schema URI
- Rejects unknown or invalid schema URNs

### Mutability
- Flags immutable attributes (`id`, `meta`) being set by client
- Validates read-only attributes are not modified

### PATCH Operations
- Validates operation structure
- Validates `op` values (`add`, `remove`, `replace`)
- Checks for duplicate paths
- Validates required fields per operation type

### Data Semantics
- Rejects `null` values (use PATCH `remove` instead)
- Validates complex attribute structures
- Validates multi-valued attributes are arrays

## Pre-commit Integration

1. Install pre-commit:
   ```bash
   pip install pre-commit
   pre-commit install
   ```

2. Add `.pre-commit-config.yaml`:

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

Ansible action plugin for SCIM validation in playbooks. See [ansible/README.md](ansible/README.md) for documentation.

### Quick Start

1. Install scim-sanity on Ansible control node:
   ```bash
   pip install scim-sanity
   ```

2. Copy action plugin:
   ```bash
   cp ansible/action_plugins/scim_validate.py playbooks/action_plugins/
   ```

3. Use in playbook:
   ```yaml
   - name: Validate SCIM payload
     scim_validate:
       payload: "{{ user_payload }}"
       operation: full
     register: validation_result
   ```

See [ansible/README.md](ansible/README.md) for complete documentation.

## Identity Provider Integration Guides

Integration guides for Microsoft Entra ID and Google Workspace provisioning workflows:

- [Microsoft Entra ID Integration](docs/integrations/entra-id.md) - SCIM validation for Entra ID provisioning
- [Google Workspace Integration](docs/integrations/google-workspace.md) - SCIM validation for Google Workspace provisioning

Includes pre-provisioning validation workflows, CI/CD integration examples, and common SCIM operations.

## Security and Compliance

Compliance documentation referencing CIS and Microsoft Security Benchmarks:

- [Security and Compliance Guide](docs/security/compliance.md) - CIS and Microsoft Security Benchmark compliance

Supports compliance with:
- CIS Microsoft Azure Foundations Benchmark (Section 5: Identity Services)
- CIS Google Workspace Benchmark (Sections 1 and 4)
- Microsoft Cloud Security Benchmark (Identity Management controls)

Includes compliance validation workflows, audit procedures, and reporting examples.

## Examples

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

### Invalid Examples

**Missing required field:**
```json
{
  "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"]
}
```
Error: `Missing required attribute: 'userName'`

**Setting immutable attribute:**
```json
{
  "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
  "userName": "user@example.com",
  "id": "12345"
}
```
Error: `Immutable attribute 'id' should not be set by client`

**Using null value:**
```json
{
  "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
  "userName": "user@example.com",
  "displayName": null
}
```
Error: `Attribute 'displayName' has null value. Use PATCH 'remove' operation to clear attributes instead`

## Error Messages

- **Missing required attribute** - Required field for resource type is missing
- **Immutable attribute** - Attempt to set read-only field (e.g., `id`, `meta`)
- **Null value** - Use of `null` to clear value (use PATCH `remove` instead)
- **Invalid schema** - Unknown or invalid schema URN
- **Invalid structure** - Data does not match expected SCIM structure

## Agent and AgenticApplication Support

Validates Agent and AgenticApplication resources per IETF draft-abbey-scim-agent-extension-00.

### Schema URIs
- Agent: `urn:ietf:params:scim:schemas:core:2.0:Agent`
- AgenticApplication: `urn:ietf:params:scim:schemas:core:2.0:AgenticApplication`

### Validation Rules
- Agent: `name` required, all other attributes optional
- AgenticApplication: `name` required, all other attributes optional
- Validates mutability rules (e.g., `subject`, `owners` are read-only)

## Development

```bash
git clone https://github.com/thomaselliottbetz/scim-sanity.git
cd scim-sanity
python -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
pytest
```

## Contributing

Contributions via Pull Request.

## License

MIT License - see [LICENSE](LICENSE) file.

## References

- [RFC 7643 - SCIM: Core Schema](https://tools.ietf.org/html/rfc7643)
- [RFC 7644 - SCIM: Protocol](https://tools.ietf.org/html/rfc7644)
- [draft-abbey-scim-agent-extension-00](https://datatracker.ietf.org/doc/draft-abbey-scim-agent-extension/)
- [CIS Microsoft Azure Foundations Benchmark](https://downloads.cisecurity.org/#/)
- [CIS Google Workspace Benchmark](https://downloads.cisecurity.org/#/)
- [Microsoft Cloud Security Benchmark](https://github.com/MicrosoftDocs/SecurityBenchmarks)
- [Microsoft Entra ID SCIM Documentation](https://learn.microsoft.com/entra/identity/app-provisioning/use-scim-to-provision-users-and-groups)
- [Google Workspace SCIM API Documentation](https://developers.google.com/admin-sdk/directory/v1/guides/manage-users)
