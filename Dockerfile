FROM python:3.13.7-alpine3.22@sha256:9ba6d8cbebf0fb6546ae71f2a1c14f6ffd2fdab83af7fa5669734ef30ad48844 AS base

WORKDIR /app

COPY pyproject.toml requirements.txt ./
COPY object_storage_api/ object_storage_api/


FROM base AS dev

WORKDIR /app

RUN --mount=type=cache,target=/root/.cache \
    set -eux; \
    \
    pip install --no-cache-dir .[dev]; \
    # Ensure the pinned versions of the production dependencies and subdependencies are installed \
    pip install --no-cache-dir --requirement requirements.txt;


CMD ["fastapi", "dev", "object_storage_api/main.py", "--host", "0.0.0.0", "--port", "8000"]

EXPOSE 8000


FROM dev AS test

WORKDIR /app

COPY test/ test/

CMD ["pytest",  "--config-file", "test/pytest.ini", "-v"]


FROM base AS prod

WORKDIR /app

RUN --mount=type=cache,target=/root/.cache \
    set -eux; \
    \
    # Ensure the package gets installed properly using the pyproject.toml file \
    pip install --no-cache-dir .; \
    # Ensure the pinned versions of the production dependencies and subdependencies are installed \
    pip install --no-cache-dir --requirement requirements.txt; \
    \
    # Create a non-root user to run as \
    addgroup -g 500 -S object-storage-api; \
    adduser -S -D -G object-storage-api -H -u 500 -h /app object-storage-api;

USER object-storage-api

CMD ["fastapi", "run", "object_storage_api/main.py", "--host", "0.0.0.0", "--port", "8000"]

EXPOSE 8000
