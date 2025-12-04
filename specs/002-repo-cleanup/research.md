# Research: Repository Audit and Reorganization

**Date**: 2025-01-27  
**Feature**: 002-repo-cleanup

## Overview

This document consolidates research findings and best practices for repository organization, documentation structure, and file management. All technical decisions have been made based on industry best practices and the specific requirements of this Python data ingestion project.

---

## 1. Repository Root Directory Organization

### Decision
Keep root directory minimal with only essential files: README.md, configuration files (pyproject.toml, requirements.txt, .gitignore), and top-level directories (src/, tests/, scripts/, docs/, specs/).

### Rationale
- **Clarity**: Minimal root directory makes repository structure immediately understandable
- **Professional appearance**: Clean root directory signals well-maintained project
- **Navigation**: Essential files are easy to find without scrolling through clutter
- **Standard practice**: Aligns with Python project conventions (PEP 518, setuptools standards)

### Best Practices Applied
- Configuration files in root: `pyproject.toml`, `requirements.txt`, `.gitignore`
- Source code in `src/` directory (standard Python layout)
- Tests in `tests/` directory (pytest convention)
- Utility scripts in `scripts/` directory
- Documentation in `docs/` directory (common convention)
- Specifications/plans in `specs/` directory (project-specific)

### Alternatives Considered
- **Flat structure**: Rejected due to poor scalability and organization
- **Multiple root configs**: Accepted only for essential files (pyproject.toml, requirements.txt)

---

## 2. Documentation Organization Structure

### Decision
Organize documentation in `docs/` directory with logical subdirectories:
- `docs/operations/` - Operational guides (runbook, troubleshooting, production checklist)
- `docs/deployment/` - Deployment guides (Supabase setup, deployment options)
- `docs/archive/` - Historical or analysis files that may have value but aren't actively used

### Rationale
- **Discoverability**: Logical grouping makes documentation easy to find
- **Scalability**: Subdirectories allow growth without cluttering single directory
- **Clarity**: Clear categorization helps users find relevant information quickly
- **Maintenance**: Organized structure makes it easier to keep documentation up-to-date

### Documentation Categories
1. **Operations**: Day-to-day operational procedures, troubleshooting, production checklists
2. **Deployment**: Setup guides, deployment options, platform-specific instructions
3. **Archive**: Historical analysis, deprecated guides, reference materials

### Best Practices
- Include `docs/README.md` as documentation index with navigation
- Use consistent naming: kebab-case for files (`production-checklist.md`, not `PRODUCTION_CHECKLIST.md`)
- Maintain clear hierarchy: general → specific (e.g., deployment → supabase-setup)
- Cross-reference related documents with relative links

### Alternatives Considered
- **Single docs directory**: Rejected due to poor scalability (too many files)
- **Root-level docs**: Rejected because it clutters root directory

---

## 3. Utility Script Organization

### Decision
Move all standalone Python utility scripts from root to `scripts/` directory.

### Rationale
- **Consistency**: All utility scripts in one location
- **Clarity**: Root directory remains clean
- **Discoverability**: Users know where to find utility scripts
- **Standard practice**: Common Python project convention

### Script Categories
- **Database utilities**: `check_duplicates.py`, `verify_schema.py`, `run_migration.py`
- **Analysis utilities**: `find_missing_meetings.py`
- **Database setup**: `setup_db.sh`, `setup_db.sql` (already in scripts/)

### Naming Conventions
- Use descriptive names: `check_duplicates.py` not `check.py`
- Use kebab-case or snake_case consistently
- Include purpose in name: `verify_schema.py` clearly indicates function

### Alternatives Considered
- **Keep scripts in root**: Rejected due to root directory clutter
- **Separate directories per script type**: Rejected as over-engineering for current scale

---

## 4. Log File Management

### Decision
Remove all `.log` files from version control and ensure `.gitignore` properly excludes them.

### Rationale
- **Version control best practice**: Log files are runtime artifacts, not source code
- **Repository size**: Log files can grow large and bloat repository
- **No value in tracking**: Log files are ephemeral and regenerated on each run
- **Security**: Logs may contain sensitive information (connection strings, errors)

