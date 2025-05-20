# Git Workflow

This document outlines the Git branching model, commit message conventions, Pull Request (PR) process, and release procedures for the Military Medical Exercise Patient Generator project.

## Branching Model

The project follows a structured Git branching model:

-   **`main`**: This branch represents the most stable, production-ready code. Only thoroughly tested and reviewed code from `develop` or hotfix branches is merged into `main`.
-   **`develop`**: This is the primary integration branch for ongoing development. All feature branches are merged into `develop` after successful review and testing.
-   **Feature Branches**:
    -   Format: `feature/<epic-name>/<task-name>` or `feature/TICKET-ID-short-description` (e.g., `feature/TD-001-frontend-architecture-consolidation`).
    -   Created from the `develop` branch for new features, bug fixes, or specific tasks.
    -   Each ticket in `open-tickets.md` should have an associated feature branch if work has commenced.
-   **Release Branches**:
    -   Format: `release/vX.Y.Z` (e.g., `release/v1.2.0`).
    -   Branched from `develop` when it's ready for a new release.
    -   Used for final testing, bug fixing, and preparing release-specific documentation.
    -   Once ready, merged into `main` and `develop` (to incorporate any release-specific fixes back into development).
-   **Hotfix Branches**:
    -   Format: `hotfix/<issue-id>` or `hotfix/TICKET-ID-short-description`.
    -   Branched from `main` to address critical bugs in production.
    -   Once fixed and tested, merged into both `main` and `develop`.

## Commit Message Format

Commit messages should be clear, concise, and informative.

-   **Format**: `[TICKET-ID] Brief description of changes`
    -   Example: `[TD-001] Refactor visualization component for Recharts`
    -   If no specific ticket ID applies (e.g., minor docs update), use a descriptive prefix like `DOCS` or `CHORE`.
-   **Body (Optional)**: Provide additional details in the commit body if the summary line is insufficient. Explain *what* changed and *why*.
-   **Reference Acceptance Criteria**: Where applicable, reference the specific acceptance criteria from the ticket that the commit addresses.

## Pull Request (PR) Process

1.  **Create PR**: When a feature branch is ready for review, create a Pull Request (PR) targeting the `develop` branch.
2.  **PR Title**: Should clearly describe the changes and ideally match or reference the ticket title.
3.  **PR Description**:
    -   Summarize the changes made.
    -   Link to the relevant ticket(s) in `open-tickets.md`.
    -   Explain the "why" behind the changes.
    -   List any specific testing steps performed or required.
    -   Mention any new dependencies or configuration changes.
4.  **Code Review**:
    -   At least one other developer must review the PR.
    -   Reviewers should check:
        -   Adherence to coding standards (see `.clinerules` and `memory-bank/code-patterns.md`).
        -   Fulfillment of acceptance criteria from the ticket.
        -   Presence of adequate tests for new functionality or bug fixes.
        -   Clarity and completeness of code and comments.
        -   Potential impacts on other parts of the system.
        -   Documentation updates (Memory Bank, READMEs, etc.).
5.  **Automated Checks**: Ensure any CI/CD checks (linters, tests) pass.
6.  **Addressing Feedback**: The PR author addresses any feedback from reviewers by pushing additional commits to the feature branch.
7.  **Approval**: Once reviewers are satisfied and all checks pass, the PR is approved.

## Merging

-   **Merge Strategy**: Use **Squash and Merge** when merging PRs into `develop` or `main`. This keeps the commit history clean and linear.
    -   The squashed commit message should be well-crafted, summarizing the entire set of changes from the feature branch, often using the PR title and a summary of its description.
-   **Post-Merge**:
    -   Delete the feature branch after merging.
    -   Update the status of the corresponding ticket in `open-tickets.md` (e.g., to "Ready for Review", "Completed") or move it to `closed-tickets.md`.

## Testing

-   **Unit Tests**: All new backend (Python) and frontend (TSX) code should be accompanied by unit tests.
-   **Integration Tests**: API integration tests should cover interactions between components.
-   **E2E Tests**: End-to-end tests should validate key user flows.
-   **Test Coverage**: Strive for high test coverage. Document test coverage in PRs where significant new tests are added.
-   All tests must pass before a PR can be merged.

## Release Procedure

1.  **Create Release Branch**: When `develop` has accumulated enough features and is stable, create a `release/vX.Y.Z` branch from `develop`.
2.  **Release Candidate Testing**: Perform thorough testing on the release branch. This includes regression testing, E2E tests, and user acceptance testing (UAT) if applicable.
3.  **Bug Fixing**: Any bugs found during this phase are fixed directly on the release branch.
4.  **Documentation Freeze**: Finalize all user and technical documentation for the release.
5.  **Merge to `main`**: Once the release branch is stable and approved, merge it into `main` (using a merge commit, not squash, to preserve the release branch history if desired, or squash if preferred for `main`). Tag this commit on `main` with the version number (e.g., `git tag -a v1.2.0 -m "Release version 1.2.0"`).
6.  **Merge to `develop`**: Merge the release branch back into `develop` to ensure any fixes made on the release branch are incorporated into ongoing development.
7.  **Deploy**: Deploy the tagged commit from `main` to production.
8.  **Announce**: Communicate the release to stakeholders.
