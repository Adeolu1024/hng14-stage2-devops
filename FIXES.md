# FIXES.md

## Bug 1: Hardcoded Redis Host in Worker

- **File:** `worker/worker.py`
- **Line:** 6
- **Problem:** The worker connects to Redis using hardcoded `host="localhost"`. In Docker, `localhost` refers to the container itself, not the Redis container, so the worker cannot reach Redis.
- **Fix:** Changed to use environment variables `REDIS_HOST` and `REDIS_PORT` with sensible defaults. Also added `REDIS_PASSWORD` support.

### Before
```python
r = redis.Redis(host="localhost", port=6379)
```

### After
```python
r = redis.Redis(
    host=os.getenv("REDIS_HOST", "redis"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    password=os.getenv("REDIS_PASSWORD", None),
    decode_responses=False
)
```

---

## Bug 2: Hardcoded Redis Host in API (already partially fixed in starter)

- **File:** `api/main.py`
- **Line:** 9-12
- **Problem:** The original code used `host="localhost"` which fails in Docker. The starter had already been partially fixed to use env vars, but it was missing Redis password support and connection pooling.
- **Fix:** Added `REDIS_PASSWORD` support, connection pooling for efficiency, and `REDIS_DB` support.

### Before
```python
def get_redis():
    return redis.Redis(
        host=os.getenv("REDIS_HOST", "redis"),
        port=int(os.getenv("REDIS_PORT", 6379))
    )
```

### After
```python
redis_pool = redis.ConnectionPool(
    host=os.getenv("REDIS_HOST", "redis"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    password=os.getenv("REDIS_PASSWORD", None),
    decode_responses=False,
    db=int(os.getenv("REDIS_DB", 0))
)

def get_redis():
    return redis.Redis(connection_pool=redis_pool)
```

---

## Bug 3: Health Check Does Not Verify Redis Connectivity

- **File:** `api/main.py`
- **Line:** 31-33
- **Problem:** The `/health` endpoint always returns `{"status": "ok"}` without actually checking if Redis is reachable. A false-positive health check means Docker will consider the service healthy even when Redis is down.
- **Fix:** Added a `redis.ping()` call inside a try/except block. Returns `{"status": "error"}` if Redis is unreachable.

### Before
```python
@app.get("/health")
def health():
    return {"status": "ok"}
```

### After
```python
@app.get("/health")
def health():
    try:
        r = get_redis()
        r.ping()
        return {"status": "ok"}
    except redis.ConnectionError:
        return {"status": "error", "detail": "Redis connection failed"}
```

---

## Bug 4: Hardcoded API URL in Frontend

- **File:** `frontend/app.js`
- **Line:** 6
- **Problem:** The frontend uses `const API_URL = "http://localhost:8000"` which will not work when the API is running in a separate Docker container. In Docker, services communicate via service names, not localhost.
- **Fix:** Changed to use `process.env.API_URL` with a default of `http://api:8000` (the Docker service name).

### Before
```javascript
const API_URL = "http://localhost:8000";
```

### After
```javascript
const API_URL = process.env.API_URL || "http://api:8000";
```

---

## Bug 5: Frontend Missing Health Check Endpoint

- **File:** `frontend/app.js`
- **Line:** N/A (missing entirely)
- **Problem:** The frontend has no `/health` endpoint, making it impossible for Docker Compose to perform health checks on the frontend service.
- **Fix:** Added a `/health` endpoint that returns `{"status": "ok"}`.

### Added
```javascript
app.get('/health', (req, res) => {
  res.json({ status: 'ok' });
});
```

---

## Bug 6: Frontend Binds Only to localhost

- **File:** `frontend/app.js`
- **Line:** 29
- **Problem:** `app.listen(3000)` binds to `localhost` by default in Express, which means the service is not accessible from other containers or the host in Docker.
- **Fix:** Changed to bind to `0.0.0.0` and made the port configurable via environment variable.

### Before
```javascript
app.listen(3000, () => {
  console.log('Frontend running on port 3000');
});
```

### After
```javascript
const PORT = process.env.PORT || 3000;
app.listen(PORT, '0.0.0.0', () => {
  console.log(`Frontend running on port ${PORT}`);
});
```

---

## Bug 7: Committed .env File with Secrets

- **File:** `api/.env`
- **Line:** 1-2
- **Problem:** The `.env` file containing `REDIS_PASSWORD=supersecretpassword123` was committed to the repository. Secrets must never be in version control. Additionally, the password was defined but never actually used in the Redis connection code.
- **Fix:** Deleted the `.env` file from the repository. Added `.env` to `.gitignore`. Created `.env.example` with placeholder values. Added `REDIS_PASSWORD` support to all services.

---

## Bug 8: Missing .gitignore

- **File:** Root level
- **Line:** N/A (file missing)
- **Problem:** No `.gitignore` file exists, which means `.env` files, `node_modules/`, `__pycache__/`, and other generated files can be accidentally committed.
- **Fix:** Created a comprehensive `.gitignore` covering Python, Node.js, Docker, and IDE artifacts.

---

## Bug 9: Worker Has No Graceful Shutdown

