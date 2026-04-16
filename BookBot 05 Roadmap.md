# BookBot 05 Roadmap

This document outlines the planned trajectory and feature implementations for BookBot.

## Backlog (Ordered by Priority)

### 01. Code hygiene
- **Repeatable Task**: Let's not get into tech debt; check code is in good shape regularly, flagging issues for user review. Do not move this item to "Completed" until the project is retired.
- Add if missing, or update docstrings for all functions and methods.
- Add if missing, or update unit tests for all functions and methods.
- Add if missing, or update linting and code formatting.
- Add if missing, or update a README.md file and a .gitignore file to the project.
- Add if missing, or update a requirements.txt file to the project. (Note: initial version exists, but should be updated/verified).
- Add if missing, or update help text and tooltips on the frontend to inform the user of the purpose of each input box and button.
- consider refactoring to improve modularity and maintainability. add recommendations to roadmap, prefixed by `[CodeHygieneAISuggests]`.
- **Roadmap Management Protocol**: Ensure Roadmap Backlog prioritization is maintained, and append metadata strings to each item (`Added [Date]. Dependent on: X. Should be done before/after: Y`). Move finished items to the "Completed" section and append `Date completed: [Date]` to their metadata string.
*Added 29 March 2026. Dependent on: None. Should be done before: 3 since refactoring is better done before adding more Editor complexity. Should be done after: None. **(Hygiene sweeps performed: 16 April 2026: Implemented PEP 257 docstrings, full unit test suite (pytest), modular NarrativeWorkflow refactoring, and relative path discovery for portability).**

### 02. [CodeHygieneAISuggests] Refactor State Management
- **Task**: The `planning_view.py` still manages complex state transitions (like `active_chap_idx` and `active_draft`). Refactor this into a `StateController` or `SessionManager` in `src/core` to keep the UI layer purely for rendering.
- **Task**: Upgrade `Exporter` to use `pathlib` for more robust and Pythonic path operations.
*Added 16 April 2026. Dependent on: 1. Should be done after: none. **(Refactoring performed: 16 April 2026: Implemented StateController and upgraded Exporter to use pathlib).**

### 03. Complete build of third phase - fleshed out chapters

- Add agents for fleshing out chapters, critiquing chapters, and ensuring continuity between chapters.
- Add a mechanism for the user to edit the fleshed out chapters and provide feedback to the agents.
- Add a mechanism for the user to save and load - similar to check points, such that they can pause work on one book at any time and switch to another book, cleanly and without losing work.

### 04. Compare to Authorbot_04
- ask Claude to compare the features and codebase of each, and provide a report on the differences.
- ask Claude to suggest improvements to BookBot based on the comparison.
- ask Claude to suggest improvements to Authorbot_04 based on the comparison.

### 05. Complete build of fourth phase - review and edit, polish for publication
- Add agents for reviewing and editing, and polishing for publication.
- Add a mechanism for the user to edit the reviewed and edited, and polished for publication chapters and provide feedback to the agents.
- Add a mechanism for the user to save and load this phase, including all necessary context, - similar to check points, such that they can pause work on one book at any time and switch to another book, cleanly and without losing work.
- Provide either an image generation capability, or a mechanism for the user to generate (with an agent) descriptions of illustrations (including cover), and save/load these, ready to be used by an image generation tool to create the final illustrations. 
- Provide an export capability for the final book, in a format suitable for publication, or suitable for upload to kindle direct publishing (KDP) or other publishing platforms.


## Completed