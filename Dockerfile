FROM python:3.13.0-slim as dev

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


FROM python:3.13.0-slim as prod

WORKDIR /app

COPY requirements.txt ./
COPY object_storage_api/ object_storage_api/

RUN --mount=type=cache,target=/root/.cache \
    set -eux; \
    \
    pip install --no-cache-dir --requirement requirements.txt; \
    \
    # Create a non-root user to run as \
    groupadd -g 500 object-storage-api; \
    useradd -u 500 -g object-storage-api -d /app -M -s /sbin/nologin object-storage-api;

USER object-storage-api

CMD ["fastapi", "run", "object_storage_api/main.py", "--host", "0.0.0.0", "--port", "8000"]

EXPOSE 8000
