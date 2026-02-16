# MVP 1.10 Implementation Plan

## Design Decisions (Confirmed)

| Decision | Choice |
|----------|--------|
| Password change | Self-service with current password confirmation |
| User deletion | Soft delete (disable/enable) |
| New roles | Add **operator** role |
| Core Mapping access | Admin + MfgEng + Planner |
| Core mismatch display | Summary count + row highlights |
| Reorder scope | Cross-BLAST allowed |
| Reorder persistence | Warn on regenerate (planner chooses keep/discard) |
| Reorder effect | Changes actual BLAST sequence (reflected in exports) |

---

## Current State

- **Users**: Stored only in environment variables, loaded into memory at startup. No management UI, no persistence, no add/edit/delete capability.
- **Core Mapping**: Fully parsed by `core_mapping_parser.py`, loaded by `data_loader.py`, used by scheduler. No dedicated viewing page.
- **Schedule Reorder**: Schedule displayed in DataTable sorted by BLAST date. No drag-and-drop, no reorder API, no sequence override.

---

## Feature 1: RBAC & User Management

### 1.1 GCS-Backed User Store

**File:** `backend/user_store.py` (new)

Create a `UserStore` class that persists users to a JSON file in GCS:
- `users.json` stored in GCS bucket at `config/users.json`
- Schema: `{ "username": { "password_hash": "...", "role": "...", "active": true, "created_at": "...", "updated_at": "..." } }`
- Methods: `load()`, `save()`, `add_user()`, `update_user()`, `disable_user()`, `enable_user()`, `change_password()`, `list_users()`
- On startup: load from GCS. If no file exists, seed with the admin from env vars (migration path).
- Thread-safe writes with file-level locking pattern.

### 1.2 Update User Model

**File:** `backend/app.py`

- Add `active` field to `User` class (default `True`)
- Add `created_at`, `updated_at` fields
- Modify `load_user()` to check `active` flag — disabled users can't log in
- Update startup code to use `UserStore` instead of env var parsing
- Keep env var `ADMIN_USERNAME`/`ADMIN_PASSWORD` as bootstrap-only (first-run seed)

### 1.3 Add Operator Role

**File:** `backend/app.py`

- Add `'operator'` to the valid roles list
- Operator gets same access as guest currently (read-only dashboard, schedule view)
- No planner or admin privileges
- Update template conditionals where guest access is checked to also include operator

### 1.4 User Management Page (Admin Only)

**Files:**
- `backend/templates/user_management.html` (new)
- `backend/app.py` (new routes)

**Page route:** `GET /user-management` (admin only)

**UI:**
- DataTable listing all users: username, role, status (active/disabled), created date
- "Add User" button → modal form (username, password, confirm password, role dropdown)
- Per-row actions: Edit Role, Reset Password, Disable/Enable toggle
- Disabled users shown with muted styling and "Disabled" badge

**API routes:**
- `POST /api/users` — create user (admin only)
- `PUT /api/users/<username>` — update role (admin only)
- `PUT /api/users/<username>/reset-password` — admin reset password (admin only)
- `PUT /api/users/<username>/disable` — disable user (admin only)
- `PUT /api/users/<username>/enable` — enable user (admin only)

### 1.5 Self-Service Password Change

**Files:**
- `backend/templates/base.html` (add "Change Password" link to user dropdown)
- `backend/app.py` (new route)

**UI:** Modal accessible from the user dropdown in navbar. Fields: current password, new password, confirm new password.

**API route:** `PUT /api/users/me/password` — requires current password validation before accepting change.

### 1.6 Navigation Update

**File:** `backend/templates/base.html`

- Add "User Management" link in sidebar (admin only section, below divider)
- Icon: `bi-people-fill`

---

## Feature 2: Core Mapping View

### 2.1 Core Mapping Page

**Files:**
- `backend/templates/core_mapping.html` (new)
- `backend/app.py` (new route)

**Page route:** `GET /core-mapping` (admin, mfgeng, planner)

**UI Layout:**
- **Summary bar** at top: total core types, total physical cores, mismatch count (highlighted in warning/red badge)
- **Tab 1: Part-to-Core Mapping** — DataTable with columns: Part Number, Description, Core Number, Rubber Type, Injection Time, Cure Time, Quench Time, Stator OD, Lobe Config, Stage Count, Fit
- **Tab 2: Core Inventory** — DataTable with columns: Core Number, Suffix, Core PN#, Model, Tooling PN#, Status (available/oven/in_use/cleaning)
- Mismatch rows highlighted with `table-warning` class (Bootstrap)
- Mismatches = parts in sales orders that reference a core not in inventory, or parts with no core mapping

### 2.2 Core Mapping API

**File:** `backend/app.py`

**API route:** `GET /api/core-mapping` — returns JSON with:
- `mapping`: list of part-to-core records
- `inventory`: list of core inventory records
- `mismatches`: list of mismatch details (part number, reason)
- `summary`: { total_core_types, total_physical_cores, mismatch_count }

Data sourced from the most recently loaded `DataLoader` instance (same data used by scheduler).

### 2.3 Navigation Update

**File:** `backend/templates/base.html`

