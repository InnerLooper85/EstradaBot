# MVP 2.0 — Phase Roadmap

**Last Updated:** March 30, 2026
**Status:** MVP 2.0 phases mostly complete — see status below
**Source:** `MVP_2.0_Planning.md` (requirements and open questions)

---

## How This Works

Each phase gets its own file in this directory with three sections:
1. **Plan** — what to build, acceptance criteria, files affected
2. **Execution** — work log as it happens (updated during build)
3. **Verification** — how to confirm the phase is done (manual tests, checks)

Claude loads only the current phase's file during a session, keeping context lean.
State is tracked in `state.md` so new sessions can pick up where the last left off.

---

## Phases (Draft — Needs Sean's Review)

| # | Phase | Depends On | Status | Est. Sessions |
|---|-------|-----------|--------|---------------|
| 0 | Pre-MVP 2.0 cleanup | — | PARTIAL | 1 |
| 1 | Extended simulation options | Phase 0 | DONE | 2-3 |
| 2 | User roles & RBAC | — | DONE | 1-2 |
| 3 | Core Mapping view | Phase 2 | DONE | 2-3 |
| 4 | Schedule Reorder | Phase 2 | DONE | 3-4 |
| 5 | Days Idle & new reports | Phase 0 | BLOCKED (needs data source) | 1 |
| 6 | Testing & hardening | All above | IN PROGRESS | 2-3 |

---

## Phase 0: Pre-MVP 2.0 Cleanup

Open items (MVP 1.x cleanup):
- [x] Automated tests (pytest framework + DES engine + API + parser tests) — 51 tests passing
- [x] Resource utilization report
- [x] Role name normalization (`customer_service` → single canonical form)
- [ ] Rubber grouping optimization (LOW — may skip)

---

## Phase 1: Extended Simulation Options (MVP 1.9)

Add 6-day week, 10/12hr shift toggle, skeleton shifts.
- [x] Per-day full/skeleton shift configuration
- [x] 6-day work week support with Mon-Sat grid
- [x] Scenario builder (4d/10h, 4d/12h, 5d/12h presets)
- [x] Takt time in minutes for flexibility

---

## Phase 2: User Roles & RBAC (MVP 1.10)

Full role-based access control with user management UI.
- [x] GCS-backed user store
- [x] Admin user management page
- [x] Self-service password change
- [x] Operator role for shop floor users
- [x] Soft-delete (disable/enable) instead of hard delete

---

## Phase 3: Core Mapping View (MVP 1.10)

Read-only Core Mapping page with mismatch detection.
- [x] DataTable with part-to-core mapping
- [x] Core inventory view
- [x] Mismatch highlighting (summary bar + row highlights)
- [ ] Editable database (deferred to MVP 2.0)

---

## Phase 4: Schedule Reorder (MVP 1.10)

Drag-drop reordering, cross-BLAST movement, GCS persistence.
- [x] SortableJS drag-and-drop UI
- [x] Reorder API endpoints (save, delete, status)
- [x] BLAST sequence recalculation
- [x] Excel export integration
- [x] Regeneration warning (keep/discard dialog)

---

## Phase 5: Days Idle & New Reports

Add "Days Idle" column and expanded alert reports.
**Blocked on:** Sean providing "Last Move Date" data source.

---

## Phase 6: Testing & Hardening

Full pytest suite, integration tests, UAT with real data, performance benchmarks.
- [x] 51 automated tests in place
- [ ] Additional coverage with each release
- [ ] Integration tests with real data
- [ ] Performance benchmarks
