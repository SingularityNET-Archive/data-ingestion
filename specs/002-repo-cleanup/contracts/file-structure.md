# File Structure Contract

**Date**: 2025-01-27  
**Feature**: 002-repo-cleanup

## Overview

This contract defines the expected repository file structure after reorganization. All files must conform to this structure, and any deviations must be documented and justified.

---

## Root Directory Structure

### Required Files (Root Only)

| File | Purpose | Required | Notes |
|------|---------|----------|-------|
| `README.md` | Project overview and documentation index | Yes | Must reference new `docs/` structure |
| `CHANGELOG.md` | Version history and change log | Yes | Must document reorganization |
| `pyproject.toml` | Python project configuration | Yes | Standard Python project file |
| `requirements.txt` | Python dependencies | Yes | Standard Python project file |
| `.gitignore` | Git ignore patterns | Yes | Must include `*.log` pattern |

### Required Directories (Root Only)

| Directory | Purpose | Required | Contents |
|-----------|---------|----------|----------|
| `src/` | Application source code | Yes | Python modules organized by concern |
| `tests/` | Test suite | Yes | Tests organized by type (unit/integration/contract) |
| `scripts/` | Utility scripts | Yes | All standalone Python scripts |
| `docs/` | Documentation | Yes | All project documentation |
| `specs/` | Feature specifications | Yes | Feature specs and implementation plans |

### Prohibited in Root

- ❌ Log files (`.log` files)
- ❌ Standalone Python scripts (`.py` files)
- ❌ Documentation files (`.md` files except README.md, CHANGELOG.md)
- ❌ Analysis files (`.json` analysis files)
- ❌ Temporary files

---

## Source Code Structure (`src/`)

### Required Structure

```
src/
├── __init__.py
├── models/          # Data models and schemas
├── services/        # Business logic
├── db/              # Database utilities
├── cli/             # Command-line interface
└── lib/             # Shared utilities
```

### Validation Rules

- All Python modules organized by concern
- No standalone scripts in `src/`
- Consistent naming: snake_case for modules
- Each directory must have `__init__.py`

---

## Test Structure (`tests/`)

### Required Structure

```
tests/
├── __init__.py
├── README.md        # Test documentation with examples
├── conftest.py      # Pytest configuration
├── unit/            # Unit tests
├── integration/     # Integration tests
└── contract/        # Contract tests
```

### Validation Rules

- Tests organized by type (unit/integration/contract)
- Test files follow naming: `test_*.py`
- `tests/README.md` includes example results and expected outcomes

---

## Scripts Structure (`scripts/`)

### Required Structure

```
scripts/
├── check_duplicates.py
├── find_missing_meetings.py
├── run_migration.py
├── verify_schema.py
├── check_constraints_and_duplicates.py
├── setup_db.sh
├── setup_db.sql
└── find_duplicates.sql
```

### Validation Rules

- All standalone Python scripts in `scripts/`
- Scripts have descriptive names
- Scripts are executable
- Database setup files in `scripts/`

---

## Documentation Structure (`docs/`)

### Required Structure

```
docs/
├── README.md                    # Documentation index
├── operations/
│   ├── runbook.md
│   ├── production-checklist.md
│   ├── troubleshooting.md
│   └── duplicate-diagnosis.md
├── deployment/
│   ├── supabase-setup.md
│   ├── supabase-quickstart.md
│   └── deployment-options.md
└── archive/
    └── data-structure-analysis.json
```

### Validation Rules

- All documentation in `docs/` directory
- Logical subdirectories (operations/, deployment/, archive/)
- Files use kebab-case naming
- `docs/README.md` serves as navigation index
- All cross-references updated to new paths

---

## File Naming Conventions

### Documentation Files
- **Format**: kebab-case
- **Extension**: `.md`
- **Examples**: `production-checklist.md`, `supabase-setup.md`

### Python Scripts
- **Format**: snake_case
- **Extension**: `.py`
- **Examples**: `check_duplicates.py`, `verify_schema.py`

### Configuration Files
- **Format**: Standard names
- **Examples**: `pyproject.toml`, `requirements.txt`, `.gitignore`

---

## Reference Contracts

### README.md Contract

**Must include**:
- Link to `docs/README.md` (documentation index)
- Updated project structure section
- Links to deployment guides in `docs/deployment/`
- Links to operations guides in `docs/operations/`

**Must not include**:
- Broken links to old file locations
- References to files in root that have been moved

### Documentation Cross-Reference Contract

**All documentation files must**:
- Use relative paths for internal references
- Link to `docs/README.md` for navigation
- Have valid, working links
- Use consistent link format

**Example valid links**:
- `[Setup Guide](../deployment/supabase-setup.md)`
- `[Troubleshooting](../operations/troubleshooting.md)`
- `[Documentation Index](./README.md)`

### CI/CD Workflow Contract

**GitHub Actions workflows must**:
- Reference scripts using `scripts/` path
- Not reference moved files with old paths
- Work correctly after reorganization

**Example valid references**:
- `scripts/setup_db.sh`
- `scripts/verify_schema.py`

---

## Validation Checklist

### Pre-Reorganization
- [ ] All files to be moved identified
- [ ] All references to files mapped
- [ ] Target directory structure created
- [ ] `.gitignore` updated if needed

### During Reorganization
- [ ] Files moved to target locations
- [ ] All references updated
- [ ] Log files removed from git tracking
- [ ] Archive directory created if needed

### Post-Reorganization
- [ ] Root directory contains < 10 files
- [ ] All documentation in `docs/`
- [ ] All scripts in `scripts/`
- [ ] All links verified and working
- [ ] CI/CD workflows tested
- [ ] `CHANGELOG.md` updated
- [ ] `README.md` updated

---

## Compliance

### Enforcement

This contract is enforced through:
1. **Manual review**: Code review process checks structure compliance
2. **Automated checks**: CI/CD workflows verify structure
3. **Documentation**: README.md documents expected structure

### Violations

**Violations must be**:
- Documented in CHANGELOG.md
- Justified if intentional deviation
- Fixed if unintentional

**Common violations**:
- Files in wrong location
- Broken cross-references
- Missing required files
- Prohibited files in root

---

## Version History

| Version | Date | Changes |
|--------|------|---------|
| 1.0 | 2025-01-27 | Initial contract definition |


