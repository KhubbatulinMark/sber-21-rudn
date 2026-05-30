import os
from collections.abc import Callable
from pathlib import Path

import psycopg
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")

DATABASE_URL_SALES = os.environ["DATABASE_URL_SALES"]
DATABASE_URL_CATALOG = os.environ["DATABASE_URL_CATALOG"]
DATABASE_URL_WAREHOUSE = os.environ["DATABASE_URL_WAREHOUSE"]

_URLS: dict[str, str] = {
    "db_sales": DATABASE_URL_SALES,
    "db_catalog": DATABASE_URL_CATALOG,
    "warehouse": DATABASE_URL_WAREHOUSE,
}


def get_connection(alias: str) -> psycopg.Connection:
    return psycopg.connect(_URLS[alias])


def get_connection_sales() -> psycopg.Connection:
    return get_connection("db_sales")


def get_connection_catalog() -> psycopg.Connection:
    return get_connection("db_catalog")


def get_connection_warehouse() -> psycopg.Connection:
    return get_connection("warehouse")


def _probe(connect: Callable[[], psycopg.Connection]) -> tuple[str, str, str]:
    with connect() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT current_database(), current_user, "
            "split_part(version(), ' ', 2)"
        )
        return cur.fetchone()


if __name__ == "__main__":
    out = Path(__file__).resolve().parent / "result" / "connect.txt"
    out.parent.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []
    for alias, connect in [
        ("db_sales", get_connection_sales),
        ("db_catalog", get_connection_catalog),
        ("warehouse", get_connection_warehouse),
    ]:
        db, user, version = _probe(connect)
        lines.append(f"{alias:<10} → {db} | {user} | PostgreSQL {version}")
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
