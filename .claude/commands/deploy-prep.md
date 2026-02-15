Prepare a release for deployment by completing all 3 steps of the Versioning Protocol.

## Steps (all 3 are MANDATORY)

### Step 1: Bump the version badge
- Open `backend/templates/base.html`
- Find the `<span class="badge bg-info ...>MVP X.Y</span>` in the navbar brand (line ~176)
- Increment the minor version (e.g., MVP 1.7 → MVP 1.8)
- Only use a major bump (e.g., 1.x → 2.0) if the product owner explicitly declared one

### Step 2: Update the Update Log
- Open `backend/templates/update_log.html`
- Add a new version section **at the top** of the "Version History" card (above the previous version entry)
- Include: version badge, today's date, a short release name
- List each change as a `<li class="list-group-item">` with a description
- Follow the existing format of previous version entries in the file

### Step 3: Update CLAUDE.md
- Open `CLAUDE.md`
- Find the line `**Current Version:** MVP X.Y` under the Versioning Protocol section
- Update it to match the new version from Step 1

## After completing all 3 steps
- Report the version change (old → new)
- List what was included in the update log entry
- Remind the developer: "Ready for commit. After merge to master, deploy with `gcloud run deploy`."

## Rules
- Do NOT skip any step. All 3 must be done together.
- Do NOT deploy without completing all 3.
- Ask the developer what changes should be listed in the update log if unclear.
