# FIXES.md — Bug Fixes Log

All bugs identified and fixed during Phase 2 audit of the `hng14-stage2-devops` project.

---

## API Service (`api/`)

### Fix 1 — Hardcoded Redis connection
- **File:** `api/main.py`, line 8
- **Problem:** Redis host and port were hardcoded as `redis.Redis(host="localhost", port=6379)`. This breaks inside a container where the Redis service runs on a different hostname (e.g. `redis` in Docker Compose).
- **Fix:** Replaced with environment variables:
  ```python
  REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
  REDIS_PORT = int(os.environ.get("REDIS_PORT", 6379))
  REDIS_PASSWORD = os.environ.get("REDIS_PASSWORD", None)
  r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD, decode_responses=True)
  ```

### Fix 2 — REDIS_PASSWORD defined in .env but never used
- **File:** `api/.env`, line 1 + `api/main.py`, line 8
- **Problem:** The `.env` file defined `REDIS_PASSWORD=supersecretpassword123` but the code never read it — the Redis client was instantiated without any password parameter.
- **Fix:** Added `REDIS_PASSWORD` to the `os.environ.get()` calls and passed it to `redis.Redis(password=...)`.

### Fix 3 — Hardcoded production credential in .env
- **File:** `api/.env`, line 1
- **Problem:** The `.env` file contained `REDIS_PASSWORD=supersecretpassword123` — a hardcoded credential committed to source control. Also `APP_ENV=production` which is wrong for a dev config.
- **Fix:** Changed to `REDIS_PASSWORD=` (empty for local dev) and `APP_ENV=development`. Production credentials should be injected via CI/CD or secrets management.

### Fix 4 — "Not found" response returned HTTP 200
- **File:** `api/main.py`, line 21
- **Problem:** When a job ID is not found, the API returned `{"error": "not found"}` with an implicit `200 OK` status code, which is semantically wrong and confusing for clients.
- **Fix:** Changed to `return JSONResponse(status_code=404, content={"error": "not found"})`.

### Fix 5 — Queue key mismatch risk
- **File:** `api/main.py`, line 13
- **Problem:** The Redis list key used was `"job"` which is ambiguous and collides with the hash key pattern `"job:{id}"`. Combined with the worker reading from the same key, any typo or inconsistency causes silent failures.
- **Fix:** Renamed queue key from `"job"` to `"job_queue"` in both API and worker for clarity and safety.

### Fix 6 — Manual `.decode()` calls on Redis values
- **File:** `api/main.py`, line 22
- **Problem:** Redis returns `bytes` by default, requiring manual `.decode()` on every read. This is error-prone and produces crashes if someone forgets to decode.
- **Fix:** Added `decode_responses=True` to the Redis client constructor, which automatically returns strings.

### Fix 7 — Missing `python-dotenv` dependency
- **File:** `api/requirements.txt`
- **Problem:** The `.env` file exists but `python-dotenv` was not listed in `requirements.txt`. Without it, `dotenv` cannot auto-load the `.env` file during local development.
- **Fix:** Added `python-dotenv` to `api/requirements.txt`.

---

## Worker Service (`worker/`)

### Fix 8 — Hardcoded Redis connection
- **File:** `worker/worker.py`, line 6
- **Problem:** Same as Fix 1 — `redis.Redis(host="localhost", port=6379)` breaks in containers.
- **Fix:** Replaced with environment variables `REDIS_HOST`, `REDIS_PORT`, `REDIS_PASSWORD` with sane defaults.

### Fix 9 — `signal` imported but never used for graceful shutdown
- **File:** `worker/worker.py`, line 4
- **Problem:** The `signal` module was imported but no signal handlers were registered. A `SIGTERM` from Docker/Kubernetes would kill the worker mid-job with no cleanup.
- **Fix:** Implemented `SIGINT`/`SIGTERM` handlers that set a `shutdown` flag, allowing the current job to complete before exiting.

### Fix 10 — Queue key mismatch with API
- **File:** `worker/worker.py`, line 15
- **Problem:** The worker used `r.brpop("job", ...)` but this must match the key the API pushes to. After renaming the API key (Fix 5), the worker must also be updated.
- **Fix:** Changed from `"job"` to `"job_queue"`.

### Fix 11 — No error handling around Redis operations
- **File:** `worker/worker.py`, lines 14–18
- **Problem:** If Redis goes down temporarily, the worker crashes immediately with an unhandled `ConnectionError`. In containers, this causes restart loops.
- **Fix:** Wrapped the main loop in `try/except` for `redis.exceptions.ConnectionError` with a 5-second retry delay.

