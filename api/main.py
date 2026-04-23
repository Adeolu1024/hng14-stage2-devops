from fastapi import FastAPI
import redis
import uuid
import os

app = FastAPI()

redis_pool = redis.ConnectionPool(
    host=os.getenv("REDIS_HOST", "redis"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    password=os.getenv("REDIS_PASSWORD", None),
    decode_responses=False,
    db=int(os.getenv("REDIS_DB", 0))
)

def get_redis():
    return redis.Redis(connection_pool=redis_pool)


@app.post("/jobs")
def create_job():
    r = get_redis()
    job_id = str(uuid.uuid4())
    r.lpush("job_queue", job_id)
    r.hset(f"job:{job_id}", mapping={"status": "queued", "job_id": job_id})
    return {"job_id": job_id, "status": "queued"}

@app.get("/jobs/{job_id}")
def get_job(job_id: str):
    r = get_redis()
    data = r.hgetall(f"job:{job_id}")
    if not data:
        return {"error": "not found"}
    return {"job_id": job_id, "status": data[b"status"].decode() if isinstance(data[b"status"], bytes) else data["status"]}

@app.get("/health")
def health():
    try:
        r = get_redis()
        r.ping()
        return {"status": "ok"}
    except redis.ConnectionError:
        return {"status": "error", "detail": "Redis connection failed"}