- Add "Core Mapping" link in sidebar between "Mfg Eng Review" and "Alerts"
- Icon: `bi-diagram-3-fill`
- Visible to: admin, mfgeng, planner (template conditional)

---

## Feature 3: Schedule Reorder (Drag & Drop)

### 3.1 Drag-and-Drop UI

**File:** `backend/templates/schedule.html`

- Add [SortableJS](https://sortablejs.github.io/Sortable/) library (lightweight, no jQuery UI needed) — add via CDN
- Add drag handles column (leftmost) to the schedule DataTable
- Enable row dragging across all rows (cross-BLAST movement)
- Visual feedback: dragged row highlighted, drop target indicated
- After drop: renumber BLAST sequence for all affected rows
- "Save Order" button appears when changes are pending (unsaved state)
- "Reset Order" button to revert to original scheduler output
- Only available to admin and planner roles

### 3.2 Reorder API

**File:** `backend/app.py`

**API routes:**
- `POST /api/schedule/reorder` — accepts new sequence: `{ "mode": "4day|5day", "order": ["WO-001", "WO-002", ...] }`
  - Validates all WO numbers exist
  - Saves reordered sequence to GCS at `schedules/reorder_{mode}_{timestamp}.json`
  - Updates in-memory schedule state
  - Returns updated schedule with new BLAST sequence numbers
  - Admin/planner only

- `DELETE /api/schedule/reorder` — clears custom ordering, reverts to scheduler output
  - Admin/planner only

- `GET /api/schedule/reorder/status` — returns whether custom ordering exists for current schedule

### 3.3 BLAST Sequence Recalculation

**File:** `backend/algorithms/scheduler.py` or new utility

When reorder is saved:
- Reassign `blast_date` values based on new sequence order, maintaining original takt intervals
- Recalculate `completion_date` based on new blast_date + process times
- Update `on_time` status based on new completion vs promise date
- Recalculate `planned_desma` assignment for rubber type feasibility (or flag conflicts)

### 3.4 Export Integration

**File:** `backend/exporters/excel_exporter.py`

- `export_blast_schedule()`: Use reordered sequence if it exists (instead of sorting by blast_date)
- Sequence numbers in export reflect the planner's manual ordering
- Add a "Manual Override" indicator column when custom ordering is active

### 3.5 Regeneration Warning

**File:** `backend/app.py` (in `/api/generate` route)

Before generating a new schedule:
- Check if custom reordering exists for the current schedule
- If yes, return a warning response: `{ "warning": "custom_order_exists", "message": "..." }`
- Frontend shows confirmation dialog: "Custom ordering exists. Keep or discard?"
- If planner chooses "keep", store the WO sequence; after generation, attempt to re-apply ordering (best effort — new/removed WOs handled gracefully)
- If planner chooses "discard", generate fresh

### 3.6 Persistence

**File:** `backend/gcs_storage.py` (if needed)

- Reorder state saved as JSON in GCS: `schedules/reorder_state.json`
- Structure: `{ "mode": "4day", "sequence": ["WO-001", ...], "created_by": "username", "created_at": "ISO timestamp", "based_on_schedule": "schedule_id" }`

---

## Implementation Order

1. **RBAC & User Management** (Feature 1) — Foundation for access control
   - 1.1 UserStore class
   - 1.2 Update User model + startup
   - 1.3 Add operator role
   - 1.4 User management page + API
   - 1.5 Self-service password change
   - 1.6 Navigation update

2. **Core Mapping View** (Feature 2) — Read-only, lower complexity
   - 2.1 Core mapping page template
   - 2.2 Core mapping API endpoint
   - 2.3 Navigation update

3. **Schedule Reorder** (Feature 3) — Most complex, depends on RBAC
   - 3.1 Drag-and-drop UI
   - 3.2 Reorder API endpoints
   - 3.3 BLAST sequence recalculation
   - 3.4 Export integration
   - 3.5 Regeneration warning
   - 3.6 Persistence

---

## Files Modified (Summary)

| File | Changes |
|------|---------|
| `backend/user_store.py` | **NEW** — GCS-backed user persistence |
| `backend/app.py` | User model updates, ~8 new routes, reorder logic, core mapping API |
| `backend/templates/base.html` | Nav links (User Mgmt, Core Mapping), password change modal |
| `backend/templates/user_management.html` | **NEW** — Admin user management page |
| `backend/templates/core_mapping.html` | **NEW** — Core mapping read-only view |
| `backend/templates/schedule.html` | Drag-and-drop reorder UI, SortableJS |
| `backend/exporters/excel_exporter.py` | Reorder-aware BLAST export |
| `backend/gcs_storage.py` | Minor additions for reorder state storage (if needed) |

---

## Risks & Considerations

- **User migration**: First startup with UserStore needs to seed from env vars gracefully. Existing env var users should auto-migrate.
- **BLAST recalculation accuracy**: Reordering across BLASTs changes timing — need to handle Desma conflicts and core availability. May need to flag infeasible reorders rather than silently accept them.
- **Concurrent access**: Multiple planners reordering simultaneously could conflict. Simple last-write-wins for MVP, with username tracking.
- **DataTables + SortableJS**: These libraries can conflict. May need to temporarily destroy/reinitialize DataTable during drag operations, or use a custom rendering approach for the reorder mode.
