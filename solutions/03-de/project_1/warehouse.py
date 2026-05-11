from pathlib import Path

from connect import get_connection_warehouse

_DDL_DIR = Path(__file__).resolve().parent / "ddl"


def _apply_and_list(ddl_filename: str, schema: str) -> list[str]:
    sql_text = (_DDL_DIR / ddl_filename).read_text(encoding="utf-8")
    with get_connection_warehouse() as conn, conn.cursor() as cur:
        cur.execute(sql_text)
        cur.execute(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = %s ORDER BY table_name",
            (schema,),
        )
        return [row[0] for row in cur.fetchall()]


def create_staging_tables() -> list[str]:
    return _apply_and_list("staging.sql", "staging")


def create_analytics_tables() -> list[str]:
    return _apply_and_list("analytics.sql", "analytics")


if __name__ == "__main__":
    result_dir = Path(__file__).resolve().parent / "result"
    result_dir.mkdir(parents=True, exist_ok=True)

    staging_tables = create_staging_tables()
    (result_dir / "staging_setup.txt").write_text(
        f"staging.sql: {', '.join(staging_tables)}\n", encoding="utf-8"
    )

    analytics_tables = create_analytics_tables()
    (result_dir / "analytics_setup.txt").write_text(
        f"analytics.sql: {', '.join(analytics_tables)}\n", encoding="utf-8"
    )
