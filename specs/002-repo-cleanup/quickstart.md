# Quickstart: Repository Reorganization

**Date**: 2025-01-27  
**Feature**: 002-repo-cleanup

## Overview

This quickstart guide provides step-by-step instructions for reorganizing the repository structure. Follow these steps to clean up the root directory, consolidate documentation, and organize utility scripts.

---

## Prerequisites

- Git repository access
- Terminal/command line access
- Understanding of repository structure
- Backup of current state (optional but recommended)

---

## Step-by-Step Guide

### Step 1: Create Target Directory Structure

Create the new documentation directory structure:

```bash
# From repository root
mkdir -p docs/operations
mkdir -p docs/deployment
mkdir -p docs/archive
```

**Verify**:
```bash
ls -la docs/
# Should show: operations/, deployment/, archive/
```

---

### Step 2: Audit Current Files

Identify all files to be moved or removed:

```bash
# List files in root that need reorganization
ls -1 *.md *.py *.log *.json 2>/dev/null

# Expected files to move:
# - Documentation: DUPLICATE_DIAGNOSIS.md, OPERATIONS_RUNBOOK.md, etc.
# - Scripts: check_duplicates.py, find_missing_meetings.py, etc.
# - Logs: *.log files
# - Analysis: data_structure_analysis.json
```

---

### Step 3: Find All References

Before moving files, find all references to them:

```bash
# Find references to documentation files
grep -r "SUPABASE_SETUP_GUIDE.md" .
grep -r "OPERATIONS_RUNBOOK.md" .
grep -r "PRODUCTION_CHECKLIST.md" .
grep -r "TROUBLESHOOTING.md" .
grep -r "DUPLICATE_DIAGNOSIS.md" .
grep -r "SUPABASE_QUICK_START.md" .
grep -r "SUPABASE_DEPLOYMENT_OPTIONS.md" .

# Find references to scripts
grep -r "check_duplicates.py" .
grep -r "find_missing_meetings.py" .
grep -r "run_migration.py" .
grep -r "verify_schema.py" .
```

**Note**: Document all found references for updating.

---

### Step 4: Update References in README.md

Update `README.md` to reference new documentation structure:

```bash
# Edit README.md
# Change references from:
# - SUPABASE_SETUP_GUIDE.md → docs/deployment/supabase-setup.md
# - OPERATIONS_RUNBOOK.md → docs/operations/runbook.md
# - etc.
```

**Example changes**:
```markdown
# Before
- **Supabase Setup Guide**: `SUPABASE_SETUP_GUIDE.md`

# After
- **Supabase Setup Guide**: `docs/deployment/supabase-setup.md`
```

---

### Step 5: Update References in Documentation

Update cross-references in documentation files:

```bash
# Update internal documentation references
# Use relative paths from each file's location
```

**Example**:
- In `docs/deployment/supabase-setup.md`: `[Troubleshooting](../operations/troubleshooting.md)`
- In `docs/operations/runbook.md`: `[Production Checklist](./production-checklist.md)`

---

### Step 6: Update CI/CD Workflows

Update GitHub Actions workflows if they reference moved files:

```bash
# Check .github/workflows/*.yml files
# Update any script references to use scripts/ path
```

**Example**:
```yaml
# Before
run: python verify_schema.py

# After
run: python scripts/verify_schema.py
```

---

### Step 7: Move Documentation Files

Move documentation files to new locations with kebab-case naming:

```bash
# Move operations documentation
git mv OPERATIONS_RUNBOOK.md docs/operations/runbook.md
git mv PRODUCTION_CHECKLIST.md docs/operations/production-checklist.md
git mv TROUBLESHOOTING.md docs/operations/troubleshooting.md
git mv DUPLICATE_DIAGNOSIS.md docs/operations/duplicate-diagnosis.md

# Move deployment documentation
git mv SUPABASE_SETUP_GUIDE.md docs/deployment/supabase-setup.md
git mv SUPABASE_QUICK_START.md docs/deployment/supabase-quickstart.md
git mv SUPABASE_DEPLOYMENT_OPTIONS.md docs/deployment/deployment-options.md
```

**Verify**:
```bash
ls -la docs/operations/
ls -la docs/deployment/
# Should show all moved files
```

---

### Step 8: Move Utility Scripts

Move Python utility scripts to `scripts/` directory:

```bash
# Move scripts
git mv check_duplicates.py scripts/
git mv find_missing_meetings.py scripts/
git mv run_migration.py scripts/
git mv verify_schema.py scripts/
```

**Verify**:
```bash
ls -la scripts/*.py
# Should show all moved scripts
```

---

### Step 9: Handle Log Files

Remove log files from version control:

