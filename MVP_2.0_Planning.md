# EstradaBot — MVP 2.0 Planning Document

**Document Version:** 2.0
**Date:** February 15, 2026
**Status:** Planning
**Prerequisites:** Complete remaining MVP 1.x backlog items (see Section 4)

---

## 1. Overview

MVP 2.0 represents the next major evolution of EstradaBot. The scope has been redefined (Feb 15, 2026) around two flagship features:

1. **Rotors Product Line** — Add a second manufacturing department with its own staffing, machines, and scheduling logic, sharing the existing UI framework and feature set.
2. **Customer-Facing Reports & Quoting System** — Enable sales agents and customer service reps to generate customer-shareable reports and create quotes that temporarily reserve production capacity.

Plus two carryover items from the original MVP 2.0 plan:

3. **Full Schedule Manipulation GUI** — Drag-drop reordering, resource reassignment, manual overrides.
4. **Core Mapping Editable Database** — Replace Excel upload with a web-editable database.

---

## 2. Feature Specifications

### 2.1 Rotors Product Line (Department #2)

**Requirement:** Add Rotors as a separate department alongside the existing Stators department. Each department has its own:
- Staffing model (headcount, shifts, roles)
- Machine set (different equipment types and counts)
- Scheduling logic and constraints (different takt times, process steps, priorities)
- Input data (separate or combined Sales Order / Shop Dispatch files)

The two departments share:
- The same web UI framework (navigation, layout, page structure)
- The same feature set (simulation, planner workflow, special requests, reports, etc.)
- The same user accounts and role-based access
- The same deployment and infrastructure

**Architecture Implications:**
- The DES engine (`des_scheduler.py`) must become **department-aware** — either parameterized per department or split into department-specific subclasses with a shared base.
- Data models, parsers, and exporters need to handle department context (which department does this order belong to?).
- The UI needs a **department selector** or **department-scoped views** — user picks Stators or Rotors, and all pages reflect that context.
- GCS storage paths should be department-scoped (e.g., `gs://estradabot-files/stators/`, `gs://estradabot-files/rotors/`).
- Configuration (machines, takt times, shift patterns) must be per-department rather than global.

**Open Questions for Product Owner:**
- [ ] What machines does Rotors use? How many of each?
- [ ] What are the Rotor process steps / station sequence?
- [ ] What are Rotor takt times per station?
- [ ] Does Rotors use the same shift patterns as Stators, or different?
- [ ] Does Rotors have the same priority system (5-tier BLAST)?
- [ ] Are Sales Orders and Shop Dispatch reports shared between departments, or separate files?
- [ ] Is there cross-department resource sharing (e.g., shared staff or machines)?
- [ ] Should dashboards show both departments or one at a time?

---

### 2.2 Customer-Facing Reports & Quoting System

**Requirement:** Sales agents and customer service reps can:
1. **Generate customer-shareable reports** — filtered views of the schedule relevant to a specific customer, formatted for external sharing (PDF or Excel).
2. **Create quotes for new orders** — enter prospective order details and get an estimated production slot / delivery date.
3. **Reserve production capacity** — accepted quotes place **temporary holds** on production slots, preventing overbooking.
4. **Auto-release expired quotes** — when a quote expires without converting to a real order, the held capacity is released back to the pool.

