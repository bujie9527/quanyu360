# AI Workforce Platform Production Deployment

## 1. Server Basics

| Item | Value |
|------|-------|
| Server IP | `<your_server_ip>` |
| SSH User | `<your_ssh_user>` |
| SSH Port | `22` |

Security note: never store plaintext passwords or tokens in repository files.

---

## 2. Requirements

- Ubuntu 22.04 LTS
- Docker Engine + Docker Compose plugin
- Git
- Outbound network access for image/package/model APIs

Recommended resources: 4 vCPU, 8 GB RAM (16 GB preferred), 50 GB disk.

---

## 3. First-Time Setup

```bash
ssh <your_ssh_user>@<your_server_ip>
sudo apt-get update
sudo apt-get install -y git ca-certificates curl gnupg lsb-release
```

Install Docker according to official docs, then verify:

```bash
docker --version
docker compose version
git --version
```

---

## 4. Project Directory

```bash
sudo mkdir -p /opt/ai-workforce
sudo chown -R <your_ssh_user>:<your_ssh_user> /opt/ai-workforce
cd /opt/ai-workforce
```

Clone repository (first time only):

```bash
git clone <your_repo_url> .
```

---

## 5. Environment File

```bash
cd /opt/ai-workforce
cp .env.production.example .env.production
```

Must configure at least:

- `POSTGRES_PASSWORD`
- `REDIS_PASSWORD`
- `JWT_SECRET_KEY`
- `INTERNAL_API_KEY`
- `DATABASE_URL`
- `*_REDIS_URL`
- `NEXT_PUBLIC_*`
- `CORS_ORIGINS`

---

## 6. Service Management

```bash
cd /opt/ai-workforce
sh tools/scripts/start.sh
sh tools/scripts/status.sh
sh tools/scripts/dc.sh logs -f nginx
```

---

## 7. Health Check

```bash
SMOKE_CHECK_MODE=proxy SMOKE_CHECK_BASE_URL=http://127.0.0.1 sh tools/scripts/smoke-check.sh
```

---

## 8. Access URLs

| Entry | URL |
|------|-----|
| Frontend | `http://<your_server_ip>/` |
| Login | `http://<your_server_ip>/login` |

If you use a domain, switch all `NEXT_PUBLIC_*` and `CORS_ORIGINS` to that domain.

---

## 9. Production Release Standard

Production update has only one path:

`Git(main) -> GitHub Actions -> deploy-from-git.sh`

### 9.1 Automatic Deploy (Preferred)

1) Push code to `main`.
2) Workflow `Deploy Production` runs after CI success.
3) Workflow SSHes into server and runs:

```bash
cd /opt/ai-workforce
BRANCH=main ENV_FILE_PATH=.env.production SMOKE_CHECK_MODE=proxy SMOKE_CHECK_BASE_URL=http://127.0.0.1 sh tools/scripts/deploy-from-git.sh
```

`deploy-from-git.sh` does:

- `git fetch --prune origin`
- `git checkout main`
- `git reset --hard origin/main`
- `sh tools/scripts/deploy.sh`
- `sh tools/scripts/smoke-check.sh`

Deploy records:

- `.deploy-history/success.log`
- `.deploy-history/recent-successful-shas.log`

### 9.2 Manual Deploy (Emergency Only)

```bash
ssh <your_ssh_user>@<your_server_ip>
cd /opt/ai-workforce
BRANCH=main ENV_FILE_PATH=.env.production SMOKE_CHECK_MODE=proxy SMOKE_CHECK_BASE_URL=http://127.0.0.1 sh tools/scripts/deploy-from-git.sh
```

### 9.3 Forbidden Actions in Production

- Do not use `tools/scripts/sync-to-server.sh` as a release method.
- Do not upload code manually to replace Git sync.
- Do not skip `deploy-from-git.sh` and restart single containers as a release.

---

## 10. Rollback by Commit

```bash
ssh <your_ssh_user>@<your_server_ip>
cd /opt/ai-workforce
git log --oneline -n 20
sh tools/scripts/rollback-to-sha.sh <stable_commit_sha> main
```

Rollback script executes:

- `git reset --hard <stable_commit_sha>`
- `sh tools/scripts/deploy.sh`
- `sh tools/scripts/smoke-check.sh`

Rollback records are written to `.deploy-history/rollback.log`.

---

## 11. Release Checklists

### 11.1 Pre-Deploy

- `git rev-parse --is-inside-work-tree` is true
- `git fetch --prune origin` succeeds
- `.env.production` exists and secrets are complete
- Enough disk space (>=20% free)
- Docker and Compose healthy

### 11.2 Post-Deploy

```bash
sh tools/scripts/dc.sh ps
SMOKE_CHECK_MODE=proxy SMOKE_CHECK_BASE_URL=http://127.0.0.1 sh tools/scripts/smoke-check.sh
```

Business checks:

- `/login` works
- `/matrix-planner` works
- `/matrix-sites` works
- Create `matrix_site` project successfully