### Implementation
- Verify `.gitignore` includes `*.log` pattern (already present)
- Remove existing log files from git tracking: `git rm --cached *.log`
- Ensure CI/CD workflows don't commit logs
- Document that logs are generated but not tracked

### Log File Handling
- **Local development**: Logs generated but gitignored
- **CI/CD**: Logs uploaded as artifacts (GitHub Actions) but not committed
- **Production**: Logs streamed to stdout/stderr for container logging

### Alternatives Considered
- **Track logs in git**: Rejected due to repository bloat and security concerns
- **Separate logs directory**: Rejected as unnecessary if logs are gitignored

---

## 5. Documentation Consolidation Strategy

### Decision
Consolidate overlapping Supabase-related documentation into single comprehensive guides with clear sections.

### Rationale
- **Eliminate duplication**: Single source of truth prevents inconsistencies
- **Easier maintenance**: Updates only needed in one place
- **Better user experience**: Users don't need to piece together information from multiple files
- **Reduced confusion**: Clear, comprehensive guides are easier to follow

### Consolidation Approach
- **Supabase Setup Guide**: Primary comprehensive guide with step-by-step instructions
- **Supabase Quick Start**: Condensed checklist version for experienced users
- **Deployment Options**: Comprehensive guide covering all deployment methods (GitHub Actions, serverless, etc.)

### Content Organization
- **Setup Guide**: Detailed instructions, prerequisites, troubleshooting
- **Quick Start**: Minimal steps for rapid setup (assumes familiarity)
- **Deployment Options**: Comparison of methods, pros/cons, specific instructions

### Cross-Referencing
- Quick Start references Setup Guide for details
- Deployment Options references Setup Guide for prerequisites
- All guides link to troubleshooting documentation

### Alternatives Considered
- **Keep separate files**: Rejected due to duplication and maintenance burden
- **Single monolithic guide**: Rejected as too long and hard to navigate

---

## 6. Technical Term Definition Strategy

### Decision
Define technical terms where they first appear in documentation, with optional glossary for common terms.

### Rationale
- **Accessibility**: New contributors can understand without external research
- **Clarity**: Explicit definitions prevent misunderstandings
- **Self-contained**: Documentation doesn't require external knowledge
- **Professional**: Well-defined terms signal thorough documentation

### Definition Format
- **Inline definitions**: Define term in context where first used
- **Glossary**: Optional centralized glossary for frequently used terms
- **Cross-references**: Link to definitions when term reappears

### Terms to Define
- **Idempotent**: Operation that produces same result regardless of how many times applied
- **UPSERT**: Database operation that inserts new record or updates existing one
- **JSONB**: PostgreSQL binary JSON format with indexing support
- **Workgroup**: Organizational unit grouping related meetings
- **Ingestion**: Process of importing external data into system

### Alternatives Considered
- **No definitions**: Rejected as creates barrier for new contributors
- **Separate glossary only**: Rejected as requires jumping between documents

---

## 7. Test Documentation Enhancement

### Decision
Enhance test documentation with example results, expected outcomes, and purpose statements for each test category.

### Rationale
- **Clarity**: Example results show what success looks like
- **Onboarding**: New contributors understand test expectations
- **Debugging**: Example outputs help identify test failures
- **Maintenance**: Clear documentation helps maintain test suite

### Documentation Structure
- **Test Purpose**: What each test category verifies
- **Example Results**: Sample successful test output
- **Expected Outcomes**: What each test should verify
- **Common Failures**: Typical failure scenarios and meanings

### Test Categories
1. **Unit Tests**: Individual component testing
2. **Integration Tests**: End-to-end pipeline testing
3. **Contract Tests**: Data structure validation testing

### Example Format
```markdown
## Unit Tests

**Purpose**: Verify individual components work correctly in isolation.

**Example Output**:
```
tests/unit/test_validators.py::test_validate_uuid PASSED
tests/unit/test_models.py::test_meeting_model PASSED
```

**Expected Outcomes**:
- All validation functions return correct results
- Models serialize/deserialize correctly
- Error handling works as expected
```

