"""
============================================================
14 - DEPLOYMENT
============================================================
Getting Django to production is where many developers get
stuck. This chapter covers the full deployment stack:
Docker, docker-compose for local dev, GitHub Actions for CI/CD,
environment configuration, and production checklist.
============================================================
"""

# ─────────────────────────────────────────────────────────────
# Dockerfile
# ─────────────────────────────────────────────────────────────

DOCKERFILE = """
# Dockerfile
# Multi-stage build: keeps final image lean by separating
# the "build" stage (installs tools) from the "runtime" stage.

# ── Stage 1: Build ────────────────────────────────────────────
FROM python:3.12-slim AS builder

# Install system dependencies needed to compile Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \\
    build-essential         \\
    libpq-dev               \\
    libffi-dev              \\
    && rm -rf /var/lib/apt/lists/*

# Create a virtual environment inside the image
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies
COPY requirements/base.txt requirements/production.txt ./
RUN pip install --upgrade pip && \\
    pip install --no-cache-dir -r production.txt

# ── Stage 2: Runtime ──────────────────────────────────────────
FROM python:3.12-slim AS runtime

# Install only runtime system dependencies (no build tools)
RUN apt-get update && apt-get install -y --no-install-recommends \\
    libpq5                  \\
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user — never run apps as root!
RUN groupadd --gid 1000 appuser && \\
    useradd --uid 1000 --gid 1000 --no-create-home appuser

# Copy the virtual environment from the builder stage
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Set working directory
WORKDIR /app

# Copy application code
COPY --chown=appuser:appuser . .

# Switch to non-root user
USER appuser

# Collect static files (uses STATIC_ROOT from settings)
RUN python manage.py collectstatic --noinput

# Expose port
EXPOSE 8000

# Health check — Docker will restart unhealthy containers
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \\
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health/')" || exit 1

# Start the application
# gunicorn: WSGI server for sync Django
# uvicorn: ASGI server for async Django (channels, async views)
CMD ["gunicorn", \\
     "--bind", "0.0.0.0:8000", \\
     "--workers", "4", \\
     "--worker-class", "gthread", \\
     "--threads", "2", \\
     "--timeout", "60", \\
     "--keep-alive", "5", \\
     "--log-level", "info", \\
     "--access-logfile", "-", \\
     "--error-logfile", "-", \\
     "myproject.wsgi:application"]

# For async (Django Channels / async views):
# CMD ["uvicorn", "myproject.asgi:application",
#      "--host", "0.0.0.0", "--port", "8000",
#      "--workers", "4", "--log-level", "info"]
"""

# ─────────────────────────────────────────────────────────────
# docker-compose.yml (local development)
# ─────────────────────────────────────────────────────────────

DOCKER_COMPOSE = """
# docker-compose.yml — local development environment
# Run: docker-compose up
# Everything your app needs, wired together.

version: "3.9"

services:

  # ── Your Django app ────────────────────────────────────────
  web:
    build:
      context: .
      target: builder        # use builder stage for dev (has dev tools)
    command: >
      sh -c "python manage.py migrate &&
             python manage.py runserver 0.0.0.0:8000"
    volumes:
      - .:/app               # mount source code — changes reflect instantly
    ports:
      - "8000:8000"
    env_file:
      - .env                 # load environment variables from .env file
    environment:
      - DEBUG=True
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/myapp
      - REDIS_URL=redis://redis:6379/0
      - CELERY_BROKER_URL=redis://redis:6379/0
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: unless-stopped

  # ── PostgreSQL database ────────────────────────────────────
  db:
    image: postgres:16-alpine
    volumes:
      - postgres_data:/var/lib/postgresql/data/
    environment:
      POSTGRES_DB: myapp
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    ports:
      - "5432:5432"          # expose for local DB clients
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

  # ── Redis (cache + Celery broker) ─────────────────────────
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped

  # ── Celery worker ──────────────────────────────────────────
  celery_worker:
    build: .
    command: celery -A myproject worker --loglevel=info --concurrency=4
    volumes:
      - .:/app
    env_file: .env
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis
    restart: unless-stopped

  # ── Celery beat (scheduler) ────────────────────────────────
  celery_beat:
    build: .
    command: celery -A myproject beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler
    volumes:
      - .:/app
    env_file: .env
    depends_on:
      - db
      - redis
    restart: unless-stopped

  # ── Flower (Celery monitoring UI) ─────────────────────────
  flower:
    build: .
    command: celery -A myproject flower --port=5555
    ports:
      - "5555:5555"
    env_file: .env
    depends_on:
      - redis
    restart: unless-stopped

volumes:
  postgres_data:
"""