```bash
# Verify .gitignore includes *.log
grep "\.log" .gitignore

# Remove log files from git tracking
git rm --cached *.log

# Verify logs are gitignored
git status
# Should not show .log files
```

---

### Step 10: Archive Analysis Files

Move historical analysis files to archive:

```bash
# Move analysis file
git mv data_structure_analysis.json docs/archive/data-structure-analysis.json
```

**Note**: If file is not valuable, remove instead:
```bash
git rm data_structure_analysis.json
```

---

### Step 11: Create Documentation Index

Create `docs/README.md` as navigation index:

```bash
# Create docs/README.md with:
# - Overview of documentation organization
# - Links to all documentation categories
# - Quick navigation guide
```

**Template**:
```markdown
# Documentation Index

## Overview

This directory contains all project documentation organized by topic.

## Documentation Categories

### Operations
- [Runbook](operations/runbook.md) - Operational procedures
- [Production Checklist](operations/production-checklist.md) - Pre-deployment checklist
- [Troubleshooting](operations/troubleshooting.md) - Common issues and solutions
- [Duplicate Diagnosis](operations/duplicate-diagnosis.md) - Duplicate detection guide

### Deployment
- [Supabase Setup](deployment/supabase-setup.md) - Comprehensive setup guide
- [Supabase Quick Start](deployment/supabase-quickstart.md) - Quick reference
- [Deployment Options](deployment/deployment-options.md) - All deployment methods

### Archive
- Historical and analysis files preserved for reference
```

---

### Step 12: Update CHANGELOG.md

Document all changes in `CHANGELOG.md`:

```bash
# Add entry to CHANGELOG.md
```

**Template**:
```markdown
## [Unreleased] - 2025-01-27

### Changed
- Moved utility scripts from root to `scripts/` directory
- Consolidated Supabase documentation into `docs/deployment/`
- Organized operations guides into `docs/operations/`
- Updated all documentation cross-references

### Removed
- Removed log files from version control (now gitignored)
- Removed outdated analysis files (archived in `docs/archive/`)

### Added
- Created `docs/` directory structure with operations/ and deployment/ subdirectories
- Added `docs/README.md` as documentation index
```

---

### Step 13: Verify All Changes

Verify that all changes work correctly:

```bash
# Verify root directory is clean
ls -1 | grep -E "\.(md|py|log|json)$"
# Should show minimal files (README.md, CHANGELOG.md, config files only)

# Verify documentation structure
ls -R docs/
# Should show organized subdirectories

# Verify scripts are in scripts/
ls -1 scripts/*.py
# Should show all utility scripts

# Verify links work (if using link checker)
# Or manually check README.md links
```

---

### Step 14: Test CI/CD Workflows

Test that CI/CD workflows still work:

```bash
# If possible, test GitHub Actions workflows
# Or verify workflow files reference correct paths
```

**Check**:
- Workflows reference `scripts/` paths correctly
- No broken file references
- All workflows execute successfully

---

### Step 15: Commit Changes

Commit all changes:

```bash
# Review changes
git status

# Stage all changes
git add .

# Commit with descriptive message
git commit -m "Reorganize repository structure

- Move documentation to docs/ directory
- Move utility scripts to scripts/ directory
- Remove log files from version control
- Update all cross-references
- Create documentation index

See CHANGELOG.md for detailed changes."
```

---

## Verification Checklist

After completing all steps, verify:

- [ ] Root directory contains < 10 files
- [ ] All documentation in `docs/` directory
- [ ] All scripts in `scripts/` directory
- [ ] All log files removed from git tracking
- [ ] All links verified and working
- [ ] `docs/README.md` created as index
- [ ] `CHANGELOG.md` updated
- [ ] `README.md` updated with new structure
- [ ] CI/CD workflows tested
- [ ] No broken references

---

## Troubleshooting

### Issue: Broken Links After Move

**Solution**: Search for old file names and update references:
```bash
grep -r "OLD_FILE_NAME" .
# Update all found references
```

### Issue: CI/CD Workflow Fails

**Solution**: Check workflow files for old paths:
```bash
grep -r "old_path" .github/workflows/
# Update to new paths
```

### Issue: Scripts Don't Execute

**Solution**: Verify scripts are executable and paths are correct:
```bash
chmod +x scripts/*.py
# Update any imports or file references in scripts
```

---

## Next Steps

After reorganization:

1. **Review**: Have team members review new structure
2. **Update**: Update any external documentation referencing old paths
3. **Communicate**: Notify team of new structure
4. **Maintain**: Keep structure clean going forward

---

## Additional Resources

- [File Structure Contract](contracts/file-structure.md) - Expected structure definition
- [Reorganization Rules](contracts/reorganization-rules.md) - Detailed rules and procedures
- [Data Model](data-model.md) - Repository organization model
- [Research](research.md) - Best practices and rationale




