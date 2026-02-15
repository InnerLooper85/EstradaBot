# EstradaBot - Claude Code Project Instructions

## Session Startup (MANDATORY)

**Before doing ANY work, always run these verification steps and report the results to the developer:**

1. Run `git fetch origin` to get the latest remote state
2. Run `git branch --show-current` to confirm the active branch
3. Run `git status` to check for uncommitted changes
4. Run `git log --oneline -1` to show the current local commit
5. Run `git log --oneline -1 origin/master` to show the latest remote master commit
6. Compare local vs remote — if the branch is behind, **warn the developer** before proceeding

**Report format:**
```
SESSION CHECK:
  Branch:          <current branch>
  Local commit:    <short hash + message>
  Remote master:   <short hash + message>
  Status:          UP TO DATE | BEHIND BY X COMMITS | UNCOMMITTED CHANGES
  Ready to work:   YES | NO — <reason>
```

If the branch is behind remote or has merge conflicts, do NOT begin work until the developer decides how to handle it.

---

## Melt Banana Protocol (MBP)

Sean delivers requirements as a stream of prompts meant to be considered and acted upon together. The Melt Banana Protocol governs how Claude handles this batch-input workflow.

### Entering MBP

**Trigger phrases (any of these):**
- "Initiate Melt Banana Protocol"
- "Initiate MBP"

When MBP is initiated:

1. **STOP all immediate actions.** Do not write code, create files, run commands, or make any changes.
2. **Enter collection mode.** Your only job is to digest each prompt and update `memory.md`.
3. **Acknowledge each prompt with a numbered receipt:**
   - Example: `MBP #1: Rework the BLAST sequence to support 6-day weeks — captured.`
   - Example: `MBP #2: Add tooltip to schedule page showing core details — captured.`
   - Keep receipts short (one line). Show you understood the intent.
4. **Write collected requirements into `memory.md`** under a new section (e.g., `## MBP Session — [date]`). This is the primary deliverable during collection. Update it as each prompt arrives so nothing is lost if context compresses.
5. **Think, organize, and identify dependencies** between the collected items, but do NOT act on them yet.

### Exiting MBP (Go Signal)

**Trigger phrases (any of these):**
- "Melt Banana"
- "MELT BANANA"
- "Cook the Cavendish"

When the go signal is given:

1. **Present a consolidated briefing** — a single numbered summary of everything collected, grouped logically. This is a quick sanity check, not a blocker.
2. **Then execute immediately.** Full speed, autonomous, parallelize where possible, minimize questions. Only pause for genuinely destructive or irreversible actions.

### Aborting MBP

**Trigger phrases (any of these):**
- "Cancel MBP"
- "Stand down"
- "Abort MBP"

