# BookBot 05 Roadmap

This document outlines the planned trajectory and feature implementations for BookBot.

## Backlog (Ordered by Priority)

### 01. Code hygiene
- **Repeatable Task**: Let's not get into tech debt; check code is in good shape regularly.
- Add if missing, or update docstrings for all functions and methods.
- Add if missing, or update unit tests for all functions and methods.
- Add if missing, or update linting and code formatting.
- **[CodeHygieneAISuggests]**: Implement an "Undo" stack for the Chapter Registry to prevent accidental data loss during manual edits.
- **[CodeHygieneAISuggests]**: Add a "Global Story Bible" export that compiles all continuity memos into one world-building document.
- **Roadmap Management Protocol**: Ensure Roadmap Backlog prioritization is maintained.

### 02. Compare to Authorbot_04
- ask Claude to compare the features and codebase of each, and provide a report on the differences.
- ask Claude to suggest improvements to BookBot based on the comparison.

### 03. Complete build of fifth phase - image generation
- Provide either an image generation capability, or a mechanism for generating illustration descriptions.
- Save/load illustration context for covers and interior art.

### 04. Complete build of sixth phase - publication export
- Provide an export capability suitable for KDP (Kindle Direct Publishing) or other platforms.
- Support PDF/EPUB formatting logic.

### 10. break the code apart into simple building blocks, heavily commented
- start with agent instructions and ensure whatever they return is trimmed at </thinking> 
- don't use ai instruction, use a frickin' find and trim
- design docs should line up to code (ask claude to check) 
- make a doc for the architecture (mermaid?)

## Completed

### 05. add a phase 1 agents - 01a_brainstormer, 01b_continuity_expert
- 01a takes thoughts and expands detail. Constraints (5-15 main chars).
- 01b checks for inconsistencies.
- *Date completed: 18 April 2026. Added 18 April 2026.*

### 06. Complete build of fourth phase - NarrativeEngine
- Add agents for full prose generation (04a), critiquing (04b), and continuity (04c).
- Sequential drafting with "Prose Bridges" (last 1,000 words) and "Continuity Memos".
- *Date completed: 18 April 2026. Added 18 April 2026.*

### 07. Complete build of third phase - fleshed out chapters
- Add agents for chapter detailing (03a) and impact analysis (03b).
- Mechanism for user editing and feedback.
- *Date completed: 18 April 2026. Added 29 March 2026.*

### 08. [CodeHygieneAISuggests] Refactor State Management
- Refactored `planning_view.py` state transitions into a `StateController`.
- Upgraded `Exporter` to use `pathlib`.
- *Date completed: 16 April 2026. Added 16 April 2026.*

### 09. General Code Hygiene Pass
- Full PEP 257 docstring and type hint pass for 4-Phase architecture.
- Full UI Guidance pass (Help tooltips and "Learn More" boxes for all phases).
- *Date completed: 18 April 2026.*