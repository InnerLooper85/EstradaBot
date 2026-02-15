# MVP 2.0 — Phase Roadmap

**Last Updated:** February 15, 2026
**Status:** Planning (phases not yet finalized)
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
| 0 | Pre-MVP 2.0 cleanup | — | NOT STARTED | 1 |
| 1 | Extended simulation options | Phase 0 | NOT STARTED | 2-3 |
| 2 | User roles & RBAC | — | NOT STARTED | 1-2 |
| 3 | Core Mapping database | Phase 2 | NOT STARTED | 2-3 |
| 4 | Days Idle & new reports | Phase 0 | BLOCKED (needs data source) | 1 |
| 5 | Schedule manipulation GUI | Phase 2 | NOT STARTED | 3-4 |
| 6 | Testing & hardening | All above | NOT STARTED | 2-3 |

---

## Phase 0: Pre-MVP 2.0 Cleanup

Finish open MVP 1.x items before starting 2.0 work:
- [ ] Automated tests (pytest framework + DES engine + API + parser tests)
- [ ] Resource utilization report
- [ ] Rubber grouping optimization (LOW — may skip)
- [ ] Role name normalization (`customer_service` → single canonical form)

---

## Phase 1: Extended Simulation Options

Add 6-day week, 10/12hr shift toggle, skeleton shifts.
**Blocked on:** Sean providing skeleton shift parameters, 10-hr shift times, 6-day config.
See `MVP_2.0_Planning.md` Section 2.2 for open questions.

---

## Phase 2: User Roles & RBAC

Full role-based access control with user management UI.
**Blocked on:** Sean confirming role permission matrix.
See `MVP_2.0_Planning.md` Section 2.5 for proposed matrix.

---

## Phase 3: Core Mapping Database

Replace Excel upload with web-editable database.
**Blocked on:** Sean defining edit permissions and whether versioning is needed.
See `MVP_2.0_Planning.md` Section 2.3.

---

## Phase 4: Days Idle & New Reports

Add "Days Idle" column and expanded alert reports.
**Blocked on:** Sean providing "Last Move Date" data source.
See `MVP_2.0_Planning.md` Section 2.1.

---

## Phase 5: Schedule Manipulation GUI

Drag-drop reordering, manual overrides, what-if simulation.
**Blocked on:** Sean defining scope (reorder only? resource reassignment?).
See `MVP_2.0_Planning.md` Section 2.4.

---

## Phase 6: Testing & Hardening

Full pytest suite, integration tests, UAT with real data, performance benchmarks.
