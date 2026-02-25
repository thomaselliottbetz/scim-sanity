# Ansible Integration for scim-sanity

This directory contains Ansible integration for validating SCIM 2.0 payloads using scim-sanity.

## Overview

The Ansible Action Plugin allows you to validate SCIM resources directly in your Ansible playbooks, ensuring that SCIM payloads are correct before they reach a SCIM server. Supports User, Group, Agent, and AgenticApplication resource types.

## Installation

### Prerequisites

1. **Install scim-sanity** on the Ansible control node:
   ```bash
   pip install scim-sanity
   ```

2. **Copy the action plugin** to your Ansible action plugins directory:
   ```bash
   # Option 1: Use in a specific playbook directory
   mkdir -p playbooks/action_plugins
   cp ansible/action_plugins/scim_validate.py playbooks/action_plugins/
   
   # Option 2: Install system-wide (requires Ansible configuration)
   # Copy to your Ansible action_plugins directory (check ansible.cfg for location)
   ```

3. **Verify installation**:
   ```bash
   ansible-playbook --version
   python -c "import scim_sanity; print('scim-sanity installed')"
   ```

## Usage

### Basic Example

```yaml
- name: Validate SCIM user payload
  scim_validate:
    payload: "{{ user_payload }}"
    operation: full
  register: validation_result

- name: Fail if validation fails
  fail:
    msg: "SCIM validation failed"
  when: not validation_result.valid
```

### Parameters

- **`payload`** (dict or string, optional): SCIM payload as a dictionary or JSON string
- **`file`** (string, optional): Path to a JSON file containing SCIM payload
- **`operation`** (string, optional): Validation operation type
  - `full` (default): Validate a full SCIM resource (POST/PUT)
  - `patch`: Validate a SCIM PATCH operation
- **`fail_on_error`** (boolean, optional): Whether to fail the task if validation fails (default: `true`)

**Note:** Either `payload` or `file` must be provided, but not both.

### Return Values

- **`valid`** (boolean): Whether the SCIM payload is valid
- **`errors`** (list): List of validation errors (if any)
  - Each error contains:
    - `message`: Error message
    - `path`: Attribute path where error occurred
    - `line`: Line number (if available)
- **`msg`** (string): Human-readable message about validation result

### Examples

#### Validate from Variable

```yaml
- name: Validate user payload
  scim_validate:
    payload:
      schemas:
        - "urn:ietf:params:scim:schemas:core:2.0:User"
      userName: "user@example.com"
    operation: full
  register: result
```

#### Validate from File

```yaml
- name: Validate SCIM payload from file
  scim_validate:
    file: "/path/to/user-payload.json"
    operation: full
  register: result
```

#### Validate PATCH Operation

```yaml
- name: Validate PATCH operation
  scim_validate:
    payload: "{{ patch_payload }}"
    operation: patch
  register: result
```

#### Non-Failing Validation

```yaml
- name: Validate but don't fail
  scim_validate:
    payload: "{{ user_payload }}"
    operation: full
    fail_on_error: false
  register: result

- name: Handle validation result
  debug:
    msg: "Validation {{ 'passed' if result.valid else 'failed' }}"
```

#### Conditional Workflow

```yaml
- name: Validate before provisioning
  scim_validate:
    payload: "{{ user_payload }}"
    operation: full
  register: validation

- name: Provision user if valid
  uri:
    url: "https://api.example.com/scim/v2/Users"
    method: POST
    body: "{{ user_payload | to_json }}"
  when: validation.valid

- name: Report validation errors
  debug:
    var: validation.errors
  when: not validation.valid
```

## Integration with Identity Providers

Identity providers such as Microsoft Entra ID and Google Workspace act as SCIM clients — they push provisioning data to your application's SCIM server. Use the linter to validate payloads your SCIM server will handle, and the probe to verify your server is ready to receive them.

See the [Entra ID](../docs/integrations/entra-id.md) and [Google Workspace](../docs/integrations/google-workspace.md) integration guides for IdP-specific payload examples and architecture details.

## Server Conformance Probe

scim-sanity also includes a `probe` subcommand that tests live SCIM servers for RFC 7643/7644 conformance. You can run it from Ansible using the `command` module:

```yaml
- name: Probe SCIM server for conformance
  command: >
    scim-sanity probe {{ scim_endpoint }}
    --token {{ scim_token }}
    --json-output
    --i-accept-side-effects
  register: probe_result

- name: Parse probe results
  set_fact:
    probe_report: "{{ probe_result.stdout | from_json }}"

- name: Fail if probe detected conformance issues
  fail:
    msg: "SCIM server has {{ probe_report.summary.failed }} conformance failures"
  when: probe_report.summary.failed > 0
```

The probe creates, modifies, and deletes real test resources on the target server. The `--i-accept-side-effects` flag is required. See the main [scim-sanity documentation](../README.md) for full probe options.

## Error Handling

The plugin returns detailed error information:

```yaml
- name: Validate and handle errors
  scim_validate:
    payload: "{{ user_payload }}"
    operation: full
    fail_on_error: false
  register: validation

- name: Display errors
  debug:
    msg: "Error at {{ item.path }}: {{ item.message }}"
  loop: "{{ validation.errors }}"
  when: not validation.valid
```

## Best Practices

1. **Validate before provisioning**: Always validate SCIM payloads before they reach a SCIM server
2. **Use in CI/CD**: Integrate validation into your deployment pipelines
3. **Fail fast**: Use `fail_on_error: true` (default) to catch issues early
4. **Store valid payloads**: Only proceed with provisioning if validation passes
5. **Log validation results**: Register results and use them for reporting

## Troubleshooting

### "scim-sanity is not installed"

Install scim-sanity on the Ansible control node:
```bash
pip install scim-sanity
```

### "Cannot find action plugin"

Ensure the action plugin is in the correct location:
- For playbook-specific: `playbooks/action_plugins/scim_validate.py`
- For system-wide: Check `ansible.cfg` for `action_plugins` path

### Validation always fails

Check that:
- Payload is valid JSON
- Required SCIM attributes are present
- Schema URIs are correct
- Operation type matches payload type

## See Also

- [scim-sanity Documentation](../README.md)
- [Ansible Action Plugins Documentation](https://docs.ansible.com/ansible/latest/dev_guide/developing_plugins.html#action-plugins)
- [SCIM 2.0 Specification](https://tools.ietf.org/html/rfc7643)

