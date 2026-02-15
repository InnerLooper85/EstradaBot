# EstradaBot — Session Memory

**Last updated:** February 15, 2026
**Current deployed version:** MVP 1.7 (on master)

---

## Product Owner

- **Sean** (GitHub: InnerLooper85)
- Runs Claude Code from Windows (`C:\Users\SeanFilipow\DD Scheduler Bot`)
- Prefers fast iteration — "cowboy style" deploys when confident
- Wants to skip GitHub PR review for his own deploys (owner direct deploy in CLAUDE.md)

### Working Style — Protocols

- **Melt Banana Protocol (MBP)** — batch requirement collection. Full spec in `CLAUDE.md`.
- **Deglazing Protocol** — plan review workflow. Full spec in `CLAUDE.md`.

---

## Current State of the App (MVP 1.7)

- Full DES scheduling engine with 5-tier priority system
- Web app: Dashboard, Upload, Schedule, Reports, Simulation, Planner Workflow, Update Log
- 4/5-day schedule toggle, 3-scenario planner comparison (4d/10h, 4d/12h, 5d/12h)
- Special Requests page with Mode A/B, impact preview, approval queue
- Order Holds system, Special Instructions column (from DCP Report)
- Notification bell, Alert reports (4 types), Feedback status tracking
- Mfg Eng Review page, DCP Report parser
- Deployed on Cloud Run, files on GCS (`gs://estradabot-files`)

### Roles
- `admin`, `planner`, `customer_service`/`customerservice`, `mfgeng`, guest/operator

### Known Tech Debt
- Role name inconsistency (`customer_service` vs `customerservice`)
- Global state in app.py (module-level dicts — fine for single-instance Cloud Run)
- No automated tests (pytest planned)
- Planner workflow not battle-tested with real production data

---

## Key Files

| What | Where |
|------|-------|
| Flask app + routes | `backend/app.py` |
| DES engine | `backend/algorithms/des_scheduler.py` |
| GCS storage | `backend/gcs_storage.py` |
| Base template | `backend/templates/base.html` |
| Schedule page | `backend/templates/schedule.html` |
| Excel exporter | `backend/exporters/excel_exporter.py` |
| Project instructions | `CLAUDE.md` |
| MVP 2.0 planning | `MVP_2.0_Planning.md` |
| Implementation status | `implementation_plan.md` |

---

## Deployment

- **Cloud Run**: `gcloud run deploy estradabot --source . --region us-central1 --allow-unauthenticated`
- **GCP Project**: `project-20e62326-f8a0-47bc-be6`
- **GCS Bucket**: `gs://estradabot-files`
- **Domain**: estradabot.biz
- Claude Code sandbox pushes to `claude/*` branches; Sean pushes to master locally

---

## Feedback Workflow

- Export: `https://estradabot.biz/api/feedback/export` (admin login required)
- API: `GET /api/feedback`, `GET /api/feedback/export`, `GET /api/feedback/download/{filename}?folder={folder}`

---

## Key Decisions (Feb 13-14, 2026)

- **Mode B reconciliation**: Flag for planner review, don't auto-apply. Mismatches get `needs_review`. Expire unmatched after 28 days.
- **Notifications**: In-app bell icon, unread badge, auto-mark-as-read after 1 week.
- **Alerts**: 4 types (Promise Date Risk, Core Shortage, Machine Utilization, Late Order Summary). Auto-generate on publish + on-demand refresh.
- **Automated tests**: pytest framework, starting with DES engine, API endpoints, parsers.

---

## Shift Configuration

- **12-hour**: Day 5AM-5PM, Night 5PM-5AM. Breaks at 9:00 (15m), 11:00 (45m), 21:00 (15m), 23:00 (45m). 30-min handover.
- **10-hour**: Day only 5AM-3PM. Breaks at 9:00 (15m), 11:00 (45m). 30-min handover.

Scenario configs: `4day_10h`, `4day_12h`, `5day_12h` in `app.py`.

---

## Roadmap Decisions — Feb 15, 2026

**Status:** EXECUTED (MBP session complete)

### MVP 1.x Release Plan (agreed Feb 15)

- **1.8:** Role name normalization, resource utilization report, Days Idle column
- **1.9:** Extended simulation (6-day weeks, skeleton shifts)
- **1.10:** RBAC / user management, Core Mapping read-only view, basic schedule reorder
- **Ongoing:** Automated tests (with each release), rubber grouping (when convenient)

### MVP 2.0 — New Scope

MVP 2.0 is now defined as **two major features**:

1. **Rotors product line** — second department with own staffing, machines, scheduling logic. Separate department, shared UI framework.
2. **Customer-facing reports & quoting system** — sales/CS generate customer reports, create quotes that place temporary holds on production slots. Held slots released on quote expiry.

Plus carryover items:
- Full schedule manipulation GUI (drag-drop + resource reassignment)
- Core Mapping: editable database

See `MVP_2.0_Planning.md` for full details.

---

## Session Tips

- Always run session startup check per CLAUDE.md
- Sean's `.env` has `USE_LOCAL_STORAGE=true` — production does NOT
- `.env` is gitignored. `DEPLOY.md` contains credentials — treat as sensitive.
- Don't start building until Sean gives the go signal (MBP workflow).
