# Practice

## Description

A simple Web Server to build a Book Archive. 
Users can add any books to the archive and manage their books, by updating and deleting. 
And everyone can view all books in the archive.

![Use Case Diagram](../docs/images/user_case.png)

## Setup

1. Copy file `.env.example` to `.env` and change the following lines according to your preferred database settings.
   - If you want to run the app locally (without Docker) and connect to a local MongoDB instance, set:

```dotenv
MONGO_CONNECTION_URL=mongodb://localhost:27017/
MONGO_DATABASE=example_db
```

   - If you plan to run with the bundled Mongo container (via Docker Compose), you can keep defaults in `.env` or customize:

```dotenv
MONGO_INITDB_ROOT_USERNAME=mongo_root
MONGO_INITDB_ROOT_PASSWORD=mongo_pass
MONGO_INITDB_DATABASE=training_db
```

   - Optional override for Dockerized app to connect to a host Mongo instance instead of the bundled container:

```dotenv
# Example (macOS/Windows Docker):
# MONGO_URI=mongodb://host.docker.internal:27017/training_db
# Or on Linux use host IP such as mongodb://172.17.0.1:27017/training_db
```

   Notes / assumptions:
   - The repository provides both `MONGO_CONNECTION_URL` (used by local runs) and the `MONGO_INITDB_*` variables (used to initialize the containerized Mongo). If you set `MONGO_URI` the application is expected to prefer it over the default connection string. If the app does not currently read `MONGO_URI`, adapt your `.env` to supply the connection key your code expects (see `config.py`).
   - On Linux `host.docker.internal` may not be available; use the host's Docker bridge IP (for example `172.17.0.1`) or run the app outside Docker.


### Environment for Docker Compose

When running the project with Docker Compose, the application and the bundled MongoDB container are configured using environment variables from a `.env` file at the project root. Copy `.env.example` to `.env` and adjust any values below as needed.

Recommended variables for Compose (put these in `.env`):

```dotenv
# App server
SERVER_HOST=0.0.0.0
SERVER_PORT=8080

# Initialize the bundled MongoDB container (used only if you run the `mongo` service)
MONGO_INITDB_ROOT_USERNAME=mongo_root
MONGO_INITDB_ROOT_PASSWORD=mongo_pass
MONGO_INITDB_DATABASE=training_db

# Optional: Force the app to use an external Mongo instance instead of the bundled container
# Example for Docker Desktop on macOS/Windows:
# MONGO_URI=mongodb://host.docker.internal:27017/training_db
# Example for Linux if host.docker.internal is unavailable (replace with your host gateway IP):
# MONGO_URI=mongodb://172.17.0.1:27017/training_db

# Optional: expose the Mongo container port to the host (use with caution)
# MONGO_PORT_MAPPING=27017:27017
```

How these variables are used:
- If `MONGO_URI` is set, configure the application to prefer it (this lets the app connect to a host Mongo instead of the container).
- If `MONGO_URI` is unset, the app should connect to the internal `mongo` service (the connection string inside Docker typically looks like `mongodb://mongo:27017/<db>`).
- `MONGO_INITDB_*` variables are consumed by the official Mongo image to create the initial database and root user when the container is first started.
- `MONGO_PORT_MAPPING` is optional; if you set it and want the container to publish the port, add a `ports: - ${MONGO_PORT_MAPPING}` mapping to the `mongo` service in `docker-compose.yml` or use an override file.

2. (Optional) Create and activate a virtual environment, then install dependencies:

```bash
python3 -m venv venv
source venv/bin/activate
pip3 install -r requirements.txt
```

3. Run the application directly (without Docker):

```bash
python3 main.py
# or use your preferred command/run configuration depending on how the app is wired in main.py
```

## Run with Docker Compose (recommended for training)

The project includes a `docker-compose.yml` that can start the API service and an optional MongoDB service. The compose file is configured to NOT publish MongoDB's 27017 port by default to avoid port conflicts if you already have Mongo running on your host.

Basic commands:

```bash
# Build images and start services in foreground
docker compose up --build

# Build images and start services in background (detached)
docker compose up -d --build

# Stop and remove containers created by compose
docker compose down
```

If you want the app container to use a Mongo instance running on your host (instead of the bundled container):
- Set `MONGO_URI` in `.env` to point to your host Mongo (example above).
- Then start the app container only and avoid starting the bundled mongo service if you like:

```bash
# Start the app service only, do not start linked services
docker compose up --build --no-deps app
```

Notes:
- `--no-deps` prevents Compose from starting service dependencies. Use it only when you are sure the app can reach the DB you configured via `MONGO_URI`.
- If you need to expose the Mongo container to the host (e.g., for DB GUI tools), you can add a port mapping in `docker-compose.yml` or create an override file to map `27017:27017`. Be careful: exposing the container port may conflict with an existing host Mongo.

