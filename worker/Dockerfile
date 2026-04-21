# ============================================================
# Worker — Python Redis consumer
# ============================================================
FROM python:3.12-slim

# Security — run as non-root
RUN groupadd -r appgroup && useradd -r -g appgroup -d /app -s /sbin/nologin appuser

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY worker.py ./

# Switch to non-root user
USER appuser

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import redis, os; r=redis.Redis(host=os.environ.get('REDIS_HOST','localhost'), port=int(os.environ.get('REDIS_PORT',6379)), password=os.environ.get('REDIS_PASSWORD',None)); r.ping()" || exit 1

CMD ["python", "worker.py"]
