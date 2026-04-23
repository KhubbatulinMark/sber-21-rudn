import os
import time
from pathlib import Path

import psycopg
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL_SALES = os.environ["DATABASE_URL_SALES"]
DATABASE_URL_CATALOG = os.environ["DATABASE_URL_CATALOG"]
DATABASE_URL_WAREHOUSE = os.environ["DATABASE_URL_WAREHOUSE"]

DDL_DIR = Path(__file__).parent / "ddl"


def get_conn_sales() -> psycopg.Connection:
    return psycopg.connect(DATABASE_URL_SALES)


def get_conn_catalog() -> psycopg.Connection:
    return psycopg.connect(DATABASE_URL_CATALOG)


def get_conn_warehouse() -> psycopg.Connection:
    return psycopg.connect(DATABASE_URL_WAREHOUSE)


def _wait_and_describe(get_conn, attempts: int = 10, delay: float = 1.0) -> tuple[str, str, str]:
    last_exc: Exception | None = None
    for _ in range(attempts):
        try:
            with get_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT current_database(), current_user, "
                        "split_part(version(), ' ', 2)"
                    )
                    return cur.fetchone()
        except psycopg.OperationalError as exc:
            last_exc = exc
            time.sleep(delay)
    raise RuntimeError(f"database not ready after {attempts} attempts") from last_exc


if __name__ == "__main__":
    for name, get_conn in [
        ("db_sales", get_conn_sales),
        ("db_catalog", get_conn_catalog),
        ("warehouse", get_conn_warehouse),
    ]:
        db, user, version = _wait_and_describe(get_conn)
        print(f"{name:<10} → {db} | {user} | PostgreSQL {version}")
