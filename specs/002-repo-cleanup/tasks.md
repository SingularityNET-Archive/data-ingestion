---
description: "Task list for Repository Audit and Reorganization implementation"
---

# Tasks: Repository Audit and Reorganization

**Input**: Design documents from `/specs/002-repo-cleanup/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Tests are OPTIONAL - only include them if explicitly requested in the feature specification or if user requests TDD approach. This reorganization task does not require test tasks.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: Repository root with `src/`, `tests/`, `scripts/`, `docs/` directories
- Paths shown below assume single project structure per plan.md

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and directory structure preparation

- [X] T001 Create target directory structure (docs/operations/, docs/deployment/, docs/archive/)
- [X] T002 [P] Audit current repository state and identify all files to be moved or removed
- [X] T003 [P] Verify .gitignore includes *.log pattern for log file exclusion
- [X] T004 [P] Create comprehensive list of all file references to be updated (README.md, workflows, documentation cross-references)

**Checkpoint**: Setup complete - directory structure ready and audit complete

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T005 Find all references to files that will be moved (grep/search across repository for documentation file names)
- [X] T006 Find all references to scripts that will be moved (grep/search for script file names in workflows and documentation)
- [X] T007 Document all found references in a reference audit document for tracking updates
- [X] T008 Verify target directories exist and are ready for file moves

**Checkpoint**: Foundation ready - all references identified and documented, user story implementation can now begin

---

## Phase 3: User Story 1 - Clean Repository Structure (Priority: P1) 🎯 MVP

**Goal**: A new contributor or maintainer needs to understand the repository structure at a glance and find files in logical locations without confusion from duplicate, outdated, or misplaced files.

**Independent Test**: Can be fully tested by examining the repository root directory and verifying that:
- No duplicate files exist
- All files are in appropriate directories
- No outdated or temporary files remain in version control
- Root directory contains only essential files (README, configuration files, top-level directories)

### Implementation for User Story 1

- [X] T009 [US1] Update README.md to reference new documentation structure (change links from root-level docs to docs/ subdirectories)
- [X] T010 [US1] Update .github/workflows/*.yml files to reference scripts using scripts/ path instead of root paths
- [X] T011 [US1] Move check_duplicates.py from root to scripts/check_duplicates.py using git mv
- [X] T012 [US1] Move find_missing_meetings.py from root to scripts/find_missing_meetings.py using git mv
- [X] T013 [US1] Move run_migration.py from root to scripts/run_migration.py using git mv
- [X] T014 [US1] Move verify_schema.py from root to scripts/verify_schema.py using git mv
- [X] T015 [US1] Remove log files from git tracking (git rm --cached *.log for ingestion.log, local_ingestion_flexible.log, local_ingestion.log)
- [X] T016 [US1] Verify log files are gitignored and will not be tracked going forward
- [X] T017 [US1] Move data_structure_analysis.json from root to docs/archive/data-structure-analysis.json using git mv
- [X] T018 [US1] Verify root directory contains fewer than 10 files (excluding directories) after reorganization

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently - repository root is clean and organized

---

## Phase 4: User Story 2 - Consolidated Documentation Structure (Priority: P1) 🎯 MVP

**Goal**: A user needs to find comprehensive, well-organized documentation that covers all aspects of the project without navigating through scattered, overlapping, or redundant documents.

**Independent Test**: Can be fully tested by examining the documentation structure and verifying that:
- All documentation is organized in a clear `docs/` directory structure
- No duplicate or overlapping documentation exists
- All documents are linked coherently
- Technical terms are defined where they first appear

### Implementation for User Story 2

- [X] T019 [US2] Update all cross-references in README.md to point to new documentation locations in docs/ subdirectories
- [X] T020 [US2] Move OPERATIONS_RUNBOOK.md from root to docs/operations/runbook.md using git mv with kebab-case naming
- [X] T021 [US2] Move PRODUCTION_CHECKLIST.md from root to docs/operations/production-checklist.md using git mv with kebab-case naming
- [X] T022 [US2] Move TROUBLESHOOTING.md from root to docs/operations/troubleshooting.md using git mv with kebab-case naming
- [X] T023 [US2] Move DUPLICATE_DIAGNOSIS.md from root to docs/operations/duplicate-diagnosis.md using git mv with kebab-case naming
- [X] T024 [US2] Move SUPABASE_SETUP_GUIDE.md from root to docs/deployment/supabase-setup.md using git mv with kebab-case naming
- [X] T025 [US2] Move SUPABASE_QUICK_START.md from root to docs/deployment/supabase-quickstart.md using git mv with kebab-case naming
- [X] T026 [US2] Move SUPABASE_DEPLOYMENT_OPTIONS.md from root to docs/deployment/deployment-options.md using git mv with kebab-case naming
- [X] T027 [US2] Update all internal cross-references in moved documentation files to use relative paths (e.g., ../deployment/supabase-setup.md from operations docs)
- [X] T028 [US2] Consolidate overlapping content in Supabase documentation files (merge duplicate information into single comprehensive guides)
- [X] T029 [US2] Add technical term definitions where they first appear in documentation (define terms like idempotent, UPSERT, JSONB, workgroup, ingestion inline)
- [X] T030 [US2] Create docs/README.md as documentation index with navigation links to all documentation categories
- [X] T031 [US2] Update CHANGELOG.md with comprehensive entry documenting all file moves and organizational changes
- [X] T032 [US2] Verify all documentation cross-references are valid and lead to correct locations
- [X] T033 [US2] Verify no duplicate or overlapping documentation files exist after consolidation

**Checkpoint**: At this point, User Story 2 should be fully functional and testable independently - all documentation is organized and consolidated

---

## Phase 5: User Story 3 - Enhanced Test Documentation (Priority: P2)

**Goal**: A developer needs to understand what tests exist, what they verify, and what successful test execution looks like, including example outputs and expected outcomes.

**Independent Test**: Can be fully tested by examining test documentation and verifying that:
- Test purposes are clearly documented
- Example test results are provided for each test category
- Expected outcomes are explicitly stated
- Test execution instructions are clear

### Implementation for User Story 3

- [X] T034 [US3] Enhance tests/README.md with documented purposes for each test category (unit, integration, contract)
- [X] T035 [US3] Add example test results showing successful execution for unit tests in tests/README.md
- [X] T036 [US3] Add example test results showing successful execution for integration tests in tests/README.md
- [X] T037 [US3] Add example test results showing successful execution for contract tests in tests/README.md
- [X] T038 [US3] Add expected outcomes section for each test category in tests/README.md (what each test verifies)
- [X] T039 [US3] Add common failure scenarios and their meanings to tests/README.md
- [X] T040 [US3] Add clear test execution instructions to tests/README.md (how to run tests, prerequisites, expected output format)
- [X] T041 [US3] Verify test documentation includes example outputs for all three test categories (unit, integration, contract)

**Checkpoint**: At this point, User Story 3 should be fully functional and testable independently - test documentation is comprehensive with examples

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and final validation

- [X] T042 [P] Verify all links in README.md work correctly after reorganization
- [X] T043 [P] Verify all links in docs/README.md work correctly
- [X] T044 [P] Verify all cross-references in documentation files work correctly
- [X] T045 [P] Test CI/CD workflows to ensure they reference correct script paths
- [X] T046 [P] Verify root directory structure matches target state (fewer than 10 files, only essential files)
- [X] T047 [P] Verify all documentation files are in docs/ directory with proper subdirectory organization
- [X] T048 [P] Verify all utility scripts are in scripts/ directory
- [X] T049 [P] Verify all log files are removed from git tracking and gitignored
- [X] T050 [P] Update README.md with new repository structure section showing organized layout
- [X] T051 [P] Verify technical terms are defined where first appearing in documentation
- [X] T052 [P] Run final validation checklist: root directory clean, docs organized, scripts moved, logs removed, references updated

**Checkpoint**: At this point, all polish tasks should be complete - repository reorganization is fully validated

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2)
- **Polish (Phase 6)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P1)**: Can start after Foundational (Phase 2) - Should update references before moving files, but can proceed independently
- **User Story 3 (P2)**: Can start after Foundational (Phase 2) - Completely independent, can proceed in parallel with US1 and US2

### Within Each User Story

- Reference updates before file moves (update references first, then move files)
- Directory creation before file moves
- File moves before verification
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel (T002, T003, T004)
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, User Stories 1 and 2 can start (both P1)
- User Story 3 can proceed in parallel with US1 and US2 (different files, no dependencies)
- All Polish tasks marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members after dependencies are met

---

## Parallel Example: User Story 2

```bash
# Update references and move files in parallel where possible:
Task: "Update all cross-references in README.md to point to new documentation locations"
Task: "Move OPERATIONS_RUNBOOK.md from root to docs/operations/runbook.md"
Task: "Move PRODUCTION_CHECKLIST.md from root to docs/operations/production-checklist.md"
Task: "Move TROUBLESHOOTING.md from root to docs/operations/troubleshooting.md"
Task: "Move DUPLICATE_DIAGNOSIS.md from root to docs/operations/duplicate-diagnosis.md"

