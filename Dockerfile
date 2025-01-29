FROM python:3.12.8-alpine3.20@sha256:0c4f778362f30cc50ff734a3e9e7f3b2ae876d8386f470e0c3ee1ab299cec21b as dev

WORKDIR /object-storage-api-run

COPY pyproject.toml ./
COPY object_storage_api/ object_storage_api/

RUN --mount=type=cache,target=/root/.cache \
    set -eux; \
    \
    python3 -m pip install -r pyproject.toml;

CMD ["fastapi", "dev", "object_storage_api/main.py", "--host", "0.0.0.0", "--port", "8000"]
EXPOSE 8000

FROM dev as unit-test

WORKDIR /object-storage-api-run

COPY test/ test/

CMD ["pytest", "--config-file", "test/pytest.ini", "test/unit", "--cov"]

FROM unit-test as e2e-test

WORKDIR /object-storage-api-run

CMD ["pytest", "--config-file", "test/pytest.ini", "test/e2e", "--cov"]

FROM unit-test as test

WORKDIR /object-storage-api-run

CMD ["pytest", "--config-file", "test/pytest.ini", "test/", "--cov"]

FROM python:3.12.8-alpine3.20@sha256:0c4f778362f30cc50ff734a3e9e7f3b2ae876d8386f470e0c3ee1ab299cec21b as prod

WORKDIR /object-storage-api-run

COPY requirements.txt ./
COPY object_storage_api/ object_storage_api/

RUN --mount=type=cache,target=/root/.cache \
    set -eux; \
    \
    python3 -m pip install --no-cache-dir -r requirements.txt; \
    # Create a non-root user to run as \
    addgroup -S object-storage-api; \
    adduser -S -D -G object-storage-api -H -h /object-storage-api-run object-storage-api;

USER object-storage-api

CMD ["fastapi", "run", "object_storage_api/main.py", "--host", "0.0.0.0", "--port", "8000"]
EXPOSE 8000