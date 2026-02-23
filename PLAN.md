# Plan for Review and Improvement

This document outlines recommended actions to audit, refine and bring the Newspaper Downloader project into a robust, maintainable state. It is intended to be a living artifact that evolves as we implement changes.

1) Current state snapshot
- Language/stack: Python 3.x, PySide6 (GUI), requests, BeautifulSoup, PyPDF2, PyInstaller in requirements.
- Structure: a modular downloader system with a base downloader and per-paper implementations; a GUI layer; a config system with a singleton config object; CLI entry at root and tests that exercise downloaders.
- Versioning: The repository is not currently a Git working tree (per environment note). There is a .gitignore and sample config/build artifacts in the tree.
- Documentation: README contains a broad overview and build steps; docs folder contains architecture and MVP specs.

2) Observations and potential gaps (high level)
- Inconsistent config: DEFAULT_CONFIG in code vs config.json in repo. This can cause confusion when new developers rely on defaults before custom config files are loaded.
- Version control: No git repo initialized. This makes collaboration, history and branching brittle. A Git workflow will help track changes from plan to build.
- Tests: Tests exist but rely on live network calls. That reduces reliability and makes CI brittle. Needs mocked tests and a standalone test harness.
- Logging: A logger utility exists but the code paths shown primarily emit GUI/log signals. Centralized file-based logging could be strengthened to aid debugging and audits.
- Code hygiene: Some modules import utilities (e.g., logger) but do not consistently consume them; there are compiled artefacts in the tree (build/, dist/, __pycache__) that should be ignored or cleaned in a VCS workflow.
- API surface / coupling: The downloader modules share a lot of logic but implement bespoke HTML parsing. Consider consolidating common pieces and introducing more tests around edge cases (missing pages, HTML structure changes).
- Documentation: A Plan.md would help align stakeholders; consider a lightweight developer guide and contribution guidelines.

3) Proposed plan options
Option 1: Quick wins (Plan A) – get repo into a solid ready-to-build state
- Initialize a Git repository with a standard .gitignore (already present) and a README that documents how to run tests, build and run the app.
- Add PLAN.md (this file) detailing goals and milestones.
- Align config defaults: unify DEFAULT_CONFIG with config.json; ensure all papers declared in config.json exist in code and tests.
- Introduce a small test harness using pytest with mocks to exercise downloader interfaces without real network calls.
- Wire up a basic CI workflow (GitHub Actions) to run unit tests on push/PR.
- Create a minimal but explicit set of unit tests for the core Base class and a couple of downloader edge cases.
- Add a lightweight logging pathway to persist logs to a file for traceability.

Option 2: Robust architecture (Plan B) – seed for future multi-source, parallel downloads
- Define a clear component diagram in docs (textual or simple diagram) showing Plan, Downloader, Storage, GUI, and API boundary.
- Extract common parsing utilities into a shared module; promote a single strategy for image vs PDF processing.
- Ensure thread-safety and cancellation semantics across DownloadWorker and BatchDownloadWorker; integrate cancellation with UI reliably.
- Introduce versioned API contracts for downloader interfaces and their EditionInfo data structure; add type hints across public APIs.
- Build a lightweight integration test that uses a fake HTTP server (e.g., httpx/mock) to simulate a paper layout and image URLs.

Option 3: Hybrid approach (Recommended default) – start with Plan A, pick key elements from Plan B as milestones
- Combine the quick wins (plan hygiene, tests with mocks, CI) with a gradual introduction of an architecture roadmap (shared parsing utilities, contracts, improved docs).

4) Deliverables and milestones (illustrative)
- M1: Initialize git repo, add PLAN.md, ensure config alignment, add basic unit tests with mocks, add CI.
- M2: Refactor common downloader helpers, tighten typing, introduce EditionInfo contracts, run full test suite.
- M3: Add logging to file and enhance error handling; ensure CLI and GUI share a common run path and error codes.
- M4: Prepare packaging scripts (PyInstaller spec) and a baseline release workflow.

5) Suggested next actions (executive)
- Confirm which plan option you prefer (Plan A, Plan B, or a hybrid).
- If Plan A is acceptable, I will start by adding PLAN.md, syncing config defaults, and wiring up a pytest-based test suite with mocks. Then I will propose a CI workflow.
- If you want Plan B immediately, I will draft a more formal architecture document and begin refactoring toward modular utilities and a contract-driven downloader interface.

6) Risks and mitigations
- Risk: Changing config shapes could break existing behavior. Mitigation: introduce a config compatibility layer and document default behavior in PLAN.md.
- Risk: Tests depend on network; mitigation: use pytest mocks and a local fixture-based test server.
- Risk: GUI logic tightly coupled with downloader; mitigation: define clear interfaces and isolate business logic from UI code.

7) Concluding remark
- The project shows solid structure and thoughtful design. A structured plan and version-control onboarding will help accelerate safe, scalable progress from plan to build.

If you want, I can push the first concrete steps now (Plan A) by generating a small patch that adds PLAN.md, a minimal CONTRIBUTING.md, and a skeleton for a PyTest-based tests directory. Once you choose the option, I’ll proceed with the next patch.