# ─────────────────────────────────────────────────────────────
# .env.example — template for environment variables
# ─────────────────────────────────────────────────────────────

ENV_EXAMPLE = """
# .env.example — copy to .env and fill in your values
# NEVER commit .env to git!

# ── Django ────────────────────────────────────────────────────
DJANGO_SECRET_KEY=your-secret-key-here-generate-with-python-secrets
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# ── Database ──────────────────────────────────────────────────
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/myapp

# ── Redis ─────────────────────────────────────────────────────
REDIS_URL=redis://localhost:6379/0

# ── Email ─────────────────────────────────────────────────────
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
EMAIL_HOST=smtp.sendgrid.net
EMAIL_HOST_USER=apikey
EMAIL_HOST_PASSWORD=your-sendgrid-api-key
DEFAULT_FROM_EMAIL=noreply@myapp.com

# ── Storage (AWS S3) ──────────────────────────────────────────
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret
AWS_STORAGE_BUCKET_NAME=myapp-media
AWS_S3_REGION_NAME=us-east-1

# ── AI ────────────────────────────────────────────────────────
OPENAI_API_KEY=sk-your-key-here

# ── Monitoring ────────────────────────────────────────────────
SENTRY_DSN=https://...@sentry.io/...

# ── Frontend URL (for email links, CORS) ──────────────────────
FRONTEND_URL=http://localhost:3000

# Generate secret key with:
# python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
"""

# ─────────────────────────────────────────────────────────────
# GitHub Actions CI/CD Pipeline
# ─────────────────────────────────────────────────────────────

GITHUB_ACTIONS = """
# .github/workflows/ci.yml
# Runs on every push and pull request

name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

env:
  PYTHON_VERSION: "3.12"
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:

  # ── Job 1: Lint & Type Check ────────────────────────────────
  lint:
    name: Lint & Type Check
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}
          cache: "pip"

      - name: Install linting tools
        run: pip install black isort flake8 mypy django-stubs

      - name: Check formatting (black)
        run: black --check .

      - name: Check import order (isort)
        run: isort --check-only .

      - name: Lint (flake8)
        run: flake8 . --max-line-length=120 --exclude=migrations

      - name: Type check (mypy)
        run: mypy . --ignore-missing-imports

  # ── Job 2: Tests ────────────────────────────────────────────
  test:
    name: Tests
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:16-alpine
        env:
          POSTGRES_USER: postgres
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: test_myapp
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

      redis:
        image: redis:7-alpine
        ports:
          - 6379:6379
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}
          cache: "pip"

      - name: Install dependencies
        run: |
          pip install -r requirements/development.txt

      - name: Run tests with coverage
        env:
          DEBUG: False
          DATABASE_URL: postgresql://postgres:postgres@localhost:5432/test_myapp
          REDIS_URL: redis://localhost:6379/0
          DJANGO_SECRET_KEY: test-secret-key-not-for-production
        run: |
          pytest --cov=. --cov-report=xml --cov-fail-under=80 -v

      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v4
        with:
          file: ./coverage.xml

  # ── Job 3: Security Scan ────────────────────────────────────
  security:
    name: Security Scan
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}

      - name: Check for vulnerabilities
        run: |
          pip install pip-audit safety
          pip-audit -r requirements/base.txt
          safety check -r requirements/base.txt

      - name: Check Django security
        env:
          DJANGO_SETTINGS_MODULE: myproject.settings.production
          DJANGO_SECRET_KEY: dummy-key-for-check
        run: python manage.py check --deploy

  # ── Job 4: Build & Push Docker Image ───────────────────────
  build:
    name: Build Docker Image
    runs-on: ubuntu-latest
    needs: [lint, test, security]   # only runs if all checks pass
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'

    permissions:
      contents: read
      packages: write

    steps:
      - uses: actions/checkout@v4

      - name: Log in to container registry
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
          tags: |
            type=sha,prefix=sha-
            type=raw,value=latest,enable={{is_default_branch}}

      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

  # ── Job 5: Deploy to Production ─────────────────────────────
  deploy:
    name: Deploy to Production
    runs-on: ubuntu-latest
    needs: [build]
    environment: production    # requires manual approval in GitHub

    steps:
      - name: Deploy to server
        uses: appleboy/ssh-action@v1.0.0
        with:
          host: ${{ secrets.PROD_HOST }}
          username: ${{ secrets.PROD_USER }}
          key: ${{ secrets.PROD_SSH_KEY }}
          script: |
            cd /opt/myapp
            docker pull ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:latest
            docker-compose -f docker-compose.prod.yml up -d --no-deps web
            docker-compose -f docker-compose.prod.yml exec -T web python manage.py migrate
            docker-compose -f docker-compose.prod.yml exec -T web python manage.py collectstatic --noinput
            echo "Deployment complete!"
"""

