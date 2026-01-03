# Microsoft Security Benchmarks Reference Materials

This directory contains Microsoft Azure Security Benchmark files for reference purposes.

## Contents

### Identity Management
- `trusted-hardware-identity-management-azure-security-benchmark-v3-latest-security-baseline.xlsx` - Identity management controls

### Resource Management
- `azure-resource-manager-azure-security-benchmark-v3-latest-security-baseline.xlsx` - RBAC and access controls
- `azure-policy-azure-security-benchmark-v3-latest-security-baseline.xlsx` - Policy governance

## Important Notes

⚠️ **These files are excluded from git** - Reference materials only.

These files are for local development and documentation purposes only. They should not be committed to version control.

## Usage

These reference materials are used to:
- Understand Microsoft security controls for identity management
- Create documentation that references Microsoft controls
- Develop compliance validation examples
- Support security automation workflows

## Official Sources

For the complete, official Microsoft Security Benchmarks, visit:
- [Microsoft Security Benchmarks GitHub](https://github.com/MicrosoftDocs/SecurityBenchmarks)
- [Microsoft Cloud Security Benchmark Documentation](https://docs.microsoft.com/azure/security/benchmarks/)

## Adding New References

When adding new benchmark files:
1. Place `.xlsx` files in this directory
2. Convert to `.csv` or `.txt` if needed for easier reference
3. Do NOT commit these files to git (they're in .gitignore)
4. Update this README to document what's included

