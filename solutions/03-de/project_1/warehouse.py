from pathlib import Path

from connect import get_connection_warehouse

_DDL_DIR = Path(__file__).resolve().parent / "ddl"


def create_staging_tables() -> list[str]:
    sql_text = (_DDL_DIR / "staging.sql").read_text(encoding="utf-8")
    with get_connection_warehouse() as conn, conn.cursor() as cur:
        cur.execute(sql_text)
        cur.execute(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = 'staging' ORDER BY table_name"
        )
        return [row[0] for row in cur.fetchall()]


if __name__ == "__main__":
    out = Path(__file__).resolve().parent / "result" / "staging_setup.txt"
    out.parent.mkdir(parents=True, exist_ok=True)
    names = create_staging_tables()
    out.write_text(f"staging.sql: {', '.join(names)}\n", encoding="utf-8")