**Architecture Implications:**
- The scheduling engine needs a concept of **provisional entries** — orders that reserve capacity but aren't confirmed. These must be distinguishable from real orders.
- Quote lifecycle: `draft` → `sent` → `accepted` (hold placed) → `converted` (becomes real order) or `expired` (hold released).
- Need a quote expiry mechanism — either a background job or checked on each schedule run.
- Customer reports need a **customer filter** — show only orders for a specific customer, with appropriate detail level (no internal notes, no other customers' data).
- Report generation needs a **presentable export format** — likely branded PDF or clean Excel.
- Role access: Sales agents and CS reps can create quotes and generate reports. Planners can see all quotes. Admins manage quote settings (default expiry period, etc.).

**Open Questions for Product Owner:**
- [ ] What information should appear on customer-facing reports? (Order #, product, estimated dates, status — what else?)
- [ ] What's the default quote expiry period? (e.g., 7 days, 14 days, 30 days?)
- [ ] Can a quote hold capacity across multiple machines/dates, or is it always a single slot?
- [ ] Should quotes be visible on the main schedule view (e.g., shown in a different color)?
- [ ] Do quotes need approval from a planner before the hold is placed, or can CS/sales reserve directly?
- [ ] Should there be a limit on how much capacity can be held by quotes at any time?
- [ ] What format for customer reports — PDF, Excel, or both?
- [ ] Should customers be able to view their reports online (customer portal), or is it email/download only?

---

### 2.3 Full Schedule Manipulation GUI

**Requirement:** Allow the planner to modify the schedule via a graphical interface:
- Drag-and-drop reordering of orders within the schedule
- Resource reassignment (move an order to a different machine or time slot)
- Manual priority overrides that persist across schedule regenerations
- "Reset to Algorithm" to revert manual changes
- Visual distinction between algorithm-placed and manually-adjusted orders

**Access:** Only planners can save changes. Other roles (CS) can simulate what-if scenarios without saving.

**Technical Notes:**
- Frontend: SortableJS or HTML5 drag-and-drop
- Backend: Manual overrides stored as pinned positions that the DES engine respects
- Re-simulation on change (background, with optimistic UI)

**Open Questions for Product Owner:**
- [ ] Scope: reorder only, or also reassign machines/resources?
- [ ] Should CS have simulation/what-if drag-drop access?
- [ ] How should pinned orders interact with new data uploads? (Stay pinned? Warn and ask?)

---

### 2.4 Core Mapping Editable Database

**Requirement:** Replace the Core Mapping Excel upload with a persistent, web-editable database. Manufacturing Engineering users can add, edit, and deactivate core mappings directly in the browser.

**Approach (decided Feb 15):**
- MVP 1.x delivers a **read-only web view** of the current Core Mapping data.
- MVP 2.0 adds **edit capability** backed by a database.
- Database technology decision deferred until implementation.

**Open Questions for Product Owner:**
- [ ] Which fields should be editable vs. read-only?
- [ ] Should changes require approval, or is direct edit OK for MfgEng role?
- [ ] Is version history / audit log needed?
- [ ] Should bulk import from Excel still be supported alongside the editor?

---

## 3. Proposed Implementation Sequence

| Phase | Focus | Dependencies |
|-------|-------|-------------|
| Phase 1: Multi-Department Architecture | Refactor DES engine, data models, parsers, and UI to be department-aware. Stators continues working as-is. | None — foundational work |
| Phase 2: Rotors Integration | Implement Rotor-specific scheduling logic, machines, takt times. Add Rotor parsers and config. | Phase 1 |
| Phase 3: Customer Reports | Customer-filtered schedule views, PDF/Excel export for external sharing. | None (can parallel with Phase 1-2) |
| Phase 4: Quoting System | Quote creation, capacity holds, expiry, conversion to real orders. | Phase 2 (needs working multi-dept scheduler) |
| Phase 5: Schedule Manipulation GUI | Drag-drop reorder, resource reassignment, manual overrides. | Phase 2 (needs stable scheduler) |
| Phase 6: Core Mapping Database | Persistent editable storage, web editor UI, migration from Excel. | None (can parallel) |
| Phase 7: Testing & Refinement | End-to-end testing, UAT, performance tuning. | All phases |

**Parallelization opportunities:**
- Phases 3 and 6 can run in parallel with Phases 1-2.
- Phase 5 can begin frontend work during Phase 2.

---

## 4. MVP 1.x Backlog (Prerequisites for 2.0)

These items were moved from the original MVP 2.0 plan to 1.x during the Feb 15, 2026 roadmap replanning:

| Item | Priority | Notes |
|------|----------|-------|
| Resource utilization report | MEDIUM | MVP 1.8 target |
| Role name normalization | MEDIUM | Fix `customer_service` vs `customerservice` |
| Extended simulation (6-day, skeleton shifts) | HIGH | Skeleton = takt time adjustment; user configures per-day |
| RBAC / user management | MEDIUM | Role matrix deferred |
| Core Mapping: read-only web view | MEDIUM | Precursor to 2.0 editable database |
| Days Idle column | MEDIUM | From Shop Dispatch "Elapsed Days"; 9999→0 rule |
| Basic schedule reorder | MEDIUM | Simple priority adjustment (precursor to full GUI) |
| Rubber grouping optimization | LOW | Changeover minimization |

### Skeleton Shift Details (for Extended Simulation)
- Not reduced machines — it's a **takt time adjustment** (all machines available, fewer staff = longer takt)
- User enters expected takt time for skeleton crew
- User picks: day shift, night shift, or both
- Any day configurable as full or skeleton
- 6th day (Saturday) — user chooses full or skeleton

---

## 5. Technical Architecture Considerations

### 5.1 Multi-Department Data Model
The biggest architectural change is making everything department-aware:
- **DES Engine:** Parameterized by department config (machines, takt times, stations, priorities)
- **Parsers:** Department-tagged input data (or separate parsers per department)
- **Storage:** Department-scoped GCS paths
- **UI:** Department selector in nav, all views filtered by active department
- **Config:** Per-department settings (shift patterns, machine counts, takt times)

### 5.2 Database Addition
MVP 2.0 will require a database for:
- Core Mapping storage (editable)
- Quote management (lifecycle, capacity holds)
- User management (if RBAC moves to 2.0 scope)
- Audit logging

**Options (decision deferred):**
- SQLite (simple, no server needed)
- PostgreSQL via Cloud SQL (scalable, managed, adds cost)
- GCS JSON files (lightweight, limited querying)

### 5.3 Quote Capacity Model
Quotes introduce "soft" capacity reservations:
- The scheduler must account for held capacity when estimating delivery dates
- Expired quotes must release capacity (checked on schedule generation or via background job)
- Need to prevent overbooking: total real orders + active quote holds ≤ capacity

### 5.4 Customer Report Generation
- PDF generation: WeasyPrint, ReportLab, or wkhtmltopdf
- Excel generation: existing openpyxl infrastructure
- Customer data filtering: strict isolation — never leak other customers' data
- Branding: configurable header/logo for customer-facing documents

### 5.5 Frontend Evolution
The current Jinja2 + jQuery stack can handle most MVP 2.0 features:
- Department selector: simple nav dropdown
- Drag-drop: SortableJS library
- Quote management: standard CRUD forms
- Customer reports: server-side generation + download

A full frontend framework rewrite is not needed at this stage.

---

## 6. Items Deferred Beyond MVP 2.0

| Item | Target | Notes |
|------|--------|-------|
| Dual-Cylinder Mode Recommendation | MVP 3.0+ | Very low priority |
| Live SAP data integration | MVP 3.0+ | Requires SAP API access |
| Customer self-service portal | MVP 3.0+ | Customers view their own reports online |

---

**Document End**
