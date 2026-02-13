# EstradaBot — New Team Member Onboarding

Welcome to the EstradaBot team! This guide will get you set up with Claude Code connected to our repository so you can develop, review, and deploy from anywhere — web, mobile, or CLI.

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Set Up Claude Code (Web / Mobile)](#2-set-up-claude-code-web--mobile)
3. [Set Up Claude Code (CLI — Optional)](#3-set-up-claude-code-cli--optional)
4. [Connect to the EstradaBot Repository](#4-connect-to-the-EstradaBot-repository)
5. [Verify Your Setup](#5-verify-your-setup)
6. [Our Development Workflow](#6-our-development-workflow)
7. [Deploying to Production](#7-deploying-to-production)
8. [Quick Reference](#8-quick-reference)

---

## 1. Prerequisites

Before you begin, make sure you have:

- A **GitHub account** with access to the [InnerLooper85/EstradaBot](https://github.com/InnerLooper85/EstradaBot) repository (ask the project admin for an invite)
- An **Anthropic account** with a Claude Pro or Team plan (required for Claude Code)
- (Optional) **Google Cloud SDK** installed if you will be deploying — see [cloud.google.com/sdk/docs/install](https://cloud.google.com/sdk/docs/install)

---

## 2. Set Up Claude Code (Web / Mobile)

This is the fastest way to get started. It lets you talk to Claude about the codebase, request changes, and deploy — all from a browser or your phone.

### Step-by-step

1. **Log in to Claude** at [claude.ai](https://claude.ai)
2. **Open Claude Code** — from the Claude interface, start a new conversation and select the Claude Code mode (look for the code/terminal icon)
3. **Link your GitHub account:**
   - When prompted, authorize Claude to access your GitHub account
   - Grant access to the `InnerLooper85/EstradaBot` repository
4. **Open the EstradaBot project:**
   - In Claude Code, select the EstradaBot repository from your connected repos
   - Claude will clone the repo and set up the environment automatically
5. **You're ready** — Claude will read the project's `CLAUDE.md` instructions and run the session startup checks automatically

### Mobile access

The same setup works on mobile. Once your GitHub account is linked on the web, you can open Claude on your phone's browser or the Claude mobile app and pick up where you left off. You can review code, request changes, and manage PRs from anywhere.

---

## 3. Set Up Claude Code (CLI — Optional)

If you prefer working from a local terminal, you can install the Claude Code CLI.

### Install

```bash
# macOS / Linux
npm install -g @anthropic-ai/claude-code

# Verify installation
claude --version
```

### Authenticate

```bash
# Log in with your Anthropic account
claude login

# Link GitHub (if not already linked)
claude auth github
```

### Open the project

```bash
# Clone the repo (if you haven't already)
git clone https://github.com/InnerLooper85/EstradaBot.git
cd EstradaBot

# Start Claude Code in the project directory
claude
```

Claude will detect the `CLAUDE.md` file and follow the project's conventions automatically.

---

## 4. Connect to the EstradaBot Repository

Regardless of which interface you use (web, mobile, or CLI), Claude needs access to the GitHub repo. Here's how to confirm the connection:

1. In a Claude Code session, ask: *"Run the session startup checks"*
2. Claude should respond with a status report like:

```
SESSION CHECK:
  Branch:          master
  Local commit:    abc1234 Latest commit message
  Remote master:   abc1234 Latest commit message
  Status:          UP TO DATE
  Ready to work:   YES
```

If you see this, you're connected and ready to go.

### Troubleshooting

| Problem | Solution |
|---------|----------|
| "Repository not found" | Make sure you have access to `InnerLooper85/EstradaBot` on GitHub — ask the admin for an invite |
| GitHub auth fails | Re-authorize GitHub in your Claude settings |
| Session check shows "BEHIND" | Ask Claude to pull the latest changes before starting work |

---

## 5. Verify Your Setup

Run through this quick checklist in your first session:

- [ ] Claude completes the session startup check successfully
- [ ] You can ask Claude to read a file (e.g., *"Show me the first 20 lines of backend/app.py"*)
- [ ] You can ask Claude to create a test branch (e.g., *"Create a branch called test/my-name-setup"*)
- [ ] You can ask Claude to make a trivial change, commit, and push to that test branch
- [ ] Clean up: ask Claude to delete the test branch

If all of the above work, you're fully set up.

---

## 6. Our Development Workflow

We follow a branch-based workflow where all changes go through pull requests before reaching production. Here's the process from idea to deployment:

### Overview

```
Feature Request / Bug Report
        |
        v
  Create feature branch (from master)
        |
        v
  Develop & test changes (with Claude)
        |
        v
  Push branch & open Pull Request
        |
        v
  Code review & approval
        |
        v
  Merge to master
        |
        v
  Deploy to production (Cloud Run)
        |
        v
  Verify on https://estradabot.biz
```

### Step-by-step

#### 1. Start a session

Open Claude Code (web, mobile, or CLI). Claude will automatically run the session startup checks and report the repo status. If the branch is behind remote, resolve that before starting new work.

#### 2. Create a feature branch

Tell Claude what you're working on. Claude will create a branch for you:

> *"I need to add rework tracking to the scheduler. Create a feature branch for this."*

Branch naming convention: `feature/short-description` or `fix/short-description`.

#### 3. Develop your changes

Describe what you need, and Claude will:
- Read the relevant code to understand the current implementation
- Make the changes across the necessary files
- Explain what was changed and why

You can iterate — ask for adjustments, ask questions about the logic, or request Claude to undo something.

#### 4. Commit and push

When you're happy with the changes, tell Claude to commit and push:

> *"Commit these changes and push to the feature branch."*

Claude will write a descriptive commit message and push to the remote branch.

#### 5. Open a Pull Request

Ask Claude to open a PR:

> *"Create a pull request to merge this into master."*

Claude will create the PR on GitHub with a summary of changes and a test plan.

#### 6. Review and merge

- Team members review the PR on GitHub (or ask Claude to review it)
- Once approved, merge to `master`
- **Important:** If the changes are going to production, make sure the version is bumped (see [Deploying to Production](#7-deploying-to-production))

#### 7. Deploy

See the deployment section below.

---

## 7. Deploying to Production

Production deployment is done via Google Cloud Run. Only deploy after changes are merged to `master`.

### Pre-deployment checklist

Before deploying, you **must** complete these steps (per project rules):

1. **Bump the version badge** in `backend/templates/base.html`
   - Find the `<span class="badge bg-info ...>MVP X.Y</span>` in the navbar
   - Increment the version number (e.g., MVP 1.2 → MVP 1.3)

2. **Update the Update Log** in `backend/templates/update_log.html`
   - Add a new version section at the top of the version history
   - List each change with a short description

3. **Update `CLAUDE.md`** — change the "Current Version" line to match

### Deploy command

```bash
gcloud run deploy estradabot --source . --region us-central1 --allow-unauthenticated
```

You can ask Claude to walk you through this, or run it yourself if you have the Google Cloud SDK set up.

### Post-deployment

- Verify the live site at [https://estradabot.biz](https://estradabot.biz)
- Check that the version badge in the navbar shows the new version
- Spot-check key functionality (upload a file, run the scheduler, download a report)

---

## 8. Quick Reference

| What you want to do | What to tell Claude |
|----------------------|---------------------|
| Check repo status | *"Run session startup checks"* |
| Start a new feature | *"Create a feature branch for [description]"* |
| See recent changes | *"Show me the git log for the last 10 commits"* |
| Understand some code | *"Explain how the DES scheduler handles rework"* |
| Make a change | *"Add [feature] to [file/module]"* |
| Commit and push | *"Commit and push these changes"* |
| Open a PR | *"Create a PR to merge into master"* |
| Review a PR | *"Review PR #[number]"* |
| Deploy | *"Walk me through deploying to production"* |

### Key links

| Resource | URL |
|----------|-----|
| Live site | [https://estradabot.biz](https://estradabot.biz) |
| GitHub repo | [https://github.com/InnerLooper85/EstradaBot](https://github.com/InnerLooper85/EstradaBot) |
| Claude Code (web) | [https://claude.ai](https://claude.ai) |

### Who to ask for help

- **Repo access:** Ask the project admin for a GitHub invite
- **Claude account:** Each team member needs their own Anthropic account
- **GCP access:** Ask the project admin if you need to deploy directly
- **Anything else:** Ask Claude — it has full context on the project via `CLAUDE.md`