# Note: Reference updates should happen BEFORE file moves to prevent broken links
```

---

## Implementation Strategy

### MVP First (User Stories 1 and 2 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Clean Repository Structure)
4. Complete Phase 4: User Story 2 (Consolidated Documentation Structure)
5. **STOP and VALIDATE**: Test both stories independently and together
6. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Repository structure clean
3. Add User Story 2 → Test independently → Documentation organized
4. Add User Story 3 → Test independently → Test documentation enhanced
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (Clean Repository Structure)
   - Developer B: User Story 2 (Consolidated Documentation Structure)
3. Once User Stories 1 and 2 are complete:
   - Developer C: User Story 3 (Enhanced Test Documentation)
4. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- **CRITICAL**: Update references BEFORE moving files to prevent broken links
- Use `git mv` for all file moves to preserve git history
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- Tests are OPTIONAL - this reorganization task does not require test tasks
- All tasks include exact file paths for clarity

---

## Task Summary

- **Total Tasks**: 52
- **Setup Tasks**: 4 (Phase 1)
- **Foundational Tasks**: 4 (Phase 2)
- **User Story 1 Tasks**: 10 (Phase 3)
- **User Story 2 Tasks**: 15 (Phase 4)
- **User Story 3 Tasks**: 8 (Phase 5)
- **Polish Tasks**: 11 (Phase 6)

- **Parallel Opportunities Identified**: 
  - Setup tasks (T002-T004)
  - Foundational reference audit tasks
  - User Story 2 documentation moves (after references updated)
  - User Story 3 test documentation enhancements
  - All polish verification tasks

- **Independent Test Criteria**:
  - **US1**: Examine repository root directory, verify no duplicates, all files in appropriate directories, root contains only essential files
  - **US2**: Examine documentation structure, verify all docs in docs/ directory, no duplicates, all links valid, technical terms defined
  - **US3**: Examine test documentation, verify purposes documented, example results provided, expected outcomes stated

- **Suggested MVP Scope**: User Stories 1 and 2 (P1 priorities) - Clean repository structure and consolidated documentation structure


