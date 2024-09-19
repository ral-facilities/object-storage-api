FROM python:3.12.5-alpine3.20@sha256:bb5d0ac04679d78a1258e7dfacdb4d9bdefe9a10480eaf9b4bb09445d076369f

WORKDIR /object-storage-api-run

COPY requirements.txt ./
COPY object_storage_api/ object_storage_api/

RUN --mount=type=cache,target=/root/.cache \
    set -eux; \
    \
    python3 -m pip install -r requirements.txt;

CMD ["fastapi", "dev", "object_storage_api/main.py", "--host", "0.0.0.0", "--port", "8000"]
EXPOSE 8000
