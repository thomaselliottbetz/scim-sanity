# scim-sanity

> **Catch 95% of SCIM integration bugs before they hit production**

A lightweight, zero-dependency CLI linter for SCIM 2.0 User and Group payloads (RFC 7643/7644).

![demo gif](demo.gif)

Works offline · Pure Python standard library · No external dependencies required.

[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Why scim-sanity?

SCIM (System for Cross-domain Identity Management) integrations are notoriously tricky. Common mistakes like missing required fields, setting immutable attributes, or invalid PATCH operations can cause silent failures or break production systems. **scim-sanity** validates your SCIM payloads locally before they hit your API, catching these issues early.

## Features

✅ **Zero dependencies** - Works with Python standard library only (optional Click for better CLI)  
✅ **SCIM 2.0 compliant** - Validates against RFC 7643 and RFC 7644  
✅ **Comprehensive checks** - Catches 15+ common integration errors  
✅ **Color output** - Beautiful, readable error messages with line numbers  
✅ **PATCH support** - Validates both full resources and PATCH operations  
✅ **Enterprise extension** - Supports enterprise user extension schema  

## Installation

### Using pipx (recommended)

```bash
pipx install scim-sanity
```

### Using pip

```bash
pip install scim-sanity
```

### From source

```bash
git clone https://github.com/thomasbetz/scim-sanity.git
cd scim-sanity
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e .
```

### Verifying Installation

After installation, verify that scim-sanity is working correctly:

**Option 1: Using the command (if installed via pip/pipx or with venv activated)**
```bash
scim-sanity --help
```

**Option 2: Using Python module (works from anywhere)**
```bash
python3 -m scim_sanity --help
```

**Quick test:**
```bash
# Test with a valid user resource
echo '{"schemas":["urn:ietf:params:scim:schemas:core:2.0:User"],"userName":"test@example.com"}' | python3 -m scim_sanity --stdin
# Expected output: ✅ Valid SCIM resource

# Test with an invalid resource (missing userName)
echo '{"schemas":["urn:ietf:params:scim:schemas:core:2.0:User"]}' | python3 -m scim_sanity --stdin
# Expected output: Error about missing userName
```

## Usage

scim-sanity can be run in several ways depending on your installation method:

### Running the Tool

**If installed via pip/pipx or with virtual environment activated:**
```bash
scim-sanity [options] [file]
```

**Using Python module (always works):**
```bash
python3 -m scim_sanity [options] [file]
# or
python -m scim_sanity [options] [file]
```

### Command Options

- `<file>` - Path to a JSON file containing a SCIM resource or PATCH operation
- `--patch` - Validate the input as a SCIM PATCH operation instead of a full resource
- `--stdin` - Read JSON from standard input instead of a file
- `-h, --help` - Show help message and exit

### Basic Usage Examples

#### Validate a SCIM resource file

```bash
# Validate a User resource
scim-sanity user.json

# Validate a Group resource
scim-sanity group.json

# Using Python module
python3 -m scim_sanity user.json
```

#### Validate a PATCH operation

```bash
scim-sanity --patch patch.json

# Using Python module
python3 -m scim_sanity --patch patch.json
```

#### Validate from stdin

```bash
# Validate a User resource from stdin
echo '{"schemas":["urn:ietf:params:scim:schemas:core:2.0:User"],"userName":"user@example.com"}' | scim-sanity --stdin

# Validate a PATCH operation from stdin
echo '{"schemas":["urn:ietf:params:scim:api:messages:2.0:PatchOp"],"Operations":[{"op":"replace","path":"displayName","value":"New Name"}]}' | scim-sanity --stdin --patch

# Pipe from another command
curl -s https://api.example.com/user/123 | scim-sanity --stdin
```

### Common Workflows

#### Pre-commit Validation

Validate SCIM payloads before committing or deploying:

```bash
# Validate all JSON files in a directory
for file in payloads/*.json; do
  echo "Validating $file..."
  scim-sanity "$file" || exit 1
done
```

#### CI/CD Integration

Use in your CI pipeline to catch SCIM errors early:

```bash
# In your CI script
if ! scim-sanity user-payload.json; then
  echo "SCIM validation failed!"
  exit 1
fi
```

#### Testing API Responses

Validate responses from your SCIM API:

```bash
# Test a GET response
curl -s https://api.example.com/scim/v2/Users/123 | scim-sanity --stdin

# Test a POST request body before sending
scim-sanity new-user.json && curl -X POST https://api.example.com/scim/v2/Users -d @new-user.json
```

#### Interactive Development

Quick validation while developing:

```bash
# Validate and see errors immediately
scim-sanity my-payload.json

# If valid, proceed with API call
scim-sanity my-payload.json && curl -X POST ... -d @my-payload.json
```

### Exit Codes

The tool uses standard exit codes for scripting:

- `0` - Validation passed (resource is valid)
- `1` - Validation failed (errors found) or an error occurred

Use exit codes in scripts:

```bash
if scim-sanity payload.json; then
  echo "Payload is valid, proceeding..."
  # Continue with your workflow
else
  echo "Validation failed, stopping..."
  exit 1
fi
```

### Understanding Output

#### Valid Resource

When validation passes, you'll see:

```
✅ Valid SCIM resource
```

or for PATCH operations:

```
✅ Valid PATCH operation
```

#### Invalid Resource

When validation fails, errors are displayed with clear messages:

```
Found 3 error(s):

❌ Missing required attribute: 'userName' (schema: urn:ietf:params:scim:schemas:core:2.0:User) at userName
❌ Immutable attribute 'id' should not be set by client (mutability: readOnly) at id
❌ Attribute 'displayName' has null value. Use PATCH 'remove' operation to clear attributes instead at displayName
```

Each error message includes:
- **Error type** - What went wrong
- **Location** - The attribute path where the error occurred
- **Guidance** - How to fix the issue

#### Error Messages Explained

- **Missing required attribute** - A required field for the resource type is missing
- **Immutable attribute** - You're trying to set a read-only field (like `id` or `meta`)
- **Null value** - Using `null` to clear a value (use PATCH `remove` instead)
- **Invalid schema** - Unknown or invalid schema URN
- **Invalid structure** - Data doesn't match expected SCIM structure (e.g., multi-valued attribute not an array)

## Validation Checks

scim-sanity performs the following checks:

### Required Attributes
- ✅ Ensures `userName` is present for User resources
- ✅ Ensures `displayName` is present for Group resources
- ✅ Validates all required schema attributes

### Schema Validation
- ✅ Validates schema URNs (core User, Group, enterprise extension)
- ✅ Rejects unknown or invalid schema URNs
- ✅ Ensures `schemas` field is present and non-empty

### Mutability Rules
- ✅ Flags immutable attributes (e.g., `id`, `meta`) being set by client
- ✅ Validates read-only attributes are not modified

### PATCH Operations
- ✅ Validates PATCH operation structure
- ✅ Ensures valid `op` values (`add`, `remove`, `replace`)
- ✅ Checks for duplicate paths in operations
- ✅ Validates required fields per operation type

### Data Semantics
- ✅ Rejects `null` values (use PATCH `remove` instead)
- ✅ Validates complex attribute structures
- ✅ Validates multi-valued attributes are arrays

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
    },
    {
      "op": "add",
      "path": "emails",
      "value": [
        {
          "value": "newemail@example.com",
          "type": "work"
        }
      ]
    }
  ]
}
```

### Valid User with Enterprise Extension

```json
{
  "schemas": [
    "urn:ietf:params:scim:schemas:core:2.0:User",
    "urn:ietf:params:scim:schemas:extension:enterprise:2.0:User"
  ],
  "userName": "manager@example.com",
  "name": {
    "givenName": "Jane",
    "familyName": "Manager"
  },
  "urn:ietf:params:scim:schemas:extension:enterprise:2.0:User": {
    "employeeNumber": "EMP-001",
    "department": "Engineering",
    "manager": {
      "value": "ceo-id",
      "displayName": "CEO"
    }
  }
}
```

### Invalid Examples (Common Mistakes)

#### Missing Required Field

```json
{
  "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"]
  // Missing userName - will fail validation
}
```

**Error:** `❌ Missing required attribute: 'userName'`

#### Setting Immutable Attribute

```json
{
  "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
  "userName": "user@example.com",
  "id": "12345"  // ❌ Cannot set id - it's read-only
}
```

**Error:** `❌ Immutable attribute 'id' should not be set by client`

#### Using Null Values

```json
{
  "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
  "userName": "user@example.com",
  "displayName": null  // ❌ Use PATCH remove instead
}
```

**Error:** `❌ Attribute 'displayName' has null value. Use PATCH 'remove' operation to clear attributes instead`

#### Invalid Multi-valued Attribute

```json
{
  "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
  "userName": "user@example.com",
  "emails": "not-an-array"  // ❌ emails must be an array
}
```

**Error:** `❌ Multi-valued attribute 'emails' must be an array`

### Troubleshooting

#### Command not found

If you get `command not found: scim-sanity`:

1. **Check if virtual environment is activated** (if installed from source):
   ```bash
   source venv/bin/activate  # or .venv/bin/activate
   ```

2. **Use Python module instead**:
   ```bash
   python3 -m scim_sanity --help
   ```

3. **Verify installation**:
   ```bash
   pip show scim-sanity  # Should show package info
   ```

#### File not found errors

Make sure you're providing the correct path:
```bash
# Use absolute or relative paths
scim-sanity ./path/to/file.json
scim-sanity /absolute/path/to/file.json
```

#### JSON parsing errors

If you see "Invalid JSON" errors:
- Verify your file is valid JSON (use `jq` or an online JSON validator)
- Check for trailing commas or syntax errors
- Ensure the file encoding is UTF-8

#### Validation passes but API still rejects

scim-sanity validates SCIM 2.0 compliance, but your API might have:
- Additional custom validation rules
- Different schema extensions
- Server-specific requirements

Always test with your actual API endpoint as well.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Development

```bash
# Clone the repository
git clone https://github.com/thomasbetz/scim-sanity.git
cd scim-sanity

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run linter (if configured)
# flake8 scim_sanity tests
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## References

- [RFC 7643 - SCIM: Core Schema](https://tools.ietf.org/html/rfc7643)
- [RFC 7644 - SCIM: Protocol](https://tools.ietf.org/html/rfc7644)
