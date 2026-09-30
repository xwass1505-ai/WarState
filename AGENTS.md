# WAR STATE - AGENTS.md

Recommended specialised agents for an external AI coding environment.

### LEAD
Owns the plan, assigns files, merges work, updates PROJECT.md status/changelog. Only role that edits PROJECT.md status tables.

### ARCHITECT
Owns module boundaries, data schemas (Types.luau, GameConfig.EmptyCountry) and remote contracts.

### IMPLEMENTATION
Writes Luau/Python for an assigned file set. Edits only files the Lead assigned.

### CODE REVIEW
Reviews diffs for correctness, server authority and idempotency. Read-only.

### UI/UX REVIEW
Checks white + light-blue style, compactness, safe insets, mobile scaling, English-only text.

### GAMEPLAY TESTER
Runs the Studio runtime checklist and records PASS/FAIL per step.

### BUG HUNTER
Tries to break placement, saves, remotes (spam, invalid payloads, rejoin).

### DATA AUDITOR
Verifies registry (195), save schema, migrations, no doctrine fields, no granted resources.

### PERFORMANCE REVIEW
Part counts, per-frame work in PlacementController, server tick costs.

### ASSET/VISUAL REVIEW
Building variant readability/size, flag assets (only verified ids), no permanent labels.

## Coordination rules
1. The **LEAD** coordinates all changes and assigns file ownership before work starts.
2. **No two agents edit the same file concurrently.** Claim files in `.warstate/agent_locks.json`
   (`{"path": "agent-role"}`) before editing and release them afterwards. The Lead resolves conflicts.
3. Generated files are owned by `build_war_state.py`. To change them, change the generator, then rerun it.
   Hand edits to generated files are detected and never silently overwritten (use `--force` to replace; a backup is kept).
4. Review roles are read-only. They record major results in PROJECT.md under **Review log** (MANUAL block).
5. Nobody marks a feature IMPLEMENTED unless the code exists; runtime status changes only after the Studio checklist.
6. Distinguish: code exists / code compiles / Rojo builds / Studio received files / game runs / feature works.
