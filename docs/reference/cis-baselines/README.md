# CIS Benchmark Reference Materials

This directory contains excerpted sections from CIS Benchmarks for reference purposes.

## Contents

### Azure Foundation Benchmark
- `azure-foundations-section-1-introduction.txt` - Section 1: Introduction (overview and methodology)
- `azure-foundations-section-5.1-5.3-identity-services.txt` - Sections 5.1-5.3: Identity Services (Security Defaults, Conditional Access, Periodic Identity Reviews)

### Google Workspace Benchmark
- `google-workspace-section-1-directory.txt` - Section 1: Directory (Users and Directory Settings - most relevant for SCIM validation)
- `google-workspace-section-4-security.txt` - Section 4: Security (Authentication and Access Control)

## Important Notes

⚠️ **These files are excluded from git** - CIS Benchmarks cannot be hosted in public repositories.

These reference materials are for local development and documentation purposes only. They should not be committed to version control.

## Usage

These excerpts are used to:
- Understand relevant CIS controls for identity management
- Create documentation that references CIS controls
- Develop compliance validation examples
- Support security automation workflows

## Official Sources

For the complete, official CIS Benchmarks, visit:
- [CIS Benchmarks Downloads](https://downloads.cisecurity.org/#/)

## Adding New References

When adding new benchmark excerpts:
1. Extract only the relevant sections (e.g., Section 5 for Identity Services)
2. Save as `.txt` or `.md` files
3. Do NOT commit these files to git (they're in .gitignore)
4. Update this README to document what's included

