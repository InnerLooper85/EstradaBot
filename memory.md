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

---

## Current State of the App

### What's Live (MVP 1.3)
- Full DES scheduling engine with 5-tier priority system
- Web app: Dashboard, Upload, Schedule (with filters), Reports, Simulation, Planner Workflow, Update Log
- 4/5-day schedule toggle on the schedule page
- Planner Workflow dashboard at `/planner` (3-scenario comparison, special requests, impact simulation)
- Feedback form with file upload support (screenshots, Excel up to 25 MB)
- Local dev storage fallback (`USE_LOCAL_STORAGE=true` in .env)
- Deployed on Cloud Run, files on GCS (`gs://estradabot-files`)

### Roles That Exist
- `admin` — full access (Sean's primary account)
- `planner` — can generate/publish schedules, use planner workflow
- `customer_service` / `customerservice` — both accepted (role name inconsistency, both work)
- Guest/operator — view-only

### Known Quirks / Tech Debt
- **Role name inconsistency**: Code accepts both `customer_service` and `customerservice` as valid role names. Should be normalized eventually.
- **Planner workflow is frontend-complete but not battle-tested**: The 3-scenario simulation, special request queue, and publish flow are built but haven't been tested with real production data yet.
- **No automated tests**: Manual testing only. Unit tests and integration tests are on the MVP 1.x backlog.
- **`implementation_plan.md` is outdated**: Still references React/Node.js stack from original plan. The actual stack is Python/Flask. Status tables are current but code examples are from the original design doc, not the actual implementation.
- **Global state in app.py**: `planner_state` and `published_schedule` are module-level dicts. Works fine for single-instance Cloud Run but would need refactoring for multi-instance.

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

## What the Planner Workflow Does (MVP 1.3)

1. Planner loads data files (upload page)
2. Hits "Simulate Base Schedule" on `/planner`
3. Sees 3 scenarios side-by-side: 4d x 10h, 4d x 12h, 5d x 12h
4. Selects one as the base schedule
5. Reviews special requests (hot list requests from customer service)
6. Runs impact simulation showing what gets delayed
7. Approves/rejects requests, generates final schedule
8. Publishes — becomes the working schedule for all users

Customer service can submit special requests (priority changes, hot list items) via the app. Planner processes them in the next schedule run.

---

## Shift Configuration Details

The DES scheduler now supports two shift modes via `WorkScheduleConfig.create()`:

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
- Sean's feedback: file upload for analysis/debugging is "the highest priority" feature — it's deployed now
