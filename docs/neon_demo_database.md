# Neon Demo Database

InvoiceBridge API uses `DATABASE_URL` for all database connections, so a hosted Neon Postgres database can be used for public demos without changing application code.

Neon is used for hosted demos because it provides managed Postgres with low or zero idle cost, making it appropriate for portfolio/demo environments that receive intermittent traffic. RDS remains appropriate for production when the API is deployed into AWS and needs private networking, managed backups, RDS Proxy, compliance controls, and predictable always-on workloads.

## When To Use Neon

Use Neon for:

- public portfolio demos,
- low-traffic hosted API demos,
- short-lived test environments,
- branches or preview databases,
- showing that the app runs against real hosted Postgres without paying for always-on database infrastructure.

Use AWS RDS PostgreSQL for:

- production deployments inside a broader AWS stack,
- private VPC networking,
- predictable always-on workloads,
- managed backup/restore policies,
- RDS Proxy or advanced connection management,
- AWS compliance, audit, and networking controls.

## Create A Neon Database

1. Create a Neon project.
2. Create or use the default database, for example `neondb`.
3. Copy the Postgres connection string from Neon.
4. Keep `sslmode=require` in the connection string. If Neon includes `channel_binding=require`, keep that parameter too.

Typical Neon URL shape:

```env
DATABASE_URL=postgresql://neondb_owner:REPLACE_ME@ep-demo.us-east-1.aws.neon.tech/neondb?sslmode=require
```

The app normalizes `postgresql://` and `postgres://` URLs to SQLAlchemy's `postgresql+psycopg://` driver internally, so copied Neon URLs work with the installed `psycopg` dependency.

## Run Migrations Against Neon

For a hosted demo database, run Alembic migrations explicitly:

```bash
export DATABASE_URL="postgresql://neondb_owner:REPLACE_ME@ep-demo.us-east-1.aws.neon.tech/neondb?sslmode=require"
export AUTO_CREATE_TABLES=false
alembic upgrade head
```

Or with the Makefile:

```bash
DATABASE_URL="postgresql://neondb_owner:REPLACE_ME@ep-demo.us-east-1.aws.neon.tech/neondb?sslmode=require" \
AUTO_CREATE_TABLES=false \
make migrate
```

Use the direct Neon connection string for migrations. If you later use a pooled connection string for the app runtime, keep migrations on the direct database URL unless you have tested your migration workflow through the pooler.

## Run The API With Neon

Set the same `DATABASE_URL` in the hosted API environment:

```env
APP_ENV=demo
DATABASE_URL=postgresql://neondb_owner:REPLACE_ME@ep-demo.us-east-1.aws.neon.tech/neondb?sslmode=require
AUTO_CREATE_TABLES=false
API_KEY=REPLACE_WITH_STRONG_ADMIN_KEY
```

Then deploy the FastAPI container or run locally:

```bash
make run
```

The API will use Neon through the same SQLAlchemy engine path as local Postgres.

## SSL Notes

Neon connection strings include `sslmode=require`, and some examples include `channel_binding=require`. Keep those parameters in `DATABASE_URL`. The app does not hardcode SSL settings because SSL belongs in the Postgres connection string and differs across local Docker, Neon, and production cloud databases.

## Operational Notes

- Do not commit the real Neon URL or password.
- Rotate the Neon role password if it is exposed.
- Use sanitized invoice payloads in public demos.
- Run migrations before starting the hosted API when `AUTO_CREATE_TABLES=false`.
- Keep local development on Docker Compose Postgres or SQLite when you do not need a hosted database.
