# EstradaBot - Deployment Guide

## Live URLs

| URL | Status |
|-----|--------|
| https://estradabot-983132566705.us-central1.run.app | Live |
| https://estradabot.biz | Pending DNS/SSL (15-30 min) |
| https://www.estradabot.biz | Pending DNS/SSL |

## Test User Accounts

| Username | Password | Role |
|----------|----------|------|
| admin | EstradaAdmin2026! | Admin |
| MfgEng | MfgEng2026! | User |
| Planner | Planner2026! | User |
| CustomerService | CustSvc2026! | User |
| Guest | Guest2026! | User |

## Google Cloud Project

- **Project ID:** project-20e62326-f8a0-47bc-be6
- **Project Number:** 983132566705
- **Region:** us-central1

## Deployment Commands

### Deploy Updates

```bash
cd "C:\Users\SeanFilipow\DD Scheduler Bot"
gcloud run deploy estradabot --source . --region us-central1 --allow-unauthenticated --env-vars-file env.yaml --memory 512Mi --timeout 300 --project=project-20e62326-f8a0-47bc-be6
```

### View Logs

```bash
gcloud run logs read estradabot --region us-central1 --project=project-20e62326-f8a0-47bc-be6 --limit=50
```

### Check Domain Status

```bash
gcloud beta run domain-mappings describe --domain estradabot.biz --region us-central1 --project=project-20e62326-f8a0-47bc-be6
```

## DNS Configuration (Namecheap)

### Root Domain (estradabot.biz)

| Type | Host | Value |
|------|------|-------|
| A | @ | 216.239.32.21 |
| A | @ | 216.239.34.21 |
| A | @ | 216.239.36.21 |
| A | @ | 216.239.38.21 |

### WWW Subdomain

| Type | Host | Value |
|------|------|-------|
| CNAME | www | ghs.googlehosted.com |

### Optional IPv6

| Type | Host | Value |
|------|------|-------|
| AAAA | @ | 2001:4860:4802:32::15 |
| AAAA | @ | 2001:4860:4802:34::15 |
| AAAA | @ | 2001:4860:4802:36::15 |
| AAAA | @ | 2001:4860:4802:38::15 |

## Environment Variables

Environment variables are stored in `env.yaml` (not committed to git):

- SECRET_KEY - Flask session encryption
- ADMIN_USERNAME / ADMIN_PASSWORD - Admin account
- USERS - Additional user accounts
- BEHIND_PROXY - Set to true for Cloud Run

## Cost Estimate

Cloud Run charges only when handling requests:
- Free tier: 2 million requests/month
- Expected cost for 4 test users: $0-5/month

## Stopping the Service

To stop and avoid all charges:

```bash
gcloud run services delete estradabot --region us-central1 --project=project-20e62326-f8a0-47bc-be6
```

## Files Overview

| File | Purpose |
|------|---------|
| Dockerfile | Container build configuration |
| .dockerignore | Files excluded from Docker build |
| .gcloudignore | Files excluded from Cloud Build |
| env.yaml | Environment variables (not in git) |
| requirements.txt | Python dependencies |
