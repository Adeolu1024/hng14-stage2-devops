# Job Processing System

A multi-service job processing system consisting of a Node.js frontend, Python/FastAPI backend, Python worker, and Redis message queue.

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Frontend   │────>│     API     │────>│   Worker    │
│  (Node.js)  │     │  (FastAPI)  │     │   (Python)  │
│   :3000     │     │    :8000    │     │             │
└─────────────┘     └──────┬──────┘     └──────┬──────┘
                           │                   │
                           └────────┬──────────┘
                                    │
                           ┌────────▼────────┐
                           │     Redis       │
                           │     :6379       │
                           └─────────────────┘
```

- **Frontend**: Express.js web app where users submit and track jobs
- **API**: FastAPI service that creates jobs and serves status updates
- **Worker**: Python process that picks up and processes jobs from the queue
- **Redis**: Shared message broker between API and worker

## Prerequisites

- Docker Engine >= 20.10
- Docker Compose >= 2.0
- Git

## Quick Start

### 1. Clone the Repository

```bash
git clone <your-fork-url>
cd hng14-stage2-devops
```

### 2. Configure Environment Variables

```bash
cp .env.example .env
```

Edit `.env` and set your values:

```env
REDIS_PASSWORD=your-secure-password
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0
API_URL=http://api:8000
FRONTEND_PORT=3000
API_PORT=8000
```

### 3. Start the Stack

```bash
docker compose up -d --build
```

### 4. Verify Services

```bash
docker compose ps
```

Expected output — all services should show `(healthy)`:

```
NAME                        STATUS
hng14-stage2-devops-redis-1    Up (healthy)
hng14-stage2-devops-api-1      Up (healthy)
hng14-stage2-devops-worker-1   Up (healthy)
hng14-stage2-devops-frontend-1 Up (healthy)
```

### 5. Access the Application

- **Frontend**: http://localhost:3000
- **API**: http://localhost:8000
- **API Health**: http://localhost:8000/health
- **Frontend Health**: http://localhost:3000/health

### 6. Submit a Job

```bash
# Submit a job
curl -X POST http://localhost:3000/submit

# Check job status (replace with your job_id)
curl http://localhost:3000/status/<job_id>
```

Or open http://localhost:3000 in your browser and click "Submit New Job".

## Stopping the Stack

```bash
docker compose down -v
```

## Running Tests

```bash
cd api
pip install -r requirements.txt
pytest test_main.py -v --cov=. --cov-report=term
```

## Project Structure

```
├── api/
│   ├── Dockerfile          # Multi-stage Python build
│   ├── main.py             # FastAPI application
│   ├── requirements.txt    # Python dependencies
│   └── test_main.py        # Unit tests
├── frontend/
│   ├── Dockerfile          # Multi-stage Node.js build
│   ├── app.js              # Express.js application
│   ├── package.json        # Node.js dependencies
│   └── views/
│       └── index.html      # Frontend UI
├── worker/
│   ├── Dockerfile          # Multi-stage Python build
│   ├── worker.py           # Job processor
│   └── requirements.txt    # Python dependencies
├── .github/
│   └── workflows/
│       └── ci-cd.yml       # CI/CD pipeline
├── docker-compose.yml      # Service orchestration
├── .env.example            # Environment variable template
├── .gitignore
├── FIXES.md                # Bug fix documentation
└── README.md
```

## CI/CD Pipeline

The GitHub Actions workflow (`.github/workflows/ci-cd.yml`) runs the following stages in strict order:

1. **Lint** — flake8 (Python), ESLint (JavaScript), hadolint (Dockerfiles)
2. **Test** — pytest with Redis mocking, coverage report uploaded as artifact
3. **Build** — Build all images, tag with git SHA + latest, push to local registry
4. **Security Scan** — Trivy scan all images, fail on CRITICAL, SARIF artifact uploaded
5. **Integration Test** — Full stack e2e test: submit job, poll until completed, verify status
6. **Deploy** — Rolling update on `main` branch; new container must pass health check within 60s before old is stopped

A failure in any stage prevents all subsequent stages from running.

## Security

- No secrets are committed to the repository
- All services run as non-root users
- Redis is not exposed on the host machine
- All configuration comes from environment variables
- Images are scanned for vulnerabilities with Trivy
