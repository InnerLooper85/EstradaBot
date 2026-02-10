# EstradaBot — MVP 2.0 Planning Document

**Document Version:** 1.0
**Date:** February 4, 2026
**Status:** Early Planning
**Prerequisites:** Complete MVP 1.1 (all high-priority user feedback) and remaining MVP 1.0 implementation plan items

---

## 1. Overview

MVP 2.0 represents the next major evolution of EstradaBot. It focuses on:
- Expanded schedule simulation options
- User role-based permissions and workflows
- Replacing static file uploads with editable databases
- GUI-based schedule manipulation
- Live data integration

MVP 2.0 development should begin after:
1. All MVP 1.1 items (Phase 8 in the implementation plan) are complete
2. Remaining MVP 1.0 items are complete (rubber grouping optimization, resource utilization reports, alert reports, automated tests)

---

## 2. Deferred User Feedback Items

These items were identified during the February 4, 2026 feedback session and classified as low priority / MVP 2.0.

---

### 2.1 Days Idle Column (Customer Service Request)

**Requirement:** Add a "Days Idle" column between "Turnaround" and "Status" on the schedule page.

**Definition:** Days Idle = Days since the order's last physical movement in the shop.

**Dependencies / To-Do for Product Owner:**
- [ ] **Sean:** Provide the "Last Move Date" data field. Determine which SAP report contains this data and the exact column name.
- [ ] **Sean:** Clarify if "Last Move Date" should come from a new uploaded report, be added to the existing Sales Order report, or pulled from a live data feed.

**Clarifying Questions from Claude:**
1. Is "Last Move Date" the date the order last changed work centers in SAP? Or the last date any activity was recorded?
2. Should "Days Idle" be calculated as `Today - Last Move Date` (real-time) or `Schedule Generation Date - Last Move Date` (snapshot)?
3. Should orders with 0 days idle (recently moved) be visually distinguished from stale orders?
4. Is there a threshold for "too idle" that should trigger an alert? (e.g., > 5 days idle = warning)

**Technical Notes:**
- This will require either a new parser for the data source or an additional column in an existing uploaded report
- The schedule page DataTable will need a new column
- Consider adding an "Idle" alert report alongside existing Promise Risk and Core Shortage alerts

---

### 2.2 Extended Schedule Simulation Options

**Requirement:** Allow users to simulate more scheduling configurations beyond the MVP 1.1 4/5 day toggle.

**Options to Support:**

| Option | Values | Notes |
|--------|--------|-------|
| Work days per week | 4, 5, or 6 days | MVP 1.1 supports 4 and 5 |
| Shift length | 10 or 12 hours | Currently hardcoded to 12 |
| Number of shifts | 1 or 2 | Currently hardcoded to 2 |
| Skeleton shifts | Custom configuration | Minimal crew, constrained core subset |

**Skeleton Shift Definition:**
- Minimal crew brought in (likely 1 shift, reduced machine availability)
- Only certain cores/products run during skeleton shifts
- Needs UI for selecting which cores or product families to include
- Typical use case: weekend or holiday partial operation

**Clarifying Questions from Claude:**
1. For 10-hour shifts, what would the start/end times be? (e.g., 5:00 AM - 3:00 PM, 5:00 PM - 3:00 AM?)
2. For a 6-day week, is the 6th day Saturday? Should it have the same shift configuration as weekdays?
3. For single-shift operation, which shift is kept — day shift only?
4. For skeleton shifts:
   - How many machines would be available? (e.g., 2 of 5 Desma machines?)
   - Which stations would be staffed?
   - Should skeleton shifts be schedulable on specific days (e.g., "run skeleton on Fridays and Saturdays")?
   - How would the user select which cores/products to run?
5. Should users be able to combine options freely? (e.g., 6-day week + 10-hour shifts + skeleton shift on Saturday)
6. How many pre-generated simulation variants is practical? With all combinations, this could be 12+ variants.

**Technical Notes:**
- The `WorkScheduleConfig` class in `des_scheduler.py` will need to be fully parameterized
- Consider creating a "Schedule Configuration" page where users define simulation parameters
- Pre-generating all combinations may be too slow; consider on-demand generation with caching
- The toggle UI from MVP 1.1 will need to expand to support multiple options (possibly a configuration panel rather than simple toggle)

---

### 2.3 Replace Core Mapping Excel with Editable Database

**Requirement:** Replace the Core Mapping Excel upload with a database that can be manipulated by users with appropriate rights (Manufacturing Engineering role).

**Clarifying Questions from Claude:**
1. Should this be a web-based UI where users can add/edit/delete core mappings directly on the site?
2. Should there be an approval workflow for changes? (e.g., MfgEng proposes change, Admin approves)
3. Should historical versions be tracked? (e.g., "Core 427 changed from HR to XE rubber on 2/15/2026")
4. Should bulk import from Excel still be supported alongside the database editor?
5. What about the Core Inventory sheet — should that also become editable via the web UI?
6. Who should be able to add new cores vs. edit existing ones vs. delete/deactivate cores?

