FROM python:3.12.9-alpine3.20@sha256:4ce45e8acd11d49ee07aa736cd7ca2950df75033b946f3a5d9eca1cb4aae2ab7 as dev

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


FROM dev as test

WORKDIR /app

COPY test/ test/

CMD ["pytest",  "--config-file", "test/pytest.ini", "-v"]


FROM python:3.12.9-alpine3.20@sha256:4ce45e8acd11d49ee07aa736cd7ca2950df75033b946f3a5d9eca1cb4aae2ab7 as prod

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
