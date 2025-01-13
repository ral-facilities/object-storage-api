FROM python:3.12.8-alpine3.20@sha256:bb94273467caf397de28b4e6dd09ca4a2dd1b53fa9b130d5b2c7c82719258356

WORKDIR /object-storage-api-run

COPY requirements.txt ./
COPY object_storage_api/ object_storage_api/

RUN --mount=type=cache,target=/root/.cache \
    set -eux; \
    \
    python3 -m pip install -r requirements.txt;

CMD ["fastapi", "dev", "object_storage_api/main.py", "--host", "0.0.0.0", "--port", "8000"]
EXPOSE 8000
