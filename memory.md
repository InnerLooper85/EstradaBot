# EstradaBot — Session Memory

**Last updated:** February 14, 2026
**Current deployed version:** MVP 1.6 (on master)
**Working branch version:** MVP 1.7+ (on claude/review-estradabot-build-plan-QZj5H)

---

## Product Owner

- **Sean** (GitHub: InnerLooper85)
- Runs Claude Code from Windows (`C:\Users\SeanFilipow\DD Scheduler Bot`)
- Prefers fast iteration — "cowboy style" deploys when confident
- Wants to skip GitHub PR review for his own deploys (owner direct deploy in CLAUDE.md)
- Team members still go through PRs

### Working Style — Melt Banana Protocol (MBP)

Full protocol is defined in `CLAUDE.md` under "Melt Banana Protocol (MBP)". Summary:

- **"Initiate MBP"** or **"Initiate Melt Banana Protocol"** → Enter collection mode. Stop all actions. Only digest prompts, acknowledge with numbered receipts, and write requirements to memory.md.
- **"Melt Banana"**, **"MELT BANANA"**, or **"Cook the Cavendish"** → Go signal. Present consolidated briefing, then execute full speed.
- **"Cancel MBP"**, **"Stand down"**, or **"Abort MBP"** → Cancel collection, keep notes, return to normal.
- During MBP: number each prompt (MBP #1, #2, ...), update memory.md in real time, don't build anything.
- On go signal: consolidated summary first, then autonomous execution.

---

## Current State of the App

### What's Live (MVP 1.6)
- Full DES scheduling engine with 5-tier priority system
- Web app: Dashboard, Upload, Schedule (with filters), Reports, Simulation, Planner Workflow, Update Log
- 4/5-day schedule toggle on the schedule page
- Planner Workflow dashboard at `/planner` (3-scenario comparison, basic special requests, impact simulation)
- Dedicated Special Requests page (`/special-requests`) with Mode A/B, impact preview, approval queue
- Mfg Eng Review page (`/mfg-eng-review`)
- Feedback form with file upload support (screenshots, Excel up to 25 MB)
- Local dev storage fallback (`USE_LOCAL_STORAGE=true` in .env)
- Deployed on Cloud Run, files on GCS (`gs://estradabot-files`)

### Roles That Exist
- `admin` — full access (Sean's primary account)
- `planner` — can generate/publish schedules, use planner workflow
- `customer_service` / `customerservice` — both accepted (role name inconsistency, both work)
- `mfgeng` — manufacturing engineering (placeholder, limited implementation)
- Guest/operator — view-only

### Known Quirks / Tech Debt
- **Role name inconsistency**: Code accepts both `customer_service` and `customerservice`. Should be normalized.
- **Role case sensitivity BUG (FIXED)**: Roles from USERS env var were case-sensitive — `Planner` ≠ `planner`. Fixed by normalizing to lowercase on load.
- **File name detection (FIXED)**: Files named `OSO_*.xlsx` and `SDR_*.xlsx` not recognized. Fixed to accept these patterns.
- **DCP Report parser (BUILT)**: Parses DCPReport Excel files for WO-level special instructions and supermarket locations.
- **Planner workflow not battle-tested**: 3-scenario simulation, special request queue, and publish flow are built but haven't been tested with real production data.
- **`implementation_plan.md` is outdated**: References React/Node.js stack from original plan. Actual stack is Python/Flask.
- **Global state in app.py**: `planner_state` and `published_schedule` are module-level dicts. Fine for single-instance Cloud Run.

---

## Key Files Quick Reference

| What | Where |
|------|-------|
| Flask app + all routes | `backend/app.py` |
| DES scheduling engine | `backend/algorithms/des_scheduler.py` |
| GCS + local storage helpers | `backend/gcs_storage.py` |
| Planner workflow page | `backend/templates/planner.html` |
| Base template (navbar, sidebar) | `backend/templates/base.html` |
| Update log + feedback form | `backend/templates/update_log.html` |
| Schedule page with DataTable | `backend/templates/schedule.html` |
| Excel report generation | `backend/exporters/excel_exporter.py` |
| Impact analysis export | `backend/exporters/impact_analysis_exporter.py` |
| Project instructions | `CLAUDE.md` |
| MVP 2.0 planning + questions | `MVP_2.0_Planning.md` |
| Full implementation history | `implementation_plan.md` |

---

## Planner Workflow — Full Specification

### The 7-Step Flow (as designed by Sean)

1. **Load data files** — existing upload page flow
2. **"Simulate Base Schedule"** — runs DES engine 3 times, **WITHOUT special requests** (clean baseline)
3. **Scenario dashboard** — side-by-side comparison:
   - Scenario A: 4 days × 10 hours/day
   - Scenario B: 4 days × 12 hours/day
   - Scenario C: 5 days × 12 hours/day
   - Each shows metrics: on-time rate, late orders, at-risk, avg turnaround
4. **Set base schedule mode** — planner picks a scenario
5. **Base schedule locked** — this is the schedule without any special requests
6. **Review special requests** — planner clicks button to review. Full hot list Excel uploads AND app-based special requests are simulated. Planner sees impact dashboard.
7. **Approve/reject + generate final + publish**:
   - Approve orders they agree with
   - Click "Generate Final Schedule" — produces final schedule with approved requests baked in
   - Dashboard shows finalized metrics
   - Click "Publish Schedule" — pushes to all users as the working schedule

### Real-Time Example (Sean's scenario)
- **8:00 AM**: Planner publishes a new schedule
- **10:00 AM**: Customer Service enters a hot list request via Special Requests page. Impacts are simulated and shown to the CS user. If they proceed, they click "Make Request."
- **11:00 AM**: Planner comes in to run a new schedule. They see the pending hot list request in Step 6, review the impact, approve/reject, and publish an updated schedule.

### What's Built vs What's Specified

| Feature | Status |
|---------|--------|
| 3-scenario simulation (4d/10h, 4d/12h, 5d/12h) | Built (MVP 1.3) |
| Scenario comparison dashboard | Built (MVP 1.3) |
| Base schedule selection | Built (MVP 1.3) |
| Review special requests with impact | Built (MVP 1.4) |
| Approve/reject + generate final | Built (MVP 1.4) |
| Publish schedule | Built (MVP 1.3) |
| Dedicated Special Requests page | Built (MVP 1.4) |
| Redline Requests (material substitution) | Built (MVP 1.4) |
| Two modes (modify existing / new WO placeholder) | Built (MVP 1.4) |
| WO reconciliation on data load | Built (MVP 1.4) |
| Special Requests in left nav | Built (MVP 1.4) |
| **Order Holds** (exclude from scheduling) | **Built (MVP 1.7)** |
| **Special Instructions column** on schedules | **Built (MVP 1.7)** — field ready, needs DCP parser |
| **Simulation defaults to published schedule** | **Built (MVP 1.7)** |

---

## Special Requests — Full Feature Specification

### Overview
A new **"Special Requests"** page accessible from the left nav bar. This is the primary interface for entering requests that modify the schedule. It replaces the basic collapsible form currently on the planner page.

### Request Types
1. **Redline Requests**: Order a standard part with a change (e.g., part calls for HR rubber but customer needs XE). Any role submits, Planner/Admin approves.
2. **Hot List Orders**: Manual entry of hot list items as an alternative to Excel upload. Same fields the Excel parser expects.

### Two Modes
- **Mode A — Modify Existing Order**: Search/select an order the app already knows about (from data loads). Apply changes (material subs, priority changes, hot list addition). Feeds into Planner approval queue.
- **Mode B — New Incoming Request**: Enter a WO number + request details for an order that **doesn't exist in the system yet**. Stored as a placeholder. When a data file is later loaded containing that WO, the system matches it up and surfaces the pending request.

### Reconciliation
When new data files are loaded (via upload page), the system must check for pending Special Requests tied to incoming WO numbers and:
- Match them up
- Surface them to the Planner for review
- Apply approved modifications

### Permissions
- **Submit a request**: Any authenticated role
- **Approve/reject a request**: Planner or Admin only
- **View the approvals queue**: All roles (transparency), but approve/reject buttons only for Planner/Admin
- **Approved requests** get incorporated into the Published Schedule
- **Rejected requests** get a status update + reason (visible to the original submitter)

### Integration with Planner Workflow
- Pending special requests appear in Step 6 of the planner workflow
- Planner reviews impact, approves/rejects, then generates final schedule
- Both Excel-uploaded hot list items and app-entered special requests are combined

---

## Shift Configuration Details

The DES scheduler supports two shift modes via `WorkScheduleConfig.create()`:

- **12-hour shifts**: Day 5AM-5PM, Night 5PM-5AM, with breaks at 9:00 (15 min), 11:00 (45 min), 21:00 (15 min), 23:00 (45 min). 30-min handover each shift.
- **10-hour shifts**: Day only 5AM-3PM, no night shift. Breaks at 9:00 (15 min), 11:00 (45 min). 30-min handover.

Scenario configs in app.py:
```python
SCENARIO_CONFIGS = {
    '4day_10h': {'working_days': [0,1,2,3], 'shift_hours': 10},
    '4day_12h': {'working_days': [0,1,2,3], 'shift_hours': 12},
    '5day_12h': {'working_days': [0,1,2,3,4], 'shift_hours': 12},
}
```

---

## Implementation Plan

### MVP 1.4 — Special Requests System (can build now, no decisions needed)

Everything below has enough spec from the previous conversation to implement.

#### 1. Dedicated Special Requests Page
- New route: `GET /special-requests` → `special_requests.html`
- New template: `backend/templates/special_requests.html`
- Left nav link in `base.html` — visible to ALL authenticated roles
- Remove/replace the collapsible form currently embedded in `planner.html`

#### 2. Request Submission Form — Two Modes
- **Mode A — Modify Existing Order**:
  - WO# search/autocomplete against current schedule data (`/api/schedule` already returns all orders)
  - When WO found: pre-fill order details (part number, customer, rubber type, core)
  - User selects change type: Hot List (priority bump) or Redline (rubber substitution)
  - For Redline: dropdown for rubber override (XE, HR, XD, XR — already in existing form)
  - For Hot List: ASAP vs Dated toggle + need-by-date picker (already exists)
- **Mode B — New Incoming Request**:
  - Manual WO# entry (free text, no autocomplete match)
  - App detects "WO not found in system" and switches to placeholder mode
  - User fills in: request type, priority, rubber override, reason/comments
  - Stored with a `matched: false` flag for later reconciliation

#### 3. Approval Queue
- Visible section on the Special Requests page (below the submission form, or as a tab)
- Shows ALL requests with status badges (pending/approved/rejected/published)
- Filterable by status
- **All roles** can see the queue (transparency)
- **Approve/Reject buttons** only render for Planner and Admin roles
- Rejection requires a reason (text input)
- Already have the API: `POST /api/planner/approve-requests`

#### 4. Impact Preview at Submission Time
- When a user (e.g., CS at 10AM) submits a request, show them a preview of the impact
- Run the DES engine: current published schedule as baseline, then re-run with the new request added
- Show: which orders get delayed, by how much, any newly-late orders
- User sees this BEFORE clicking "Make Request" — they can cancel or proceed
- This is a lightweight version of what the planner sees in Step 6

#### 5. Data Load Reconciliation (Mode B matching)
- When new files are uploaded via `/api/upload`, after parsing:
  - Check all `matched: false` special requests against incoming WO numbers
  - If a match is found: update the request's `matched: true`, attach the order details
  - Surface a notification/badge: "X pending requests matched new data"
- Matched requests appear in the planner's Step 6 review with full order context

#### 6. Planner Workflow Integration
- Step 6 of planner workflow pulls from the same Special Requests store
- Includes both Excel-uploaded hot list items AND app-entered requests
- Planner sees unified view: all pending requests with impact analysis
- Approvals from the Special Requests page carry over (already approved = pre-approved in Step 6)

#### Files to Create/Modify
| File | Action |
|------|--------|
| `backend/templates/special_requests.html` | **CREATE** — main page template |
| `backend/templates/base.html` | EDIT — add "Special Requests" to left nav |
| `backend/templates/planner.html` | EDIT — remove embedded form, link to Special Requests page |
| `backend/app.py` | EDIT — add `/special-requests` route, update `/api/upload` for reconciliation, add impact-preview endpoint |
| `backend/gcs_storage.py` | EDIT — add `matched` field support to special request storage |

#### Existing Infrastructure (already built, reuse)
- `POST /api/special-requests` — submission endpoint
- `GET /api/special-requests` — list with status filter
- `POST /api/planner/approve-requests` — approval endpoint
- `save_special_requests()` / `load_special_requests()` — GCS persistence
- Hot list → scheduler conversion logic in `simulate_with_requests()`
- Request type field already supports: `hot_list`, `expedite`, `rubber_override`

---

### MVP 1.5 — Needs Sean's Input Before Building

#### Questions that need answers:

1. **Redline scope beyond rubber type**: The current form handles rubber substitution (HR→XE etc). Are there other types of redline changes? Examples:
   - Different core assignment?
   - Changed process routing (skip/add operations)?
   - Different part number substitution?
   - Or is rubber override the only redline case for now?

2. **Reconciliation behavior details**: When a Mode B placeholder matches a newly-uploaded WO:
   - Auto-apply the request to the order? Or just flag it for planner review?
   - What if the uploaded order data contradicts the request (e.g., request says "expedite WO 12345" but the WO comes in with a different part number than expected)?
   - Should unmatched placeholders expire after some time?

3. **Notification system**: Sean's 10AM example implies CS should know their request was processed:
   - In-app notifications (badge/bell icon)?
   - Just check the status on the Special Requests page?
   - Email notifications?

4. **Alert Reports** (independent feature set):
   - Resource Utilization Report — what thresholds? Format?
   - Promise Date Risk — how many days buffer = "at risk"?
   - Core Shortage — current thresholds work?
   - Machine Utilization — over/under thresholds?

5. **Automated tests** — what to prioritize first?

---

### MVP 2.0 (blocked on larger architectural decisions)
See `MVP_2.0_Planning.md` Section 3 for the full to-do list. Key blockers:
- "Last Move Date" data source for Days Idle column
- Skeleton shift parameters
- Core Mapping database edit permissions
- GUI drag-drop schedule manipulation scope
- Full RBAC with user management UI

---

## Deployment

- **Cloud Run**: `gcloud run deploy estradabot --source . --region us-central1 --allow-unauthenticated`
- **GCP Project**: `project-20e62326-f8a0-47bc-be6`
- **Region**: us-central1
- **Domain**: estradabot.biz
- **GCS Bucket**: `gs://estradabot-files`
- Claude Code sandbox can push to `claude/*` branches but NOT directly to `master` (403)
- Sean pushes to master locally after Claude merges on the branch

---

## Feedback Workflow for Dev Sessions

To pull user feedback from the live site into a Claude Code session:

1. **Export all feedback** (requires admin login):
   ```bash
   # From Sean's machine (logged in as admin in browser):
   # Visit https://estradabot.biz/api/feedback/export
   # Save the JSON file, then provide to Claude Code
   ```

2. **Download specific attachments**:
   ```bash
   # From the export JSON, each entry with an attachment has:
   #   attachment.stored_as = filename in GCS
   #   attachment.folder = "feedback/attachments" or "feedback/example_files"
   # Download via:
   # https://estradabot.biz/api/feedback/download/{stored_as}?folder={folder}
   ```

3. **Key files from feedback (Feb 13, 2026)**:
   - `DCPReport_34.xlsx` (107 KB) — Contains WO-level special instructions for blast schedule column
   - `OSO_021326.xlsx` (1498 KB) — Example Open Sales Order with non-standard naming
   - `SDR_021326.XLSX` (196 KB) — Example Shop Dispatch with non-standard naming
   - `Capture.PNG` (104 KB) — Screenshot of admin upload error
   - `image.png` (251 KB) — Screenshot of planner permissions error

4. **Feedback API** (admin only):
   - `GET /api/feedback` — JSON list of all feedback entries
   - `GET /api/feedback/export` — Downloadable JSON export
   - `GET /api/feedback/download/{filename}?folder={folder}` — Download attachment

---

## MBP Session — February 13, 2026

### Items Collected (6 total)

1. **Roles bug** — Planner signed in but can't generate schedules. Case-sensitive role comparison: `Planner` ≠ `planner`. **FIXED** — normalized roles to lowercase in `load_users()`.
2. **Admin upload error** — Loading documents as admin gave error. Root cause: file naming patterns (`OSO_*`, `SDR_*`) not recognized by the app. **FIXED** — added OSO/SDR patterns to file detection in gcs_storage, data_loader, upload.html, and app.py scrub logic.
3. **Special Instructions column** — Add to Blast (next to Core Required), Core Oven (next to Core), and Master (far right) schedules. Data source: DCPReport file. **BUILT** — column added to all 3 exports. Field added to ScheduledOrder/PartState data model. Needs DCP parser to populate.
4. **Pull all site feedback** — Download feedback entries, images, and reports. Integrate into work list. **DONE** — cataloged 9 entries, identified bugs and feature requests. Added `/api/feedback/export` endpoint.
5. **Simulation defaults to published schedule** — No longer require fresh generate each time. **BUILT** — simulation data saved to GCS on generate, served from persisted data when no in-memory objects.
6. **Order Hold status** — Flag orders as "on hold" to exclude from scheduling. Persists across uploads/simulations until removed. **BUILT** — separate holds system with API endpoints, UI on Special Requests page, scheduler exclusion logic.

### Status: All 6 items COMPLETE. Deployed as part of MVP 1.7 branch.

### Open Items from Feedback (Feb 13)
- ~~DCPReport parser~~ — **BUILT** (Feb 14 session). Parses special instructions + supermarket locations.
- ~~Capture.PNG error~~ — **Confirmed FIXED** by Sean. Was file detection bug.
- MfgEng user role confusion — **Confirmed FIXED** by role case-sensitivity fix. May still need Sean to verify USERS env var entries.

---

## Session — February 14, 2026

### Decisions Made

1. **Feedback status tracking** — Add Status column to admin feedback table. Statuses: New, In-Work, Fixed, Resolved w/o Action. Backend API to update. New feedback defaults to "New."
2. **Capture.PNG error** — Confirmed fixed by Sean. No further action.
3. **Mode B reconciliation** — Decisions made:
   - **Match behavior:** Flag for planner review (leave as-is, don't auto-apply)
   - **Data mismatches:** When a placeholder matches a WO but part_number/customer don't line up, flag with `needs_review` and store mismatch details. Notification sent to admin/planner.
   - **Expiration:** Unmatched placeholders auto-expire after 28 days (status → 'expired')
4. **Notification bell system** — In-app bell icon with unread badge count, top-right navbar next to user login info. Dropdown shows recent notifications. Also viewable on a dedicated page. Auto-mark-as-read after 1 week.
5. **Alert Reports** — All 4 types: Promise Date Risk, Core Shortage, Machine Utilization, Late Order Summary. Display: dashboard cards + dedicated Alerts page. Timing: auto-generate on schedule publish + on-demand refresh button.
6. **Automated tests** — Starting with pytest framework, DES engine tests, API endpoint tests, parser tests.

### Items Being Built (Feb 14)
- [ ] Feedback status column + API
- [ ] Notification bell system (storage, API, navbar bell, dropdown, auto-read expiry)
- [ ] Alert reports engine (4 alert types)
- [ ] Alert dashboard cards on main dashboard
- [ ] Dedicated Alerts page with filtering/history
- [ ] Pytest framework + core test suites

---

## Session Tips

- Always run the session startup check (CLAUDE.md) before starting work
- Sean's `.env` has `USE_LOCAL_STORAGE=true` for dev — production does NOT have this set
- The `.env` file is gitignored — never commit it
- `DEPLOY.md` contains credentials — treat as sensitive
- When testing locally in the sandbox, the server runs at the sandbox IP, not accessible from Sean's Windows machine. Test with curl from within the sandbox.
- **Don't start building until Sean gives the go signal.** Collect requirements first.
- Sean's feedback: file upload for analysis/debugging was "the highest priority" — it's deployed now
