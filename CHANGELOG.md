# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
