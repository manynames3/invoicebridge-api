# ADR 0011: Use Neon For Hosted Demos And RDS For AWS Production

## Status

Accepted

## Context

InvoiceBridge API is Postgres-oriented and uses `DATABASE_URL` for the SQLAlchemy engine and Alembic migrations. Public portfolio demos need a managed database with low idle cost because traffic is intermittent. Production AWS deployments have different requirements: private networking, predictable always-on capacity, managed backup policies, RDS Proxy, and AWS compliance controls.

## Decision

Use Neon Postgres as the preferred hosted demo database and keep Docker Compose Postgres as the local development default. Support copied Neon connection strings by normalizing `postgresql://` and `postgres://` URLs to SQLAlchemy's installed `psycopg` driver.

Document RDS PostgreSQL as the production AWS database option when InvoiceBridge is deployed inside a full AWS stack.

## Consequences

- Hosted demos can use managed Postgres without paying for an always-on demo database.
- Local development remains unchanged through Docker Compose or SQLite.
- Real Neon secrets stay outside the repository and are injected through environment variables.
- AWS production guidance remains credible and does not imply Neon is the default production database for every deployment.
- Alembic migrations work against local Postgres, Neon, RDS, and SQLite test databases through the same `DATABASE_URL` path.

