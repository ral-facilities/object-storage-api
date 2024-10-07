# Object Storage API

This is a Python microservice created using FastAPI that provides a REST API to upload and download attachments and
images to and from an S3 object store.

## How to Run

This microservice requires a MongoDB and S3 object storage instance to run against.

### Prerequisites

- Docker and Docker Compose installed (if you want to run the microservice inside Docker)
- Python 3.12, MongoDB 7.0 and MinIO installed on your machine (if you are not using Docker)
- Public key (must be OpenSSH encoded) to decode JWT access tokens (if JWT authentication/authorization is enabled)
- [MongoDB Compass](https://www.mongodb.com/products/compass) installed (if you want to interact with the database using
  a GUI)
- This repository cloned

### Docker Setup

Ensure that Docker is installed and running on your machine before proceeding.

1. Create a `.env` file alongside the `.env.example` file. Use the example file as a reference and modify the values
   accordingly.

   ```bash
   cp object_storage_api/.env.example object_storage_api/.env
   ```

2. Create a `logging.ini` file alongside the `logging.example.ini` file. Use the example file as a reference and modify
   it accordingly:

   ```bash
   cp object_storage_api/logging.example.ini object_storage_api/logging.ini
   ```

#### Using `docker-compose.yml`

The easiest way to run the application with Docker for local development is using the `docker-compose.yml` file. It is
configured to start

- A MongoDB instance that can be accessed at `localhost:27018` using `root` as the username and
  `example` as the password
- A MinIO instance at `localhost:9000` with a console that can be accessed at `localhost:9001` using `root` as the
  username and `example_password` as the password
- The application in a reload mode using the `Dockerfile`.

1. Build and start the Docker containers:

   ```bash
   docker-compose up
   ```

   The microservice should now be running inside Docker at http://localhost:8000 and its Swagger UI could be accessed
   at http://localhost:8000/docs. A MongoDB instance should also be running at http://localhost:27018.

#### Using `Dockerfile`

Use the `Dockerfile` to run just the application itself in a container. Use this only for local development (not
production)!

1. Build an image using the `Dockerfile` from the root of the project directory:

   ```bash
   docker build -f Dockerfile -t object_storage_api_image .
   ```

2. Start the container using the image built and map it to port `8000` locally):

   ```bash
   docker run -p 8000:8000 --name object_storage_api_container object_storage_api_image
   ```

   or with values for the environment variables:

   ```bash
   docker run -p 8000:8000 --name object_storage_api_container --env DATABASE__NAME=ims object-storage_api_image
   ```

   The microservice should now be running inside Docker at http://localhost:8000 and its Swagger UI could be accessed
   at http://localhost:8000/docs.

### Local Setup

Ensure that Python is installed on your machine before proceeding.

1. Create a Python virtual environment and activate it in the root of the project directory:

   ```bash
   python -m venv venv
   source venv/bin/activate
   ```

2. Install the required dependencies using pip:

   ```bash
   pip install .[dev]
   pip install -r requirements.txt
   ```

3. Create a `.env` file alongside the `.env.example` file. Use the example file as a reference and modify the values
   accordingly. You may need to update the port in `DATABASE__HOST_AND_OPTIONS` if running the database outside of
   docker.

   ```bash
   cp object_storage_api/.env.example object_storage_api/.env
   ```

4. Create a `logging.ini` file alongside the `logging.example.ini` file. Use the example file as a reference and modify
   it accordingly:

   ```bash
   cp object_storage_api/logging.example.ini object_storage_api/logging.ini
   ```

5. Start the microservice using FastAPI's CLI:

   ```bash
   fastapi dev object_storage_api/main.py
   ```

   The microservice should now be running locally at http://localhost:8000. The Swagger UI can be accessed
   at http://localhost:8000/docs.

## Notes

### Application Configuration

The configuration for the application is handled
using [Pydantic Settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/). It allows for loading config
values from environment variables or the `.env` file. Please note that even when using the `.env` file, Pydantic will
still read environment variables as well as the `.env` file, environment variables will always take priority over
values loaded from the `.env` file.

Listed below are the environment variables supported by the application.

| Environment Variable                           | Description                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   | Mandatory | Default Value                                    |
| ---------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------- | ------------------------------------------------ |
| `API__TITLE`                                   | The title of the API which is added to the generated OpenAPI.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 | No        | `Object Storage Service API`                     |
| `API__DESCRIPTION`                             | The description of the API which is added to the generated OpenAPI.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           | No        | `This is the API for the Object Storage Service` |
| `API__ROOT_PATH`                               | (If using a proxy) The path prefix handled by a proxy that is not seen by the app.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            | No        | ` `                                              |
| `API__ALLOWED_CORS_HEADERS`                    | The list of headers that are allowed to be included in cross-origin requests.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 | Yes       |                                                  |
| `API__ALLOWED_CORS_ORIGINS`                    | The list of origins (domains) that are allowed to make cross-origin requests.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 | Yes       |                                                  |
| `API__ALLOWED_CORS_METHODS`                    | The list of methods that are allowed to be used to make cross-origin requests.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                | Yes       |                                                  |
| `DATABASE__PROTOCOL`                           | The protocol component (i.e. `mongodb`) to use for the connection string for the `MongoClient` to connect to the database.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    | Yes       |                                                  |
| `DATABASE__USERNAME`                           | The database username to use for the connection string for the `MongoClient` to connect to the database.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      | Yes       |                                                  |
| `DATABASE__PASSWORD`                           | The database password to use for the connection string for the `MongoClient` to connect to the database.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      | Yes       |                                                  |
| `DATABASE__HOST_AND_OPTIONS`                   | The host (and optional port number) component as well specific options (if any) to use for the connection string for the `MongoClient` to connect to the database. The host component is the name or IP address of the host where the `mongod` instance is running, whereas the options are `<name>=<value>` pairs (i.e. `?authMechanism=SCRAM-SHA-256&authSource=admin`) specific to the connection.<br> <ul><li>For a replica set `mongod` instance(s), specify the hostname(s) and any options as listed in the replica set configuration - `prod-mongodb-1:27017,prod-mongodb-2:27017,prod-mongodb-3:27017/?authMechanism=SCRAM-SHA-256&authSource=admin`</li><li>For a standalone `mongod` instance, specify the hostname and any options - `prod-mongodb:27017/?authMechanism=SCRAM-SHA-256&authSource=admin`</li></ul> | Yes       |                                                  |
| `DATABASE__NAME`                               | The name of the database to use for the `MongoClient` to connect to the database.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             | Yes       |                                                  |
| `OBJECT_STORAGE__ENDPOINT_URL`                 | The URL of the object storage S3 endpoint.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    | Yes       |                                                  |
| `OBJECT_STORAGE__ACCESS_KEY`                   | The access key to use to authenticate with the S3 object storage.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             | Yes       |                                                  |
| `OBJECT_STORAGE__SECRET_ACCESS_KEY`            | The secret access key to use to authenticate with the S3 object storage.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      | Yes       |                                                  |
| `OBJECT_STORAGE__BUCKET_NAME`                  | The name of the S3 bucket to use for object storage.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          | Yes       |                                                  |
| `OBJECT_STORAGE__PRESIGNED_URL_EXPIRY_SECONDS` | The expiry time of presigned URLs.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            | Yes       |                                                  |
| `OBJECT_STORAGE__ATTACHMENT_MAX_SIZE_BYTES`    | The maximum file size of an attachment given in bytes.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        | Yes       |                                                  |
