# Reorganization Rules Contract

**Date**: 2025-01-27  
**Feature**: 002-repo-cleanup

## Overview

This contract defines the rules and procedures for reorganizing repository files. All file moves, removals, and organizational changes must follow these rules to ensure consistency and prevent broken references.

---

## File Move Rules

### Rule 1: Reference Update Before Move

**Requirement**: All references to a file must be updated BEFORE the file is moved.

**Rationale**: Prevents broken links and ensures continuous functionality.

**Process**:
1. Identify all references to file (grep/search)
2. Update all references to new path
3. Verify updates are correct
4. Move file to new location
5. Verify file works in new location

**Example**:
```bash
# Step 1: Find references
grep -r "SUPABASE_SETUP_GUIDE.md" .

# Step 2: Update references
# In README.md: Change link to docs/deployment/supabase-setup.md

# Step 3: Move file
git mv SUPABASE_SETUP_GUIDE.md docs/deployment/supabase-setup.md

# Step 4: Verify
# Check README.md link works
```

---

### Rule 2: Consistent Naming Convention

**Requirement**: All moved files must follow naming conventions:
- Documentation: kebab-case (e.g., `production-checklist.md`)
- Scripts: snake_case (e.g., `check_duplicates.py`)

**Rationale**: Consistent naming improves discoverability and maintainability.

**Transformation Examples**:
- `PRODUCTION_CHECKLIST.md` → `docs/operations/production-checklist.md`
- `SUPABASE_SETUP_GUIDE.md` → `docs/deployment/supabase-setup.md`
- `check_duplicates.py` → `scripts/check_duplicates.py` (no rename needed)

---

### Rule 3: Logical Directory Organization

**Requirement**: Files must be organized into logical directories based on purpose.

**Directory Mapping**:
- **Operations guides** → `docs/operations/`
- **Deployment guides** → `docs/deployment/`
- **Utility scripts** → `scripts/`
- **Historical/analysis** → `docs/archive/`

**Rationale**: Logical organization improves discoverability and navigation.

---

### Rule 4: Preserve Historical Context

**Requirement**: Valuable historical files must be archived, not deleted.

**Archive Criteria**:
- Analysis files that provide context
- Historical documentation with valuable insights
- Reference materials that may be useful

**Process**:
1. Evaluate file for historical value
2. If valuable, move to `docs/archive/`
3. If not valuable, remove from git tracking
4. Document archive contents in `docs/archive/README.md`

---

## File Removal Rules

### Rule 5: Log File Removal

**Requirement**: All `.log` files must be removed from version control.

**Process**:
1. Verify `.gitignore` includes `*.log` pattern
2. Remove log files from git tracking: `git rm --cached *.log`
3. Commit removal
4. Verify logs are gitignored going forward

**Rationale**: Log files are runtime artifacts, not source code.

---

### Rule 6: Outdated File Removal

**Requirement**: Outdated or temporary files must be removed or archived.

**Removal Criteria**:
- Temporary analysis files (if not valuable)
- Duplicate files
- Deprecated files (if no historical value)

**Archive Criteria**:
- Analysis files with valuable context
- Historical documentation
- Reference materials

**Process**:
1. Evaluate file value
2. Archive if valuable, remove if not
3. Document decision in CHANGELOG.md

---

## Reference Update Rules

### Rule 7: Comprehensive Reference Audit

**Requirement**: All references must be identified and updated.

**Reference Sources**:
- `README.md` - Main documentation
- `.github/workflows/*.yml` - CI/CD workflows
- `docs/*.md` - Documentation cross-references
- `scripts/*.py` - Script imports
- `CHANGELOG.md` - Change documentation

**Process**:
1. Search for file name across repository
2. Identify all references
3. Update each reference
4. Verify updates are correct

---

### Rule 8: Relative Path Usage

**Requirement**: Documentation cross-references must use relative paths.

**Rationale**: Relative paths work regardless of repository location.

**Examples**:
- `[Setup Guide](../deployment/supabase-setup.md)` ✅
- `[Setup Guide](docs/deployment/supabase-setup.md)` ✅ (from root)
- `[Setup Guide](https://github.com/.../supabase-setup.md)` ❌ (avoid absolute URLs)

---

## Documentation Rules

### Rule 9: Documentation Index Maintenance

**Requirement**: `docs/README.md` must serve as navigation index.

**Must include**:
- Overview of documentation organization
- Links to all documentation categories
- Quick navigation guide

**Process**:
1. Create/update `docs/README.md`
2. Link all documentation categories
3. Provide clear navigation structure
4. Keep index up-to-date

---

### Rule 10: Technical Term Definitions

**Requirement**: Technical terms must be defined where first used.

**Process**:
1. Identify technical terms in documentation
2. Define term where first used
3. Optionally create glossary for common terms
4. Cross-reference definitions as needed

**Example**:
```markdown
## Idempotent Operations

An **idempotent** operation produces the same result regardless of how many times it is applied. In this pipeline, UPSERT operations are idempotent, meaning running ingestion multiple times produces the same final state.
```

---

## CHANGELOG Rules

### Rule 11: Comprehensive Change Documentation

**Requirement**: All file moves and removals must be documented in CHANGELOG.md.

**Format**:
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

**Process**:
1. Document all changes in CHANGELOG.md
2. Use clear, descriptive entries
3. Group changes by type (Changed/Removed/Added)
4. Include dates and version information

---

## Verification Rules

### Rule 12: Pre-Move Verification

**Requirement**: Verify all prerequisites before moving files.

**Checklist**:
- [ ] All references identified
- [ ] All references updated
- [ ] Target directories created
- [ ] `.gitignore` updated if needed
- [ ] CHANGELOG.md entry prepared

---

### Rule 13: Post-Move Verification

**Requirement**: Verify all changes work correctly after reorganization.

**Checklist**:
- [ ] All links verified and working
- [ ] CI/CD workflows tested
- [ ] Scripts execute correctly
- [ ] Documentation renders correctly
- [ ] No broken references
- [ ] Root directory structure correct

---

## Exception Handling

### Rule 14: Documented Exceptions

**Requirement**: Any deviation from these rules must be documented and justified.

**Process**:
1. Document exception in CHANGELOG.md
2. Provide justification
3. Get approval if needed
4. Update rules if exception becomes standard

---

## Compliance

### Enforcement

These rules are enforced through:
1. **Code review**: Reviewers check rule compliance
2. **Automated checks**: CI/CD workflows verify structure
3. **Documentation**: Rules documented and accessible

### Violations

**Violations must be**:
- Fixed immediately if unintentional
- Documented and justified if intentional
- Reviewed for rule updates if common

---

## Version History

| Version | Date | Changes |
|--------|------|---------|
| 1.0 | 2025-01-27 | Initial rules definition |