When aborted:
- Stop collection mode, return to normal interactive behavior.
- Keep anything already written to `memory.md` (don't delete collected notes).
- Acknowledge: "MBP cancelled. [N] items collected and saved to memory.md."

### Rules

- **Never break MBP to start building early.** Even if a prompt seems urgent or simple.
- **Priority ordering is Sean's job.** Collect everything; don't reorder or skip items.
- **Ask clarifying questions sparingly during MBP.** Only if a prompt is genuinely ambiguous. Prefer collecting and clarifying in the consolidated briefing.
- **MBP state survives context compression.** If you notice you're in MBP (check memory.md for an active MBP session section), stay in collection mode until the go signal.

---

## Deglazing Protocol

When reviewing an existing plan or planning document, the Deglazing Protocol provides a structured way to recover what's still valid, identify what's changed, surface decisions that need to be made, and produce a clean updated version — like deglazing a pan to incorporate the fond into a new sauce.

### Entering the Deglazing Protocol

**Trigger phrases (any of these):**
- "Initiate Deglazing Protocol"
- "Deglaze"
- "Deglaze [document name]"

### What Claude Does

When the Deglazing Protocol is initiated:

1. **Identify the target document.** If not specified, ask which plan to review. Common targets:
   - `MVP_2.0_Planning.md`
   - `planning/roadmap.md`
   - A specific phase file in `planning/`
   - `implementation_plan.md`

2. **Read the document and produce a Deglaze Report** with these sections:

   **STILL VALID** — Items that remain accurate and don't need changes. List briefly.

   **STALE / OUTDATED** — Items that reference old state, completed work, or superseded decisions. For each: what it says now, what it should say (or whether to remove it).

   **OPEN QUESTIONS** — Decisions that still need Sean's input. For each: the question, why it matters, and what's blocked until it's answered. Number these for easy reference.

   **NEW CONTEXT** — Things that have changed since the document was written that affect the plan. New features built, bugs discovered, decisions made in later sessions, etc.

   **PROPOSED UPDATES** — Specific edits to make, grouped by section. These are proposals, not actions — wait for Sean's approval.

3. **Present the report and wait.** Do NOT edit the document yet. The report is a conversation starter, not a go signal.

### After the Report

Sean will review and respond. Common patterns:
- "Approve all" or "Looks good, make the changes" → Apply all proposed updates
- "Approve except #3 and #7" → Apply all except those items, discuss the exceptions
- Inline corrections → Incorporate Sean's edits and apply
- "Let's discuss [topic]" → Switch to interactive discussion on that topic, then return to the report

### Combining with MBP

If Sean wants to add new requirements during a Deglaze session, he can initiate MBP. The Deglazing Protocol pauses, MBP collects new items, and when MBP completes (go signal), the new items are incorporated into the Deglaze report as additions before applying updates.

### Rules

- **Never edit the target document before presenting the report.** The report is for review, not a fait accompli.
- **Keep the report scannable.** Use bullet points, not paragraphs. Sean should be able to approve/reject individual items quickly.
- **Number open questions consistently.** Use `DG-Q1`, `DG-Q2`, etc. so Sean can reference them easily.
- **Track what was approved.** After applying changes, update `planning/state.md` with a session log entry noting what was deglazed and what changed.

---

## Project Overview

**EstradaBot** is a discrete event simulation (DES) based production scheduling web application for stator manufacturing. It is deployed on Google Cloud Run with persistent storage via Google Cloud Storage.

- **Repository:** https://github.com/InnerLooper85/EstradaBot.git
- **Live site:** https://estradabot.biz
- **GCP Project:** project-20e62326-f8a0-47bc-be6
- **GCS Bucket:** gs://estradabot-files
- **Region:** us-central1

---

## Tech Stack

- **Backend:** Python 3.11, Flask 3.0+, gunicorn
- **Frontend:** Bootstrap 5, jQuery, DataTables, Jinja2 templates
- **Scheduler Engine:** Custom DES in `backend/algorithms/des_scheduler.py`
- **Storage:** Google Cloud Storage (uploads, outputs, state)
- **Deployment:** Docker container on Google Cloud Run
- **Auth:** Flask-Login with role-based access (Admin, Planner, MfgEng, CustomerService, Guest)

---

## Project Structure

```
EstradaBot/
├── backend/
│   ├── app.py                  # Flask application entry point
│   ├── gcs_storage.py          # GCS helper module
│   ├── data_loader.py          # File parsing and validation
│   ├── validators.py           # Input validation
│   ├── algorithms/
│   │   ├── des_scheduler.py    # Main DES scheduling engine (core logic)
│   │   └── scheduler.py        # Scheduling utilities
│   ├── exporters/
│   │   ├── excel_exporter.py   # Excel report generation
│   │   └── impact_analysis_exporter.py
│   ├── parsers/                # Input file parsers (Sales Order, Hot List, etc.)
│   ├── templates/              # Jinja2 HTML templates
│   └── static/                 # CSS and JavaScript
├── deployment/                 # Server config examples
├── Dockerfile                  # Cloud Run container build
├── requirements.txt            # Python dependencies
├── .env.example                # Environment variable template
└── DEPLOY.md                   # Deployment guide and infrastructure details
```

---

## Key Conventions

### Git Workflow
- **Main branch:** `master`
- **Feature branches:** Create a new branch for each feature or fix
- **Pull requests:** All changes to `master` go through a PR with review (for team members)
- **Owner direct deploy:** When the project owner (InnerLooper85) explicitly requests a deploy during a Claude Code session, Claude may merge directly to `master` and push without creating a PR. This bypasses GitHub review for speed. All other contributors must still use PRs.
- **Commit messages:** Short, descriptive — explain the "why" not just the "what"
- Never force push to `master`
- Always pull the latest `master` before creating a new branch

### Code Style
- Python code follows PEP 8
- Use descriptive variable and function names
- Add docstrings to new functions and classes
- Keep Flask routes in `backend/app.py`
- Keep scheduling logic in `backend/algorithms/`
- Keep file parsing in `backend/parsers/`
- Keep export logic in `backend/exporters/`

### File Handling
- All file I/O goes through GCS in production (`backend/gcs_storage.py`)
- Local file paths are only for development
- Input files are Excel (.xlsx) — use openpyxl/pandas for reading
- Output files are Excel (.xlsx) — use openpyxl for writing

### Environment Variables
- Never hardcode secrets — use environment variables
- Reference `.env.example` for the full list of required variables
- Production secrets are managed in GCP (env.yaml, not committed to git)

---

## Sensitive Files — DO NOT Commit

- `.env` — local environment variables with passwords
- `env.yaml` — production environment variables
- Any file containing passwords, API keys, or secrets
- `DEPLOY.md` contains credentials — it is currently committed but should be treated as sensitive reference material

---

## Testing Changes Locally

```bash
# Create/activate virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Copy and configure environment
cp .env.example .env
# Edit .env with your local settings

# Run the development server
python run_production.py
```

The app will be available at http://localhost:5000

---

## Deploying to Production

Deployment is done via Google Cloud Run from the repo root:

```bash
gcloud run deploy estradabot --source . --region us-central1 --allow-unauthenticated
```

### Owner Direct Deploy (fast path)

When the project owner says "deploy", "merge and deploy", "push to production", or similar during a Claude Code session, follow this streamlined process:

1. Complete the **Versioning Protocol** below (version badge, update log, CLAUDE.md)
2. Commit changes on the feature branch and push
3. Switch to `master`, pull latest, merge the feature branch
4. Push `master` to origin
5. Report: "Merged to master and pushed. Ready for `gcloud run deploy`."

**Note:** The actual `gcloud run deploy` command must be run by the owner on their local machine (Claude Code does not have gcloud credentials). Claude's job is to get `master` ready.

### Standard Deploy (team members)

**Before deploying:**
1. Ensure all tests pass locally
2. Ensure your changes are committed and pushed
3. Create a PR and get it reviewed/approved
4. Merge via GitHub
5. Coordinate with the team — only one deploy at a time
6. Verify the live site after deployment: https://estradabot.biz

---

## Common Tasks Reference

| Task | Where to look |
|------|---------------|
| Add a new input parser | `backend/parsers/` — follow existing parser patterns |
| Modify scheduling logic | `backend/algorithms/des_scheduler.py` |
| Add a new page/route | `backend/app.py` + `backend/templates/` |
| Change export format | `backend/exporters/` |
| Update frontend styles | `backend/static/` |
| Modify GCS integration | `backend/gcs_storage.py` |
| Update dependencies | `requirements.txt` + rebuild container |

---

## Versioning Protocol (MANDATORY for production releases)

**Current Version:** MVP 1.7

When merging changes to `master` that will be deployed to production, you MUST:

1. **Increment the version badge** in `backend/templates/base.html`
   - Find the `<span class="badge bg-info ...>MVP X.Y</span>` in the navbar brand
   - Bump the version number (e.g., MVP 1.1 → MVP 1.2)
   - Use minor bumps (1.1 → 1.2) for feature additions and fixes
   - Use major bumps (1.x → 2.0) only when the product owner declares a new major release

2. **Update the Update Log page** in `backend/templates/update_log.html`
   - Add a new version section at the top of the "Version History" card (above the previous version)
   - Include the version badge, date, and a short release name
   - List each change as a `<li class="list-group-item">` with a description
   - Follow the existing format (see MVP 1.0 and MVP 1.1 entries as examples)

3. **Update this file** — change "Current Version" above to match the new version

**Do NOT deploy to production without completing all three steps.**

---

## Team Coordination

- Before starting work on a feature, check the GitHub project board and open PRs
- If someone else is working on the same area, coordinate before making changes
- Use descriptive branch names: `feature/add-rework-tracking`, `fix/hot-list-parsing`
- Keep PRs focused — one feature or fix per PR
- Review teammates' PRs promptly
