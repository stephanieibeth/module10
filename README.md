# Module 12 – User Authentication & Calculation API

This project extends the FastAPI Calculator into a complete REST API with secure user authentication, PostgreSQL integration, calculation history, Docker containerization, and automated testing using GitHub Actions.

---

## Features

- FastAPI REST API
- PostgreSQL database
- SQLAlchemy ORM
- Secure password hashing with bcrypt
- JWT authentication
- Pydantic validation
- User registration and login
- Calculation CRUD (BREAD)
- OpenAPI / Swagger documentation
- Unit, integration, and end-to-end testing
- Docker & Docker Compose support
- GitHub Actions CI/CD
- Docker Hub deployment

---

# API Endpoints

## User Endpoints

| Method | Endpoint | Description |
|---------|----------|-------------|
| POST | `/users/register` | Register a new user |
| POST | `/users/login` | Login and receive a JWT token |

---

## Calculation Endpoints

| Method | Endpoint | Description |
|---------|----------|-------------|
| GET | `/calculations` | Browse all calculations |
| POST | `/calculations` | Create a new calculation |
| GET | `/calculations/{id}` | Read one calculation |
| PUT | `/calculations/{id}` | Update a calculation |
| DELETE | `/calculations/{id}` | Delete a calculation |

---

## Basic Calculator Endpoints

| Method | Endpoint |
|---------|----------|
| POST | `/add` |
| POST | `/subtract` |
| POST | `/multiply` |
| POST | `/divide` |

---

# Running the Application

Clone the repository:

```bash
git clone https://github.com/stephanieibeth/module10.git
cd module10
```

Build and start Docker containers:

```bash
docker compose up --build
```

The application will be available at:

```
http://localhost:8000
```

Swagger Documentation:

```
http://localhost:8000/docs
```

ReDoc Documentation:

```
http://localhost:8000/redoc
```

---

# Running Tests

Run all tests:

```bash
pytest -q
```

Run with coverage:

```bash
pytest --cov=app
```

Current project status:

- 116 tests passed
- 1 test skipped
- 97% test coverage

---

# Docker

Build the image:

```bash
docker compose build
```

Start containers:

```bash
docker compose up
```

Stop containers:

```bash
docker compose down
```

---

# Database

This project uses PostgreSQL.

Default database:

```
fastapi_db
```

Database service runs through Docker Compose.

---

# Technologies Used

- Python 3.12
- FastAPI
- PostgreSQL
- SQLAlchemy
- Pydantic
- Docker
- Docker Compose
- Pytest
- GitHub Actions
- JWT Authentication
- Passlib (bcrypt)

---

# Docker Hub

Docker image:

```
https://hub.docker.com/r/YOUR_DOCKERHUB_USERNAME/module10_is601
```

Replace `YOUR_DOCKERHUB_USERNAME` with your actual Docker Hub username.

---

# Manual API Testing

The API was manually tested using Swagger UI (`/docs`).

Verified functionality includes:

- User registration
- User login
- Create calculation
- Browse calculations
- Read calculation
- Update calculation
- Delete calculation

All endpoints returned the expected HTTP status codes and responses.

---

# Continuous Integration

GitHub Actions automatically:

- Runs all tests
- Checks code quality
- Builds the Docker image
- Pushes the Docker image to Docker Hub after successful builds

---

# Author

Stephanie Manchame

IS218 – Building Web Applications

Module 12