### Fix 12 — No "processing" intermediate state
- **File:** `worker/worker.py`, line 9
- **Problem:** Jobs went straight from `queued` to `completed` with no intermediate state. During the 2-second simulated work period, the frontend shows `queued` instead of `processing`.
- **Fix:** Added `r.hset(f"job:{job_id}", "status", "processing")` before the work begins.

### Fix 13 — `print()` instead of proper logging
- **File:** `worker/worker.py`, lines 9, 12
- **Problem:** Using `print()` for output. In containers, `print()` output may be buffered and lost. Proper logging includes timestamps and log levels.
- **Fix:** Replaced with Python `logging` module with `INFO` level and timestamped format.

### Fix 14 — Infinite loop with no exit path
- **File:** `worker/worker.py`, line 14
- **Problem:** `while True:` with no break condition means the worker can only be stopped by killing the process. Combined with no signal handling, this causes ungraceful shutdowns.
- **Fix:** Changed to `while not shutdown:` using the signal-controlled flag.

### Fix 15 — Manual `.decode()` on Redis values
- **File:** `worker/worker.py`, line 18
- **Problem:** Same as Fix 6 — `job_id.decode()` is needed because `decode_responses` was not set.
- **Fix:** Added `decode_responses=True` to the Redis client. Removed manual `.decode()` call (brpop with decode_responses returns strings directly).

---

## Frontend Service (`frontend/`)

### Fix 16 — Hardcoded API URL (`localhost`)
- **File:** `frontend/app.js`, line 6
- **Problem:** `const API_URL = "http://localhost:8000"` — this breaks inside a container where the API service is accessible via a service hostname (e.g. `http://api:8000`), not `localhost`.
- **Fix:** Changed to `const API_URL = process.env.API_URL || "http://localhost:8000"`.

### Fix 17 — Hardcoded port
- **File:** `frontend/app.js`, line 29
- **Problem:** Port `3000` was hardcoded. Container orchestrators often need to set arbitrary ports.
- **Fix:** Changed to `const PORT = process.env.PORT || 3000`.

### Fix 18 — Wrong HTTP error status codes
- **File:** `frontend/app.js`, lines 16, 25
- **Problem:** API proxy errors returned `500 Internal Server Error`, but the frontend itself isn't broken — the upstream API is unreachable. The correct status is `502 Bad Gateway`.
- **Fix:** Changed `res.status(500)` to `res.status(502)` with a descriptive message `"Failed to communicate with API service"`.

### Fix 19 — No error logging
- **File:** `frontend/app.js`, lines 15–17, 24–26
- **Problem:** Errors were silently swallowed. When the API is unreachable, the catch block returned a generic error with no server-side logging, making debugging impossible.
- **Fix:** Added `console.error("Error submitting job:", err.message)` and equivalent for the status endpoint.

### Fix 20 — `app.listen()` not bound to `0.0.0.0`
- **File:** `frontend/app.js`, line 29
- **Problem:** `app.listen(3000)` binds to the default interface. Inside a Docker container, if the default is `127.0.0.1`, the service is unreachable from outside the container.
- **Fix:** Changed to `app.listen(PORT, '0.0.0.0', ...)`.

---

## Summary

| # | Service | File | Bug Category |
|---|---------|------|--------------|
| 1 | API | `main.py` | Hardcoded values |
| 2 | API | `main.py` + `.env` | Unused env var |
| 3 | API | `.env` | Hardcoded credential |
| 4 | API | `main.py` | Wrong HTTP status |
| 5 | API | `main.py` | Ambiguous key name |
| 6 | API | `main.py` | Missing decode_responses |
| 7 | API | `requirements.txt` | Missing dependency |
| 8 | Worker | `worker.py` | Hardcoded values |
| 9 | Worker | `worker.py` | Dead code (unused import) |
| 10 | Worker | `worker.py` | Key mismatch |
| 11 | Worker | `worker.py` | No error handling |
| 12 | Worker | `worker.py` | Missing intermediate state |
| 13 | Worker | `worker.py` | No structured logging |
| 14 | Worker | `worker.py` | No graceful shutdown |
| 15 | Worker | `worker.py` | Missing decode_responses |
| 16 | Frontend | `app.js` | Hardcoded localhost |
| 17 | Frontend | `app.js` | Hardcoded port |
| 18 | Frontend | `app.js` | Wrong HTTP status |
| 19 | Frontend | `app.js` | Silent error swallowing |
| 20 | Frontend | `app.js` | Listen bind address |
