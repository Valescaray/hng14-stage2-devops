import redis
import time
import os
import signal
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
REDIS_PORT = int(os.environ.get("REDIS_PORT", 6379))
REDIS_PASSWORD = os.environ.get("REDIS_PASSWORD", None)

r = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    password=REDIS_PASSWORD,
    decode_responses=True
)

shutdown = False


def handle_signal(signum, frame):
    global shutdown
    logger.info("Shutdown signal received, finishing current job...")
    shutdown = True


signal.signal(signal.SIGINT, handle_signal)
signal.signal(signal.SIGTERM, handle_signal)


def process_job(job_id):
    logger.info(f"Processing job {job_id}")
    r.hset(f"job:{job_id}", "status", "processing")
    time.sleep(2)  # simulate work
    r.hset(f"job:{job_id}", "status", "completed")
    logger.info(f"Done: {job_id}")


while not shutdown:
    try:
        job = r.brpop("job_queue", timeout=5)
        if job:
            _, job_id = job
            process_job(job_id)
    except redis.exceptions.ConnectionError as e:
        logger.error(f"Redis connection error: {e}. Retrying in 5s...")
        time.sleep(5)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        time.sleep(1)

logger.info("Worker shut down gracefully.")