# ─────────────────────────────────────────────────────────────
# PRODUCTION CHECKLIST
# ─────────────────────────────────────────────────────────────

PRODUCTION_CHECKLIST = """
╔══════════════════════════════════════════════════════════════╗
║               DJANGO PRODUCTION CHECKLIST                    ║
╚══════════════════════════════════════════════════════════════╝

Run: python manage.py check --deploy  ← this catches most issues!

── Security ──────────────────────────────────────────────────
☐ DEBUG = False
☐ SECRET_KEY is long, random, from environment variable
☐ ALLOWED_HOSTS is set (not "*")
☐ HTTPS enforced (SECURE_SSL_REDIRECT = True)
☐ HSTS configured (SECURE_HSTS_SECONDS = 31536000)
☐ CSRF protection enabled (default: yes, don't disable it)
☐ Secure cookies (SESSION_COOKIE_SECURE, CSRF_COOKIE_SECURE)
☐ No debug information in production error pages
☐ Database credentials in environment variables, not code

── Database ──────────────────────────────────────────────────
☐ Database is NOT SQLite (use PostgreSQL)
☐ Connection pooling configured (django-db-geventpool or PgBouncer)
☐ Database backups automated and tested
☐ Migrations have been run
☐ Database indexes created for frequent queries

── Static & Media Files ──────────────────────────────────────
☐ STATIC_ROOT configured, collectstatic run
☐ WhiteNoise or S3/CDN serving static files
☐ Media files on S3 or similar (not local disk in containers)

── Performance ───────────────────────────────────────────────
☐ Redis cache configured
☐ Database queries optimized (select_related, prefetch_related)
☐ No N+1 queries (use django-debug-toolbar to check)
☐ Celery workers running for async tasks
☐ Gunicorn/uvicorn with appropriate worker count

── Monitoring ────────────────────────────────────────────────
☐ Sentry (or similar) for error tracking
☐ Logging configured and shipping to central location
☐ Health check endpoint (/health/) configured
☐ Uptime monitoring set up
☐ Database performance monitoring

── Deployment ────────────────────────────────────────────────
☐ CI/CD pipeline runs tests before deploy
☐ Zero-downtime deployment configured
☐ Rollback plan documented and tested
☐ Environment variables set in deployment platform
☐ Docker image uses non-root user
"""

print("Deployment module loaded.")
print("Contents: Dockerfile, docker-compose, GitHub Actions CI/CD, production checklist")
