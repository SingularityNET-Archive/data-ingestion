# Data Model: Repository Organization Structure

**Date**: 2025-01-27  
**Feature**: 002-repo-cleanup

## Overview

This document defines the repository organization structure, file categorization, and relationships between documentation and code artifacts. The model describes how files are organized, categorized, and linked to create a maintainable and discoverable codebase.

---

## Repository Structure Hierarchy

```
Repository Root
├── Configuration Files (root level only)
│   ├── README.md
│   ├── CHANGELOG.md
│   ├── pyproject.toml
│   ├── requirements.txt
│   └── .gitignore
├── Source Code Directories
│   ├── src/                    # Application source code
│   └── tests/                  # Test suite
├── Utility Directories
│   └── scripts/                # Utility scripts and database setup
├── Documentation Directory
│   └── docs/                   # Consolidated documentation
│       ├── README.md           # Documentation index
│       ├── operations/         # Operational guides
│       ├── deployment/         # Deployment guides
│       └── archive/            # Historical/archived content
└── Specification Directory
    └── specs/                  # Feature specifications and plans
```

---

## File Categories

### 1. Configuration Files

**Location**: Repository root only  
**Purpose**: Project configuration and metadata

| File Type | Examples | Purpose | Constraints |
|-----------|----------|---------|-------------|
| **Project Metadata** | `README.md`, `CHANGELOG.md` | Project overview, change history | Must be in root for discoverability |
| **Build Configuration** | `pyproject.toml`, `requirements.txt` | Dependency management, build settings | Standard Python project files |
| **Version Control** | `.gitignore` | Git ignore patterns | Must be in root for git to recognize |

**Validation Rules**:
- Only essential configuration files in root
- No duplicate or redundant configuration files
- All configuration files must be actively used

**Relationships**:
- Referenced by CI/CD workflows
- Referenced by documentation
- Used by build tools and package managers

---

### 2. Source Code Files

**Location**: `src/` directory  
**Purpose**: Application source code

| Directory | Purpose | File Types |
|-----------|---------|------------|
| `src/models/` | Data models and schemas | `.py` files |
| `src/services/` | Business logic | `.py` files |
| `src/db/` | Database utilities | `.py` files |
| `src/cli/` | Command-line interface | `.py` files |
| `src/lib/` | Shared utilities | `.py` files |

**Validation Rules**:
- All Python source files organized by concern
- No standalone Python files in root (moved to `scripts/`)
- Consistent naming: snake_case for modules

**Relationships**:
- Referenced by tests in `tests/`
- Imported by CLI entry point
- Used by CI/CD workflows

---

### 3. Test Files

**Location**: `tests/` directory  
**Purpose**: Test suite for application

| Directory | Purpose | Test Types |
|-----------|---------|------------|
| `tests/unit/` | Unit tests | Component isolation tests |
| `tests/integration/` | Integration tests | End-to-end pipeline tests |
| `tests/contract/` | Contract tests | Data structure validation tests |

**Validation Rules**:
- Tests organized by test type
- Test files follow naming convention: `test_*.py`
- Test documentation includes examples and expected outcomes

**Relationships**:
- Tests reference source code in `src/`
- Test documentation in `tests/README.md`
- Executed by CI/CD workflows

---

### 4. Utility Scripts

**Location**: `scripts/` directory  
**Purpose**: Standalone utility scripts for maintenance and operations

| Script Category | Examples | Purpose |
|----------------|----------|---------|
| **Database Utilities** | `check_duplicates.py`, `verify_schema.py`, `run_migration.py` | Database maintenance and validation |
| **Analysis Utilities** | `find_missing_meetings.py` | Data analysis and reporting |
| **Database Setup** | `setup_db.sh`, `setup_db.sql` | Database schema initialization |

**Validation Rules**:
- All standalone Python scripts in `scripts/` directory
- Scripts have descriptive names indicating purpose
- Scripts are executable and documented

