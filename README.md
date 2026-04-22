# HNG Stage 2 — DevOps sample app

This repository contains a small stack: an API, a worker, and a frontend. Below are prerequisites, commands to run the stack on a clean machine, expected successful startup indications, and a final review checklist.

**Prerequisites**

- Docker: 20.x or later
- Docker Compose (v2) — `docker compose` command
- Node.js: 20.x (for frontend tooling)
- npm: bundled with Node.js
- Python: 3.11 (for local development of the `api` and tests)
- pip: Python package manager

**Quick setup (clean machine)**

1. Clone the repo:

   git clone https://github.com/chukwukelu2023/hng14-stage2-devops.git
   cd hng14-stage2-devops

2. Create a local `.env` file (do NOT commit this file). Example contents:

   REDIS_HOST=redis
   REDIS_PORT=6379
   REDIS_PASSWORD=testpassword
   API_URL=http://api:8000
   FRONTEND_PORT=3000
   APP_ENV=development

3. Start the full stack with Docker Compose:

   docker compose up -d --build

4. Follow logs (optional):

   docker compose logs -f

5. Verify services are running:

   docker compose ps

6. API health check (once services are up):

   curl -s http://localhost:8000/health

   Expected response: {"status":"ok"}

7. Create a job via the API (or frontend endpoint):

   curl -s -X POST http://localhost:8000/jobs -H "Content-Type: application/json" -d '{}'

   Expected response: {"job_id":"<uuid>"}

8. Poll job status:

   curl -s http://localhost:8000/jobs/<job_id>

   Expected response while queued: {"job_id":"<job_id>","status":"queued"}
   Expected final response when processed: {"job_id":"<job_id>","status":"completed"}

**What a successful startup looks like**

- `docker compose ps` shows containers for `api`, `worker`, `frontend`, and `redis` in `healthy` or `running` state.
- `curl http://localhost:8000/health` returns `{"status":"ok"}`.
- Creating a job returns a `job_id` and the worker logs show the job being picked from the queue and processed.
- Frontend (if present) is reachable at `http://localhost:3000` and can create jobs through the UI.

**Final review checklist (must pass before merging)**

- `.env` must never be committed. Confirm `.gitignore` contains `.env` and check git history for accidental commits.
- No hardcoded secrets in repository files (YAML workflows, `api/main.py`, `worker/worker.py`, frontend files). Replace any secrets with references to GitHub Actions secrets or environment variables.
- Tests: `api/tests/` contains at least three tests (create job, fetch job status, invalid job → 404).
- CI workflow present at `.github/workflows/ci.yml` implementing lint, tests, build, security scan, integration test, and deploy stages.

# hng14-stage2-devops
