FROM python:3.13-slim

WORKDIR /app

# Run as an unprivileged user: a compromised app process shouldn't own the container.
RUN addgroup --system app && adduser --system --ingroup app --no-create-home app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY alembic ./alembic
COPY alembic.ini .
RUN chown -R app:app /app

USER app

EXPOSE 8000

# Readiness, not just liveness: the check fails if the database is unreachable,
# so orchestrators stop routing traffic to a container that can't serve requests.
HEALTHCHECK --interval=30s --timeout=3s --start-period=15s --retries=3 \
    CMD python -c "import sys, urllib.request; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health/ready', timeout=2).status == 200 else 1)"

CMD ["sh", "-c", "python -m alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