**Relationships**:
- May reference source code in `src/`
- Referenced by documentation (setup guides)
- Used by developers and CI/CD workflows

---

### 5. Documentation Files

**Location**: `docs/` directory with subdirectories  
**Purpose**: Project documentation organized by topic

#### 5.1 Operations Documentation

**Location**: `docs/operations/`  
**Purpose**: Day-to-day operational procedures

| File | Source | Purpose |
|------|--------|---------|
| `runbook.md` | `OPERATIONS_RUNBOOK.md` | Step-by-step operational procedures |
| `production-checklist.md` | `PRODUCTION_CHECKLIST.md` | Pre-deployment verification checklist |
| `troubleshooting.md` | `TROUBLESHOOTING.md` | Common issues and solutions |
| `duplicate-diagnosis.md` | `DUPLICATE_DIAGNOSIS.md` | Duplicate detection and resolution guide |

**Validation Rules**:
- All operations guides in `docs/operations/`
- Files use kebab-case naming
- Cross-references updated to new paths

**Relationships**:
- Referenced by README.md
- Referenced by deployment guides
- Used by operations team

#### 5.2 Deployment Documentation

**Location**: `docs/deployment/`  
**Purpose**: Deployment and setup guides

| File | Source | Purpose |
|------|--------|---------|
| `supabase-setup.md` | `SUPABASE_SETUP_GUIDE.md` | Comprehensive Supabase setup guide |
| `supabase-quickstart.md` | `SUPABASE_QUICK_START.md` | Quick reference checklist |
| `deployment-options.md` | `SUPABASE_DEPLOYMENT_OPTIONS.md` | All deployment method comparisons |

**Validation Rules**:
- All deployment guides in `docs/deployment/`
- Files use kebab-case naming
- Consolidated overlapping content

**Relationships**:
- Referenced by README.md
- Referenced by operations guides
- Used by developers setting up environment

#### 5.3 Archive Documentation

**Location**: `docs/archive/`  
**Purpose**: Historical or analysis files

| File | Source | Purpose |
|------|--------|---------|
| `data-structure-analysis.json` | `data_structure_analysis.json` | Historical data structure analysis |

**Validation Rules**:
- Historical files preserved for context
- Archive directory doesn't clutter active docs
- Files documented with purpose

**Relationships**:
- Referenced by documentation index
- Used for historical reference

#### 5.4 Documentation Index

**Location**: `docs/README.md`  
**Purpose**: Navigation index for all documentation

**Structure**:
- Overview of documentation organization
- Links to all documentation categories
- Quick navigation guide

**Validation Rules**:
- Must be kept up-to-date
- All documentation linked from index
- Clear navigation structure

---

### 6. Log Files

**Location**: Not in version control (gitignored)  
**Purpose**: Runtime execution logs

| File Type | Examples | Status |
|-----------|----------|--------|
| **Log Files** | `*.log` | Removed from git, gitignored |

**Validation Rules**:
- All `.log` files excluded from version control
- `.gitignore` includes `*.log` pattern
- Logs generated but not committed

**Relationships**:
- Generated by application execution
- Uploaded as CI/CD artifacts (not committed)
- Used for debugging and monitoring

---

## File Naming Conventions

### Documentation Files
- **Format**: kebab-case (e.g., `production-checklist.md`)
- **Extension**: `.md` for Markdown files
- **Descriptive**: Names clearly indicate content

### Python Scripts
- **Format**: snake_case (e.g., `check_duplicates.py`)
- **Extension**: `.py` for Python files
- **Descriptive**: Names indicate script purpose

### Configuration Files
- **Format**: Standard names (e.g., `pyproject.toml`, `requirements.txt`)
- **Location**: Root directory only
- **Standard**: Follow Python/project conventions

---

## File Relationships and Dependencies

### Cross-Reference Map

