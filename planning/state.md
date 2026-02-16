# MVP 2.0 — Current State

**Last Updated:** February 16, 2026

---

## Active Phase: MVP 1.11 (in progress, separate session)

## Overall Status

| Phase | Status | Notes |
|-------|--------|-------|
| Phase 0: Pre-2.0 cleanup | PARTIAL | MVP 1.8 completed role normalization, utilization report, Days Idle. 51 automated tests in place. |
| Phase 1: Extended simulation | DONE | MVP 1.9 — skeleton shifts, 6-day weeks, per-day config, custom scenario builder. |
| Phase 2: User roles & RBAC | DONE | MVP 1.10 — GCS-backed user store, admin management page, self-service password change, operator role, soft-delete. |
| Phase 3: Core Mapping view | DONE | MVP 1.10 — Read-only Core Mapping page with mismatch detection. Editable DB deferred to 2.0. |
| Phase 4: Schedule Reorder | DONE | MVP 1.10 — SortableJS drag-and-drop, cross-BLAST, GCS persistence, Excel export integration, regeneration warning. |
| Phase 5: Days Idle | BLOCKED | Waiting on "Last Move Date" data source |
| Phase 6: Testing | IN PROGRESS | 51 tests passing (alerts, API endpoints, DES scheduler). More coverage with each release. |

## MVP 1.10 Design Decisions (for reference)

These decisions were confirmed by Sean during the 1.10 planning session:

- **Password change:** Self-service with current password confirmation
- **User deletion:** Soft delete (disable/enable), not hard delete
- **New roles:** Added `operator` for shop floor users
- **Core Mapping access:** Admin + MfgEng + Planner
- **Core mismatch display:** Summary count bar + highlighted rows
- **Reorder scope:** Cross-BLAST movement allowed
- **Reorder persistence:** Warn on regenerate (planner chooses keep/discard)
- **Reorder effect:** Changes actual BLAST sequence (reflected in exports)

## Blockers for Sean

1. Provide "Last Move Date" data source for Days Idle
2. Define MVP 1.11 scope (or confirm what the other session is building)

## Session Log

| Date | Session | What happened |
|------|---------|---------------|
| Feb 15, 2026 | Planning setup | Created planning directory structure, roadmap, state tracking |
| Feb 15, 2026 | MVP 1.9 design | Deglazed implementation plan. Approved: Mon-Sat grid, per-day full/skeleton, takt in minutes, 6day_12h preset, advanced config panel (single custom run), CURE/QUENCH treat skeleton as working days. |
| Feb 16, 2026 | MVP 1.10 build | Implemented all 3 features: RBAC/User Management, Core Mapping view, Schedule Reorder. 51 tests pass. Merged to master, deployed. |
