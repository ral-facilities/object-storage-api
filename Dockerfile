FROM python:3.12.8-alpine3.20@sha256:3b1df87fc50e7d47762aeb48673736079aa22e7c98c8851f5453dd49fc03ad1b as dev

WORKDIR /app

COPY pyproject.toml requirements.txt ./
COPY object_storage_api/ object_storage_api/

RUN --mount=type=cache,target=/root/.cache \
    set -eux; \
    \
    pip install --no-cache-dir .[dev]; \
    # Ensure the pinned versions of the production dependencies and subdependencies are installed \
    pip install --no-cache-dir --requirement requirements.txt;


CMD ["fastapi", "dev", "object_storage_api/main.py", "--host", "0.0.0.0", "--port", "8000"]

EXPOSE 8000


FROM python:3.12.8-alpine3.20@sha256:3b1df87fc50e7d47762aeb48673736079aa22e7c98c8851f5453dd49fc03ad1b as prod

WORKDIR /app

COPY requirements.txt ./
COPY object_storage_api/ object_storage_api/

RUN --mount=type=cache,target=/root/.cache \
    set -eux; \
    \
    pip install --no-cache-dir --requirement requirements.txt; \
    \
    # Create a non-root user to run as \
    addgroup -g 500 -S object-storage-api; \
    adduser -S -D -G object-storage-api -H -u 500 -h /app object-storage-api;

USER object-storage-api

CMD ["fastapi", "run", "object_storage_api/main.py", "--host", "0.0.0.0", "--port", "8000"]

EXPOSE 8000