**Technical Notes:**
- This will likely require adding a database (SQLite or PostgreSQL) to the architecture
- Currently the system is stateless (file-based storage via GCS) — adding a database is a significant architectural change
- Alternative: Use GCS-stored JSON as a lightweight "database" with a web editor UI, avoiding a full database
- Need to consider data migration from current Excel format
- Will need audit logging for all changes

**To-Do for Product Owner:**
- [ ] **Sean:** Define which fields in the Core Mapping should be editable vs. read-only
- [ ] **Sean:** Define the Manufacturing Engineering role permissions (what can they edit, what needs approval?)
- [ ] **Sean:** Decide if historical versioning is needed or if simple edit-in-place is sufficient

---

### 2.4 GUI-Based Schedule Manipulation

**Requirement:** Allow the planner to modify the schedule via a GUI on the site (dragging orders up/down, individually reprioritize specific orders, etc.). Only the planner can lock these changes in; other users can simulate but not save.

**Clarifying Questions from Claude:**
1. When the planner drags an order to a new position, should the entire schedule be re-simulated with the new ordering, or should only the moved order's times change?
2. Should there be an "undo" capability for manual changes?
3. Should manually repositioned orders be visually marked as "manually adjusted" vs. "algorithm-placed"?
4. Should there be a "Reset to Algorithm" button to revert all manual changes?
5. How should manual overrides interact with future schedule regenerations? (i.e., if the planner pins Order A to position 3, does it stay there when new data is uploaded and schedule is regenerated?)
6. Should other roles (Customer Service) be able to simulate drag/drop changes without saving? This would support "what-if" analysis.
7. What level of granularity — can the planner only reorder within the BLAST sequence, or can they also reassign cores, change Desma machines, etc.?

**Technical Notes:**
- Frontend: Will need a drag-and-drop library (e.g., SortableJS, or HTML5 drag-and-drop API)
- Backend: Need to support "manual overrides" concept — orders with fixed positions that the algorithm respects
- Performance: Re-simulating the full schedule on every drag event may be too slow; consider optimistic UI updates with background re-simulation
- State management: Need to distinguish between algorithm-generated and manually-adjusted schedules

**To-Do for Product Owner:**
- [ ] **Sean:** Decide on the scope of manual manipulation (reorder only? reassign resources? both?)
- [ ] **Sean:** Decide if Customer Service should have simulation/what-if drag-drop access

---

### 2.5 User Group Role Definitions

**Requirement:** Fully define user group responsibilities and rights for all roles.

**Proposed Role Matrix (from User Feedback):**

| Capability | Admin | Planner | Customer Service | Mfg Engineering | Operator/Guest |
|------------|-------|---------|-----------------|-----------------|----------------|
| Upload Sales Order / Shop Dispatch | Yes | Yes | No | No | No |
| Upload Hot List | Yes | Yes | Yes | No | No |
| Upload Core Mapping / Process Map | Yes | No | No | Yes | No |
| Generate Schedule | Yes | Yes | No | No | No |
| Publish Schedule | Yes | Yes | No | No | No |
| View Published Schedule | Yes | Yes | Yes | Yes | Yes |
| Simulate Schedule (personal) | Yes | Yes | Yes | No | No |
| Download Reports | Yes | Yes | Yes (limited) | No | No |
| Make Hot List Requests | No | No | Yes | No | No |
| Simulate Impact Analysis | Yes | Yes | Yes | No | No |
| Request Priority Override (FIFO bypass) | No | No | Yes | No | No |
| Edit Core Mapping Database | Yes | No | No | Yes | No |
| Request Engineering Work Orders | No | No | No | Yes | No |
| View BLAST/Core Schedules | Yes | Yes | Yes | Yes | Yes |
| Manage Users | Yes | No | No | No | No |
| Submit User Feedback | Yes | Yes | Yes | Yes | Yes |

**Clarifying Questions from Claude:**
1. Are "Hot List Requests" different from uploading a Hot List file? Is this a request workflow where CS submits a request and the Planner approves it?
2. For "Request Priority Override" — does this mean Customer Service can request that a specific customer's orders bypass FIFO? How does the Planner approve/deny this?
3. For "Engineering Work Orders" — these only appear on the Shop Dispatch report, not the main schedule. Should the system have a separate view for engineering work orders?
4. Should there be a notification system when requests are made? (e.g., CS submits a hot list request → Planner gets a notification)
5. The current system uses environment variables for user management. For MVP 2.0, should we move to a database-backed user management system with a web UI for creating/managing users?

