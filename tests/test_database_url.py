from app.db.url import sqlalchemy_database_url


def test_sqlalchemy_database_url_preserves_local_sqlite() -> None:
    assert sqlalchemy_database_url("sqlite:///./invoicebridge.db") == "sqlite:///./invoicebridge.db"


def test_sqlalchemy_database_url_preserves_explicit_psycopg_driver() -> None:
    url = "postgresql+psycopg://invoicebridge:invoicebridge@localhost:5432/invoicebridge"
    assert sqlalchemy_database_url(url) == url


def test_sqlalchemy_database_url_uses_psycopg_for_neon_style_postgresql_url() -> None:
    url = "postgresql://neondb_owner:secret@ep-demo.us-east-1.aws.neon.tech/neondb?sslmode=require"
    assert (
        sqlalchemy_database_url(url)
        == "postgresql+psycopg://neondb_owner:secret@ep-demo.us-east-1.aws.neon.tech/neondb?sslmode=require"
    )


def test_sqlalchemy_database_url_uses_psycopg_for_postgres_scheme() -> None:
    url = "postgres://user:secret@example.test/db?sslmode=require"
    assert sqlalchemy_database_url(url) == "postgresql+psycopg://user:secret@example.test/db?sslmode=require"