```
README.md
├── → docs/README.md (documentation index)
├── → docs/deployment/supabase-setup.md (setup guide)
├── → docs/operations/runbook.md (operations guide)
└── → specs/001-meeting-summaries-ingestion/quickstart.md (dev quickstart)

docs/README.md
├── → docs/operations/* (all operations docs)
├── → docs/deployment/* (all deployment docs)
└── → docs/archive/* (archived content)

docs/deployment/supabase-setup.md
├── → docs/deployment/supabase-quickstart.md (quick reference)
└── → docs/operations/troubleshooting.md (troubleshooting)

docs/operations/runbook.md
├── → docs/operations/production-checklist.md (pre-deployment)
└── → docs/operations/troubleshooting.md (error handling)
```

### Reference Update Requirements

**Before moving files, update references in**:
1. `README.md` - Main project documentation
2. `.github/workflows/*.yml` - CI/CD workflows
3. `docs/*.md` - Documentation cross-references
4. `scripts/*.py` - Script imports or file references
5. `CHANGELOG.md` - Change documentation

---

## File State Transitions

### Reorganization Workflow

1. **Audit Phase**
   - Identify all files to be moved/removed
   - Map all references to files
   - Document current state

2. **Update Phase**
   - Update all references to new paths
   - Update `.gitignore` if needed
   - Update `CHANGELOG.md` with planned changes

3. **Move Phase**
   - Move files to target locations
   - Remove log files from git tracking
   - Archive historical files

4. **Verification Phase**
   - Verify all references work
   - Test CI/CD workflows
   - Verify documentation links

5. **Documentation Phase**
   - Update `README.md` with new structure
   - Update `docs/README.md` index
   - Document changes in `CHANGELOG.md`

---

## Validation Rules

### Root Directory Rules
- **Maximum files**: < 10 files (excluding directories)
- **Allowed files**: README.md, CHANGELOG.md, configuration files only
- **Prohibited**: Log files, utility scripts, documentation files

### Documentation Rules
- **Location**: All documentation in `docs/` directory
- **Organization**: Logical subdirectories (operations/, deployment/, archive/)
- **Naming**: kebab-case for all documentation files
- **Cross-references**: All links must be valid

### Script Rules
- **Location**: All utility scripts in `scripts/` directory
- **Naming**: snake_case for Python scripts
- **Documentation**: Scripts should have docstrings or README

### Log File Rules
- **Version control**: No log files tracked in git
- **Gitignore**: `*.log` pattern must be present
- **CI/CD**: Logs uploaded as artifacts, not committed

---

## Success Metrics

### Measurable Outcomes

| Metric | Target | Measurement |
|--------|--------|-------------|
| Root directory files | < 10 files | Count files in root |
| Documentation organization | 100% in `docs/` | Verify no docs in root |
| Script organization | 100% in `scripts/` | Verify no scripts in root |
| Log file tracking | 0 tracked | Verify git status |
| Broken references | 0 broken | Test all links |
| Cross-reference validity | 100% valid | Verify all links work |

---

## Maintenance Guidelines

### Adding New Files

**Documentation**:
- Place in appropriate `docs/` subdirectory
- Use kebab-case naming
- Update `docs/README.md` index
- Add cross-references as needed

**Scripts**:
- Place in `scripts/` directory
- Use snake_case naming
- Add docstrings
- Document in relevant guides if needed

**Configuration**:
- Only essential configs in root
- Follow Python project conventions
- Update `.gitignore` if needed

### Updating Existing Files

**Documentation**:
- Maintain kebab-case naming
- Update cross-references if moving
- Update `CHANGELOG.md` for significant changes

**Scripts**:
- Maintain snake_case naming
- Update imports if moving
- Update documentation references

---

## Archive Strategy

### Archive Criteria
- Historical analysis files
- Deprecated guides (if valuable context)
- Reference materials not actively used

### Archive Location
- `docs/archive/` directory
- Preserve original names or descriptive names
- Include README explaining archive contents

### Archive Maintenance
- Review periodically for relevance
- Remove if no longer valuable
- Document purpose in archive README