## Framework Sanic

*Reference: [Introduction | Sanic Framework](https://sanic.dev/en/guide/)*

* Web Server: [main.py](main.py)
* Configs: [config.py](config.py)
* Example APIs: [books_blueprint.py](app/apis/books_blueprint.py)

> Task 1: 
> 
> * Run Web Server
> ```
> $ python3 main.py
> ```
> * Call APIs via browser and [Postman](https://www.postman.com/downloads/)
> ```
> GET localhost:8080
> GET localhost:8080/books
> ```

## Database

- Reference: Databases

* Use `MongoDB` database and `PyMongo` library
* Database design: [collections](../docs/database_models/collections.json)
* Functions to query and update data: [mongodb.py](app/databases/mongodb.py)

> Task 2:
> 
> * Write functions to `create`, `get`, `update` and `delete` a book

## RESTful API

*Reference: [RESTful API](../README.md#restful-api-with-crud)*

* API Get all books: `GET /books`
* Validate HTTP request body: [json_validator.py](app/decorators/json_validator.py)

> Task 3:
> 
> * Complete CRUD books APIs
> 
> ```
> Create a book:        POST    /books
> 
> Read a book by ID:    GET     /books/{id}
> 
> Update a book by ID:  PUT     /books/{id}
> 
> Delete a book by ID:  DELETE  /books/{id}
> ```

## Caching

*Reference: [Cache strategies](https://docs.aws.amazon.com/AmazonElastiCache/latest/mem-ug/Strategies.html)*

* Use `Redis` in-memory data store
* Functions to set and get cache: [redis_cached.py](app/databases/redis_cached.py)
* Time-to-live

> Task 4:
> 
> * API Get all books: Cache data response

[//]: # (> * API Create, Update, Delete: Update cache when data updated)

## Authentication & Authorization

*Reference: [JSON Web Tokens](https://auth0.com/learn/json-web-tokens/)*

* Use JSON Web Token `JWT`
* Generate JWT: [jwt_utils.py](app/utils/jwt_utils.py)
* Authenticate: [auth.py](app/decorators/auth.py)
* Authorization: Check if the user has permission to take
* Login returns a short-lived `access_token` and a `refresh_token`.
* Refresh: `POST /v1/auth/refresh` with `{"refresh_token": "..."}`. Refresh tokens rotate and the old `jti` is revoked in Redis until its expiry.
* Logout: `POST /v1/auth/logout` with the access token and optional refresh token. Both token `jti` values are revoked in Redis with their remaining TTL.

Set `JWT_ACCESS_EXPIRATION` and `JWT_REFRESH_EXPIRATION` (seconds) in the environment to configure token lifetimes.

[//]: # (![JWT]&#40;../docs/images/jwt.png&#41;)

![JWT](../docs/images/jwt.png)

> Task 5:
> 
> * Write API Register and API Login
> * API Create a book: Must be logged in
> * API Update, Delete: Only owner are taken

## Unittest

*Reference: [Unit Test a REST API](https://www.testim.io/blog/unit-test-rest-api/)*

* Automatic API testing
* Unittest for books APIs: [testing.py](testing.py)

> Task 6:
> 
> * Complete unittest for all APIs
> * Run unittest
> ```
> $ python3 testing.py
> ```


## Docker
> Task 7:
> 
> * Goal: Read and understand the project's `docker-compose.yml` file (no changes to network or MongoDB configuration required).
> * While reading, pay attention to and be able to explain the following items:
>   - The `services` defined (for example `app`, `mongo`) and the role of each service.
>   - The difference between `build:` and `image:` in a service definition.
>   - The purpose of `env_file:` and important environment variables related to MongoDB (e.g. `MONGO_INITDB_*`, `MONGO_URI`).
>   - How `volumes:` are used to persist data (for example `./data/mongo:/data/db`).
>   - `ports:` and why the MongoDB port (27017) might intentionally NOT be mapped to the host by default.
>   - The role of `depends_on:`, `restart:`, and `healthcheck:` (if present) and why they matter.
>   - The `networks:` section and how services communicate by service name within the same network.
> * After reading, answer briefly (1-3 sentences) for each of the following:
>   1. Where will the app connect to Mongo when running with Compose? (example: `mongodb://mongo:27017/<db>`)
>   2. If you want to access Mongo from the host (for example with MongoDB Compass), what needs to be changed in the compose file or environment?
>   3. Why is it not recommended to copy an IP from `ifconfig` into the connection string for Compose deployments?
> 
> Useful commands to inspect and run the compose stack:
> ```bash
> # View the merged compose configuration
> docker compose config
>
> # Build images and start services in the foreground
> docker compose up --build
>
> # Build and start services in detached mode
> docker compose up -d --build
>
> # Stop and remove containers
> docker compose down
> ```
