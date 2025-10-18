FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements from api (shared)
COPY api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy api code (beat needs access to Django apps)
COPY api /app

CMD ["celery", "-A", "config", "beat", "--loglevel=info", "--scheduler", "django_celery_beat.schedulers:DatabaseScheduler"]