- **File:** `worker/worker.py`
- **Line:** 4
- **Problem:** The `signal` module was imported but never used. The worker runs in an infinite `while True` loop with no way to gracefully shut down on SIGTERM/SIGINT, which causes Docker to force-kill the container.
- **Fix:** Implemented signal handlers for SIGTERM and SIGINT that set a `running` flag to `False`, allowing the worker loop to exit cleanly.

### Before
```python
import signal
# ... signal never used
while True:
```

### After
```python
import signal
import sys

running = True

def shutdown(signum, frame):
    global running
    print("Shutting down gracefully...")
    running = False

signal.signal(signal.SIGTERM, shutdown)
signal.signal(signal.SIGINT, shutdown)

while running:
```

---

## Bug 10: Redis Queue Name Mismatch Risk

- **File:** `api/main.py` (line 19), `worker/worker.py` (line 15)
- **Problem:** The API uses `r.lpush("job", job_id)` and the worker uses `r.brpop("job", timeout=5)`. While these match, the name "job" is ambiguous and could conflict with the Redis hash key pattern `job:{job_id}`. Using a more specific queue name prevents potential key collisions.
- **Fix:** Changed both to use `"job_queue"` as the list name.

### Before (API)
```python
r.lpush("job", job_id)
```

### After (API)
```python
r.lpush("job_queue", job_id)
```

### Before (Worker)
```python
job = r.brpop("job", timeout=5)
```

### After (Worker)
```python
job = r.brpop("job_queue", timeout=5)
```

---

## Bug 11: API Response Missing Status Field

- **File:** `api/main.py`
- **Line:** 21
- **Problem:** The `create_job` endpoint returns only `{"job_id": job_id}` without a `status` field. The frontend and integration tests expect a `status` field in the response.
- **Fix:** Added `"status": "queued"` to the response and used `hset` with `mapping` for atomic multi-field setting.

### Before
```python
r.hset(f"job:{job_id}", "status", "queued")
return {"job_id": job_id}
```

### After
```python
r.hset(f"job:{job_id}", mapping={"status": "queued", "job_id": job_id})
return {"job_id": job_id, "status": "queued"}
```

---

## Bug 12: No Version Pinning in requirements.txt

- **File:** `api/requirements.txt`, `worker/requirements.txt`
- **Line:** All lines
- **Problem:** Dependencies are listed without version pins (e.g., `fastapi` instead of `fastapi==0.104.1`). This leads to non-reproducible builds and potential breakage when upstream packages update.
- **Fix:** Pinned all dependencies to specific versions.

---

## Bug 13: Missing Test Dependencies

- **File:** `api/requirements.txt`
- **Line:** N/A (missing entries)
- **Problem:** No test framework or coverage tools are listed in requirements.txt, making it impossible to run tests in CI without additional setup.
- **Fix:** Added `pytest`, `pytest-cov`, and `httpx` (for FastAPI TestClient) to `api/requirements.txt`.

---

## Bug 14: Empty Root Dockerfile

- **File:** `Dockerfile` (root)
- **Line:** All
- **Problem:** An empty Dockerfile exists at the repository root. This is invalid and would cause build failures.
- **Fix:** Removed the empty root Dockerfile. Each service now has its own Dockerfile in its respective directory.

---

## Bug 15: API get_job Uses hget Instead of hgetall

- **File:** `api/main.py`
- **Line:** 26
- **Problem:** Using `hget` for a single field works but is less flexible. If we want to return additional fields in the future, `hgetall` is more appropriate. Also, the original code assumed `status` would always be bytes, which may not be the case with `decode_responses` settings.
- **Fix:** Changed to use `hgetall` and added proper bytes/string handling.

### Before
```python
status = r.hget(f"job:{job_id}", "status")
if not status:
    return {"error": "not found"}
return {"job_id": job_id, "status": status.decode()}
```

### After
```python
data = r.hgetall(f"job:{job_id}")
if not data:
    return {"error": "not found"}
return {"job_id": job_id, "status": data[b"status"].decode() if isinstance(data[b"status"], bytes) else data["status"]}
```

---

## Bug 16: Redis Fails to Start Without Password Set

- **File:** `docker-compose.yml`
- **Line:** 7
- **Problem:** `redis-server --requirepass ${REDIS_PASSWORD}` fails when `REDIS_PASSWORD` is not set (empty string). Redis rejects empty passwords and crashes immediately. Additionally, `redis-cli -a ""` in the healthcheck prints authentication warnings to stderr, causing the health check to fail even when Redis is running.
- **Fix:** Added default password fallback `${REDIS_PASSWORD:-defaultpassword}` in all Redis-related configuration (command, healthcheck, service environment vars). Added `--no-auth-warning` flag to all `redis-cli` health checks.

### Before
```yaml
command: redis-server --requirepass ${REDIS_PASSWORD}
healthcheck:
  test: ["CMD", "redis-cli", "-a", "${REDIS_PASSWORD}", "ping"]
```

### After
```yaml
command: redis-server --requirepass ${REDIS_PASSWORD:-defaultpassword}
healthcheck:
  test: ["CMD", "redis-cli", "--no-auth-warning", "-a", "${REDIS_PASSWORD:-defaultpassword}", "ping"]
```
