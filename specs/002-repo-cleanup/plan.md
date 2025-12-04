# Implementation Plan: Repository Audit and Reorganization

**Branch**: `002-repo-cleanup` | **Date**: 2025-01-27 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/002-repo-cleanup/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Audit and reorganize the GitHub repository to improve clarity, usability, and maintainability. Remove duplicate, redundant, or outdated files. Consolidate all documentation into a clear, logical structure under a `docs/` directory. Ensure technical terms are defined where they appear and all sections are coherently linked. Enhance test documentation with example results. The final repository should present a clean, well-structured codebase that is easy for both newcomers and experienced contributors to understand and use.

## Technical Context

**Language/Version**: Python 3.8+ (existing project)  
**Primary Dependencies**: Git (for version control operations), Markdown (for documentation), Python (for utility scripts)  
**Storage**: N/A (file system reorganization only)  
**Testing**: N/A (documentation of existing tests, not modification of test code)  
**Target Platform**: GitHub repository (cross-platform compatible)  
**Project Type**: single (repository reorganization task, not a new code feature)  
**Performance Goals**: N/A (organizational task with no runtime performance requirements)  
**Constraints**: 
- Must preserve all functional code and tests (reorganization only, no code changes)
- Must update all references to moved files (README, workflows, scripts, cross-references)
- Must document all changes in CHANGELOG.md
- Must maintain backward compatibility for CI/CD workflows (update paths as needed)
- Must preserve historical context where valuable (archive rather than delete)
**Scale/Scope**: 
- ~15-20 files to reorganize (documentation, utility scripts, log files)
- 3 main documentation categories: operations guides, deployment guides, troubleshooting
- 4 standalone Python scripts to move to `scripts/`
- 3 log files to remove or gitignore
- Multiple Supabase-related docs to consolidate

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Design Status
**Status**: Constitution file at `.specify/memory/constitution.md` is currently a template with placeholders. No specific constitutional gates are defined at this time. Proceeding with implementation planning based on feature specification requirements.

**Design Principles Applied**:
- Single project structure (repository reorganization, not new code)
- Clear separation of concerns (documentation organization, file structure)
- Preservation of functionality (reorganization only, no code changes)
- Comprehensive documentation (consolidation and enhancement)
- Maintainability (clean structure for future contributors)

### Post-Design Re-Evaluation

**Status**: ✅ **PASSED** - All design artifacts completed successfully.

**Design Validation**:
- ✅ **Research Complete**: All technical decisions documented in `research.md` with rationale and alternatives
- ✅ **Data Model Defined**: Repository organization structure documented in `data-model.md` with file categories and relationships
- ✅ **Contracts Established**: File structure and reorganization rules defined in `contracts/` directory
- ✅ **Quickstart Created**: Step-by-step reorganization guide provided in `quickstart.md`
- ✅ **Agent Context Updated**: Cursor IDE context file updated with project information

**Constitutional Compliance**:
- ✅ No violations of project structure principles
- ✅ Maintains single project organization
- ✅ Preserves all functional code and tests
- ✅ Enhances documentation without breaking changes
- ✅ Follows Python project conventions

**Ready for Implementation**: All planning artifacts complete. Ready to proceed with `/speckit.tasks` to break down into implementation tasks.

## Project Structure

### Documentation (this feature)

```text
specs/002-repo-cleanup/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Repository Structure (Current → Target)

**Current State** (files to be reorganized):
```text
Root directory (cluttered):
├── check_duplicates.py          # → scripts/
├── find_missing_meetings.py     # → scripts/
├── run_migration.py              # → scripts/
├── verify_schema.py              # → scripts/
├── ingestion.log                 # → remove (gitignored)
├── local_ingestion_flexible.log  # → remove (gitignored)
├── local_ingestion.log           # → remove (gitignored)
├── data_structure_analysis.json  # → remove or docs/archive/
├── DUPLICATE_DIAGNOSIS.md        # → docs/operations/
├── OPERATIONS_RUNBOOK.md         # → docs/operations/
├── PRODUCTION_CHECKLIST.md       # → docs/operations/
├── SUPABASE_DEPLOYMENT_OPTIONS.md # → docs/deployment/
├── SUPABASE_QUICK_START.md       # → docs/deployment/
├── SUPABASE_SETUP_GUIDE.md       # → docs/deployment/
└── TROUBLESHOOTING.md            # → docs/operations/
```

**Target State** (clean organization):
```text
Root directory (clean):
├── README.md                     # Updated with new structure
├── CHANGELOG.md                  # Updated with reorganization entries
├── pyproject.toml
├── requirements.txt
├── .gitignore                    # Updated to exclude logs
├── src/                          # Unchanged
├── tests/                        # Unchanged
├── scripts/                      # Enhanced with moved utilities
│   ├── check_duplicates.py
│   ├── find_missing_meetings.py
│   ├── run_migration.py
│   ├── verify_schema.py
│   ├── check_constraints_and_duplicates.py
│   ├── setup_db.sh
│   ├── setup_db.sql
│   └── find_duplicates.sql
├── docs/                         # NEW: Consolidated documentation
│   ├── README.md                 # Documentation index
│   ├── operations/
│   │   ├── runbook.md            # OPERATIONS_RUNBOOK.md
│   │   ├── production-checklist.md # PRODUCTION_CHECKLIST.md
│   │   ├── troubleshooting.md   # TROUBLESHOOTING.md
│   │   └── duplicate-diagnosis.md # DUPLICATE_DIAGNOSIS.md
│   ├── deployment/
│   │   ├── supabase-setup.md     # SUPABASE_SETUP_GUIDE.md
│   │   ├── supabase-quickstart.md # SUPABASE_QUICK_START.md
│   │   └── deployment-options.md # SUPABASE_DEPLOYMENT_OPTIONS.md
│   └── archive/                  # Historical/analysis files
│       └── data-structure-analysis.json
└── specs/                        # Unchanged
    └── [existing spec directories]
```

**Structure Decision**: Single project structure maintained. The reorganization focuses on:
1. **Root directory cleanup**: Move utility scripts to `scripts/`, remove log files, organize documentation
2. **Documentation consolidation**: Create `docs/` directory with logical subdirectories (`operations/`, `deployment/`, `archive/`)
3. **Preservation**: All functional code and tests remain unchanged; only file organization improves
4. **Reference updates**: All cross-references in README, workflows, and documentation will be updated to reflect new paths

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |
