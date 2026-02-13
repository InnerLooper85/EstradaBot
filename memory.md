# EstradaBot — Session Memory

**Last updated:** February 13, 2026
**Current deployed version:** MVP 1.3 (revision estradabot-00016-tw2)

---

## Product Owner

- **Sean** (GitHub: InnerLooper85)
- Runs Claude Code from Windows (`C:\Users\SeanFilipow\DD Scheduler Bot`)
- Prefers fast iteration — "cowboy style" deploys when confident
- Wants to skip GitHub PR review for his own deploys (owner direct deploy in CLAUDE.md)
- Team members still go through PRs

### Working Style
- Sean dumps requirements as a stream of thoughts, then says **"Melt Banana"** as the go signal
- **"Melt Banana" means:** start executing immediately, full speed, autonomous, parallelize, minimize questions. Only pause for genuinely destructive actions.
- **DO NOT start building before the go signal.** Collect, think, but don't act until told.
- Sean prefers to see plans acknowledged and understood before execution starts

---

## Current State of the App

### What's Live (MVP 1.3)
- Full DES scheduling engine with 5-tier priority system
- Web app: Dashboard, Upload, Schedule (with filters), Reports, Simulation, Planner Workflow, Update Log
- 4/5-day schedule toggle on the schedule page
- Planner Workflow dashboard at `/planner` (3-scenario comparison, basic special requests, impact simulation)
- Feedback form with file upload support (screenshots, Excel up to 25 MB) — **Sean's highest priority, delivered**
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
- **Planner workflow not battle-tested**: 3-scenario simulation, special request queue, and publish flow are built but haven't been tested with real production data.
- **No automated tests**: Manual testing only. Unit/integration tests on MVP 1.x backlog.
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
| Review special requests with impact | Built (basic, MVP 1.3) |
| Approve/reject + generate final | Built (basic, MVP 1.3) |
| Publish schedule | Built (MVP 1.3) |
| **Dedicated Special Requests page** | **NOT BUILT** — only a collapsible form on planner page |
| **Redline Requests** (material substitution) | **NOT BUILT** |
| **Two modes** (modify existing / new WO placeholder) | **NOT BUILT** |
| **WO reconciliation on data load** | **NOT BUILT** |
| **Special Requests in left nav** | **NOT BUILT** |

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

## Remaining Work

### Immediate Next — Special Requests System (MVP 1.4)
See "Special Requests — Full Feature Specification" above. This is the next priority feature.

### MVP 1.x (no owner decisions needed)
- Resource Utilization Report (MEDIUM)
- Promise Date Risk Alert Report (MEDIUM)
- Core Shortage Alert Report (MEDIUM)
- Machine Utilization Alert Report (MEDIUM)
- Automated unit tests — pytest (MEDIUM)
- Automated integration tests (MEDIUM)
- Rubber Grouping Optimization — changeover minimization (LOW)

### MVP 2.0 (blocked on Sean's decisions)
See `MVP_2.0_Planning.md` Section 3 for the full to-do list. Key blockers:
- "Last Move Date" data source for Days Idle column
- Skeleton shift parameters
- Core Mapping database edit permissions
- Schedule manipulation scope (reorder vs reassign)
- User role permission matrix confirmation

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

## Session Tips

- Always run the session startup check (CLAUDE.md) before starting work
- Sean's `.env` has `USE_LOCAL_STORAGE=true` for dev — production does NOT have this set
- The `.env` file is gitignored — never commit it
- `DEPLOY.md` contains credentials — treat as sensitive
- When testing locally in the sandbox, the server runs at the sandbox IP, not accessible from Sean's Windows machine. Test with curl from within the sandbox.
- **Don't start building until Sean gives the go signal.** Collect requirements first.
- Sean's feedback: file upload for analysis/debugging was "the highest priority" — it's deployed now
