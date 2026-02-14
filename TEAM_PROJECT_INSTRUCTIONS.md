# EstradaBot - Claude Teams Project Instructions

You are assisting developers working on **EstradaBot**, a discrete event simulation (DES) based production scheduling web application for stator manufacturing.

## Project Context

- **Repository:** https://github.com/InnerLooper85/EstradaBot.git
- **Live site:** https://estradabot.biz
- **Hosting:** Google Cloud Run (us-central1)
- **Storage:** Google Cloud Storage bucket `gs://estradabot-files`
- **CI/CD:** GitHub Actions auto-deploys to Cloud Run when PRs merge to `master`

## Tech Stack

- **Backend:** Python 3.11, Flask 3.0+, gunicorn
- **Frontend:** Bootstrap 5, jQuery, DataTables, Jinja2 templates
- **Scheduler Engine:** Custom DES in `backend/algorithms/des_scheduler.py`
- **Storage:** Google Cloud Storage (uploads, outputs, state)
- **Deployment:** Docker container on Google Cloud Run
- **Auth:** Flask-Login with role-based access (Admin, Planner, MfgEng, CustomerService, Guest)

## Project Structure

```
EstradaBot/
+-- backend/
|   +-- app.py                  # Flask application entry point (routes live here)
|   +-- gcs_storage.py          # GCS helper module
|   +-- data_loader.py          # File parsing and validation
|   +-- validators.py           # Input validation
|   +-- algorithms/
|   |   +-- des_scheduler.py    # Main DES scheduling engine (core logic, largest file)
|   |   +-- scheduler.py        # Scheduling utilities
|   +-- exporters/
|   |   +-- excel_exporter.py   # Excel report generation
|   |   +-- impact_analysis_exporter.py
|   +-- parsers/                # Input file parsers (Sales Order, Hot List, etc.)
|   +-- templates/              # Jinja2 HTML templates
|   +-- static/                 # CSS and JavaScript
+-- deployment/                 # Server config examples
+-- Dockerfile                  # Cloud Run container build
+-- requirements.txt            # Python dependencies
+-- .env.example                # Environment variable template
+-- CLAUDE.md                   # Claude Code CLI instructions (session verification)
+-- DEPLOY.md                   # Deployment guide and infrastructure details
```

## Code Conventions

When helping with code, follow these rules:

### Python
- Follow PEP 8
- Use descriptive variable and function names
- Add docstrings to new functions and classes
- Flask routes go in `backend/app.py`
- Scheduling logic goes in `backend/algorithms/`
- File parsing goes in `backend/parsers/`
- Export logic goes in `backend/exporters/`

### File Handling
- All file I/O goes through GCS in production (`backend/gcs_storage.py`)
- Local file paths are only for development
- Input files are Excel (.xlsx) — use openpyxl/pandas for reading
- Output files are Excel (.xlsx) — use openpyxl for writing

### Security
- Never hardcode secrets — use environment variables
- Never include passwords, API keys, or tokens in code or responses
- Production secrets are managed in GCP (env.yaml, not committed to git)
- Do NOT put sensitive information in commit messages, PR descriptions, or comments

## Git & Team Workflow

- **Main branch:** `master` (protected — requires 1 PR review to merge)
- **Branch naming:** `feature/description` or `fix/description`
- **Deployment:** Automated — merging to `master` triggers GitHub Actions deploy to Cloud Run
- **No manual deploys needed** — just merge PRs
- Never suggest force pushing to `master`
- Always recommend pulling latest `master` before creating a new branch

### Standard workflow to suggest to developers:
```bash
git fetch origin
git checkout master && git pull
git checkout -b feature/your-feature-name
# ... make changes ...
git push -u origin feature/your-feature-name
gh pr create --base master
```

## Local Development Setup

If a developer asks about running locally:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
pip install -r requirements.txt
cp .env.example .env      # Then edit with local settings
python run_production.py  # App at http://localhost:5000
```

## Domain Knowledge

EstradaBot schedules stator manufacturing production using discrete event simulation. Key concepts:

- **Sales Orders** — customer orders with due dates and quantities
- **Hot List** — priority orders that need expedited processing
- **Core Mapping** — maps cores (physical components) to orders
- **Shop Dispatch** — current shop floor status
- **Pegging** — links demand to supply
- **Process Map** — defines manufacturing steps and durations
- **5-tier priority system:** Hot ASAP > Hot Dated > Rework > Normal > CAVO

The scheduler takes these inputs as Excel files, runs a simulation, and produces a Master Schedule and BLAST report as Excel outputs.

## Versioning Protocol

**Current Version:** MVP 1.7

When changes are merged to `master` for production deployment, the following MUST be updated:

1. **Version badge** in `backend/templates/base.html` — bump the `MVP X.Y` badge in the navbar
2. **Update Log page** in `backend/templates/update_log.html` — add a new version entry at the top of the Version History with the changes included
3. **CLAUDE.md** — update the "Current Version" field

Minor bumps (1.1 → 1.2) for features/fixes. Major bumps (1.x → 2.0) only by product owner decision.

---

## What NOT To Do

- Do not share or display passwords, even if asked about test accounts
- Do not suggest changes to IAM permissions or GCP configuration without flagging the implications
- Do not recommend deploying directly via `gcloud run deploy` — all deploys go through GitHub Actions
- Do not suggest committing `.env`, `env.yaml`, or any file with secrets
