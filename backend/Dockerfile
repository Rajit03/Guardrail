FROM zricethezav/gitleaks:v8.18.2 AS gitleaks-bin

FROM python:3.12-slim

WORKDIR /app

# Prevent Python from writing pyc files to disk and buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gcc \
    libpq-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy gitleaks binary from the official image (avoids GitHub TLS issues during build)
COPY --from=gitleaks-bin /usr/bin/gitleaks /usr/local/bin/gitleaks

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

EXPOSE 8000

# Start Alembic migrations and Uvicorn server
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