**Technical Notes:**
- Current auth system is simple (env vars, two roles: admin/user). MVP 2.0 needs full RBAC.
- Options: Flask-Security, Flask-Principal, or custom middleware
- User management UI will be needed (admin page to add/edit/delete users and assign roles)
- Consider using Flask sessions or JWT for more granular permission checking

**To-Do for Product Owner:**
- [ ] **Sean:** Confirm the role matrix above or provide corrections
- [ ] **Sean:** Define the hot list request workflow (is it a form submission? Does it require approval?)
- [ ] **Sean:** Define the priority override workflow
- [ ] **Sean:** Define the engineering work order workflow
- [ ] **Sean:** Decide on notification preferences (email, in-app, both?)

---

### 2.6 Additional MVP 2.0 Items (from Original Implementation Plan)

These were in the original plan but not yet implemented:

| Item | Original Phase | Status |
|------|---------------|--------|
| Rubber Grouping Optimization (changeover minimization) | Phase 3 | Not implemented |
| Dual-Cylinder Mode Recommendation | Phase 3 | Not implemented |
| Resource Utilization Report | Phase 6 | Not implemented |
| Promise Date Risk Alert Report | Phase 6 | Not implemented |
| Core Shortage Alert Report | Phase 6 | Not implemented |
| Machine Utilization Alert Report | Phase 6 | Not implemented |
| Automated Unit Tests | Phase 7 | Not implemented |
| Automated Integration Tests | Phase 7 | Not implemented |

**Note:** Some of these (rubber grouping, reports, tests) may be completed as part of MVP 1.x iterations before MVP 2.0 begins. They are listed here for completeness.

---

## 3. MVP 2.0 To-Do List for Product Owner (Sean)

| # | Item | Priority | Notes |
|---|------|----------|-------|
| 1 | Provide "Last Move Date" data source for Days Idle column | High | Which SAP report? Column name? |
| 2 | Define skeleton shift parameters | Medium | How many machines, which stations, which days? |
| 3 | Define 10-hour shift start/end times | Medium | e.g., 5:00 AM - 3:00 PM? |
| 4 | Define 6-day week configuration | Medium | Is Saturday the 6th day? Same shifts? |
| 5 | Define Core Mapping database edit permissions | Medium | What's editable, who approves? |
| 6 | Define schedule manipulation scope | Medium | Reorder only, or resource reassignment too? |
| 7 | Confirm user role permission matrix | High | See Section 2.5 table |
| 8 | Define hot list request workflow | Medium | Form → approval? Notifications? |
| 9 | Define priority override workflow | Medium | CS requests → Planner approves? |
| 10 | Define engineering work order workflow | Low | Separate view? Who creates? |
| 11 | Decide on notification system | Low | Email, in-app, both? |
| 12 | Decide on user management approach | Medium | Database-backed? Web UI? |

---

## 4. Technical Architecture Considerations for MVP 2.0

### 4.1 Database Addition
MVP 2.0 will likely require a database for:
- User management (roles, permissions)
- Core Mapping storage (editable)
- Schedule history and versions
- Feedback and request tracking
- Audit logging

**Options:**
- SQLite (simple, no server needed, good for small teams)
- PostgreSQL via Cloud SQL (scalable, managed, adds cost)
- GCS JSON files (lightweight, no database server, limited querying)

### 4.2 Frontend Evolution
The current server-rendered Jinja2 + jQuery approach may become limiting with:
- Drag-and-drop schedule manipulation
- Complex multi-option simulation UI
- Real-time notification system
- Editable database tables

**Options:**
- Continue with jQuery + enhanced DataTables (simplest, most incremental)
- Add Vue.js or React for interactive components only (hybrid approach)
- Full frontend rewrite to React/Vue (most capable, highest effort)

### 4.3 API Evolution
Current API is minimal. MVP 2.0 will need:
- RESTful endpoints for CRUD operations on Core Mapping
- WebSocket or polling for notifications
- Role-based API authorization middleware
- Pagination for large datasets

---

## 5. Estimated Timeline

| Phase | Duration | Content |
|-------|----------|---------|
| Planning & Design | 2-3 weeks | Finalize requirements, answer clarifying questions, design architecture |
| User Roles & Auth | 1-2 weeks | RBAC system, user management UI |
| Extended Simulations | 2-3 weeks | 6-day week, 10/12hr shifts, skeleton shifts |
| Core Mapping Database | 2-3 weeks | Database setup, editor UI, migration |
| Days Idle & New Reports | 1 week | New columns, alert reports |
| Schedule Manipulation GUI | 3-4 weeks | Drag-drop, manual overrides, re-simulation |
| Testing & Refinement | 2-3 weeks | UAT, bug fixes, performance |

**Total Estimated:** 13-19 weeks (can be compressed with parallel work)

---

**Document End**
