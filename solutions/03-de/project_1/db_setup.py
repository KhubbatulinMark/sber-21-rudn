from pathlib import Path

from connect import get_connection_catalog, get_connection_sales

_DDL_DIR = Path(__file__).resolve().parent / "ddl"


def create_tables() -> dict[str, list[str]]:
    targets = [
        ("db_sales.sql", get_connection_sales),
        ("db_catalog.sql", get_connection_catalog),
    ]
    listed: dict[str, list[str]] = {}
    for filename, connect in targets:
        sql_text = (_DDL_DIR / filename).read_text(encoding="utf-8")
        with connect() as conn, conn.cursor() as cur:
            cur.execute(sql_text)
            cur.execute(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = 'public' ORDER BY table_name"
            )
            listed[filename] = [row[0] for row in cur.fetchall()]
    return listed


if __name__ == "__main__":
    out = Path(__file__).resolve().parent / "result" / "db_setup.txt"
    out.parent.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []
    for filename, names in create_tables().items():
        lines.append(f"{filename}: {', '.join(names)}")
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
