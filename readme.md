# Organization Catalog API

REST API application for managing Organizations, Buildings, and Activities directory

Tech Stack: FastAPI, PostgreSQL + PostGIS, SQLAlchemy, Alembic, Redis, Pydantic, Docker

## Features

- *Organizations Management*: List, search, and filter organizations by various criteria
- *Buildings Directory*: Manage buildings with geospatial coordinates
- *Activity Classification*: Hierarchical activity tree with up to 3 levels of nesting
- *Geospatial Search*: Search organizations by radius or rectangular area using PostGIS
- *Hierarchical Search*: Search organizations by activity type including all child activities
- *Redis Caching*: Caching layer for performance
- *API Key Authentication*: Access with static API key
- *Swagger Documentation*: API documentation at `/docs`

## Quick Start

### 1. Configure environment

Copy the example environment file and configure if needed:

```bash
cp .env.example .env
```

Default configuration:
- API Key: `secret-api-key`
- Database: PostgreSQL on port 5432
- Redis: Redis on port 6382
- API Server: http://localhost:8051

### 2. Start the application

```bash
docker compose up --build -d
```

This will:
- Start PostgreSQL with PostGIS extension
- Start Redis
- Run database migrations automatically
- Start the API server on port 8051

### 4. Load test data

```bash
./db-data-generation.sh
```

This script populates the database with sample organizations

### 5. Access the API

- **API Base URL**: http://localhost:8051
- **Swagger UI**: http://localhost:8051/docs
- **ReDoc**: http://localhost:8051/redoc

## Development

### Using Makefile

The project includes a Makefile with common commands:

```bash
make help      # Show available commands
make build     # Build Docker images
make up        # Start services
make upb       # Build and start services
make down      # Stop services
make logs      # View logs
make test      # Run tests
make lint      # Format code with ruff
```

### Running tests

```bash
make test
```
