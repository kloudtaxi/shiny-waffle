# The OWM service (contract v1.2), deploy-ready. Build context: the repo root.
#   docker build -f lab/owm_service/Dockerfile -t owm-service:dev .
# Lab routes are OFF by default. The image holds no key; live Jev needs a key file mounted at run
# time and TYPESAFE_API_KEY_FILE pointing to it.
FROM ghcr.io/astral-sh/uv:0.12.17 AS uv

FROM python:3.12.11-slim
COPY --from=uv /uv /uvx /bin/
WORKDIR /app

# Dependencies only: the project itself (src/, the northstar package) is never installed, and the
# repo's README never enters the image.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --group owm-service --no-dev --no-install-project

# Only the four lab packages the service imports (through _lab.py), never the rest of lab/
COPY lab/owm_service/ lab/owm_service/
COPY lab/owm_kernel/ lab/owm_kernel/
COPY lab/owm_register/ lab/owm_register/
COPY lab/decision_engine/ lab/decision_engine/
COPY dataset/evidence/ dataset/evidence/
COPY dataset/evidence-variants/ dataset/evidence-variants/
# runs/: the .dockerignore lets through only the recorded Jev exchanges and the admission specs
COPY runs/ runs/

ENV PYTHONPATH=/app/lab \
    OWM_LAB_ROUTES=0 \
    OWM_JEV=replay \
    OWM_STATE_DIR=/data \
    PYTHONUNBUFFERED=1 \
    UV_CACHE_DIR=/tmp/uv-cache \
    UV_PYTHON_DOWNLOADS=never

RUN useradd --system --uid 10001 --no-create-home owm \
    && mkdir -p /data && chown owm /data
USER owm
VOLUME /data
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s \
    CMD ["/app/.venv/bin/python", "-c", "import urllib.request as u; u.urlopen('http://127.0.0.1:8000/healthz', timeout=2)"]

CMD ["uv", "run", "--no-sync", "python", "-m", "owm_service"]
