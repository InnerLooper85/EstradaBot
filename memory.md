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

## MBP Session — Feb 15, 2026 (Roadmap Replanning)

**Status:** COLLECTING

**Context:** Reviewing and replanning the project roadmap. Several items moved from MVP 2.0 to MVP 1.x during interactive walkthrough. MBP initiated to collect additional requirements.

### Decisions Made Before MBP (interactive walkthrough)

- Resource utilization report → MVP 1.8
- Role name normalization → next 1.x release
- Rubber grouping optimization → stays MVP 1.x backlog (LOW)
- Tests & alert reports → already done in 1.7, doc cleanup needed
- Extended simulation options (6-day, skeleton shifts) → moved to 1.x
  - Skeleton shifts = takt time adjustment (all machines available, fewer staff = longer takt)
  - User enters expected takt time for skeleton
  - Day shift, night shift, or both — user picks
  - Any day configurable as full or skeleton
  - 6th day (Saturday) — user chooses full or skeleton
- RBAC / user management → moved to 1.x (role matrix deferred)
- Core Mapping: read-only web view in 1.x, editable database in 2.0 (DB tech deferred)
- Days Idle column → moved to 1.x
  - Data source: "Elapsed Days" column in Shop Dispatch report (already uploaded)
  - Rule: 9999 → 0 (just-released orders); otherwise display as-is
- Basic schedule reorder → 1.x
- Full schedule manipulation GUI (drag-drop + resource reassignment) → MVP 2.0

### MBP Items

1. **MVP 2.0 = Rotors product line.** Add a second department (Rotors) with its own staffing, machines, and scheduling logic. Separate department but shared UI framework and feature set. This redefines the entire MVP 2.0 scope.

---

## Session Tips

- Always run session startup check per CLAUDE.md
- Sean's `.env` has `USE_LOCAL_STORAGE=true` — production does NOT
- `.env` is gitignored. `DEPLOY.md` contains credentials — treat as sensitive.
- Don't start building until Sean gives the go signal (MBP workflow).