### Alternatives Considered
- **Minimal documentation**: Rejected as doesn't help new contributors
- **Code comments only**: Rejected as less discoverable than dedicated docs

---

## 8. File Reference Update Strategy

### Decision
Audit all file references (README, workflows, scripts, cross-references) and update paths before moving files.

### Rationale
- **Prevent broken links**: Update references before move prevents 404s
- **Maintain functionality**: CI/CD workflows must continue working
- **User experience**: Broken links frustrate users
- **Professional**: Working references signal attention to detail

### Reference Audit Checklist
- [ ] README.md links to documentation
- [ ] GitHub Actions workflows reference scripts/files
- [ ] Documentation cross-references
- [ ] Script imports or file references
- [ ] CHANGELOG.md entries

### Update Process
1. **Identify all references**: Search for file names across repository
2. **Update before move**: Change references first, then move files
3. **Verify**: Test all references work after reorganization
4. **Document**: Record all changes in CHANGELOG.md

### Alternatives Considered
- **Update after move**: Rejected due to temporary broken state
- **Redirects/aliases**: Considered but git doesn't support symlinks well

---

## 9. Historical File Preservation

### Decision
Archive valuable historical content in `docs/archive/` rather than deleting.

### Rationale
- **Preserve context**: Historical analysis may provide valuable insights
- **Audit trail**: Shows evolution of project understanding
- **Low cost**: Archive directory doesn't clutter active documentation
- **Future reference**: May be useful for understanding decisions

### Archive Criteria
- **Analysis files**: Data structure analysis, duplicate diagnosis
- **Deprecated guides**: Old deployment methods (if valuable context)
- **Historical context**: Documents explaining past decisions

### Archive Naming
- Use descriptive names: `data-structure-analysis.json`
- Include date if relevant: `duplicate-diagnosis-2025-01.md`
- Document purpose: Include README in archive explaining contents

### Alternatives Considered
- **Delete historical files**: Rejected as loses potentially valuable context
- **Keep in active docs**: Rejected as clutters current documentation

---

## 10. CHANGELOG Documentation Strategy

### Decision
Document all file moves, removals, and organizational changes in CHANGELOG.md with clear entries.

### Rationale
- **Transparency**: Users can see what changed and why
- **Migration guide**: Helps users adapt to new structure
- **Historical record**: Documents evolution of repository organization
- **Professional**: Standard practice for well-maintained projects

### CHANGELOG Format
```markdown
## [Unreleased] - 2025-01-27

### Changed
- Moved utility scripts from root to `scripts/` directory
- Consolidated Supabase documentation into `docs/deployment/`
- Organized operations guides into `docs/operations/`

### Removed
- Removed log files from version control (now gitignored)
- Removed outdated analysis files (archived in `docs/archive/`)

### Added
- Created `docs/` directory structure with operations/ and deployment/ subdirectories
- Added `docs/README.md` as documentation index
```

### Alternatives Considered
- **No changelog**: Rejected as doesn't communicate changes to users
- **Git history only**: Rejected as less discoverable than explicit changelog

---

## Summary of Technical Decisions

| Decision Area | Choice | Key Rationale |
|--------------|--------|---------------|
| Root Directory | Minimal essential files only | Clarity and professional appearance |
| Documentation Structure | `docs/` with operations/, deployment/, archive/ | Logical organization and scalability |
| Utility Scripts | All in `scripts/` directory | Consistency and discoverability |
| Log Files | Remove from git, ensure gitignore | Version control best practice |
| Documentation Consolidation | Merge overlapping docs | Single source of truth |
| Technical Terms | Define where first used | Accessibility for new contributors |
| Test Documentation | Examples, purposes, expected outcomes | Clarity and onboarding |
| File References | Update before move | Prevent broken links |
| Historical Files | Archive in `docs/archive/` | Preserve context |
| CHANGELOG | Document all changes | Transparency and migration guide |

---

## Resolved Clarifications

All technical decisions have been made based on:
1. Feature specification requirements
2. Python project best practices
3. GitHub repository conventions
4. Documentation organization standards
5. Version control best practices

No outstanding "NEEDS CLARIFICATION" items remain in Technical Context. The reorganization plan is ready for implementation.

