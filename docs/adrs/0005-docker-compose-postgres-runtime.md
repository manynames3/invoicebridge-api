# ADR 0005: Use Docker Compose And PostgreSQL For Local Runtime

## Status

Accepted

## Context

The project should be easy for reviewers to run while still resembling a persisted backend service. SQLite is useful for fast tests, but the runtime model should show a realistic database.

## Decision

Use Docker Compose with a FastAPI container and PostgreSQL 16. Keep Alembic migrations in the repo and allow local auto table creation for MVP convenience.

## Consequences

- Reviewers can start the API and database with one command.
- SQLAlchemy models and migrations show the intended persistent schema.
- Production deployment should run migrations explicitly and disable automatic table creation.
