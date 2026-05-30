from datetime import date

import psycopg

from connect import get_connection_sales


def query_orders_by_status(
    conn: psycopg.Connection,
    status: str,
    date_from: date,
    date_to: date,
) -> int:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT COUNT(*)
            FROM orders
            WHERE order_status = %s
              AND order_purchase_timestamp BETWEEN %s AND %s
            """,
            (status, date_from, date_to),
        )
        return cur.fetchone()[0]


def query_top_products(
    conn: psycopg.Connection,
    top_n: int,
) -> list[tuple]:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT oi.product_id,
                   SUM(oi.price + oi.freight_value) AS revenue
            FROM orders o
            INNER JOIN order_items oi ON o.order_id = oi.order_id
            GROUP BY oi.product_id
            ORDER BY revenue DESC
            LIMIT %s
            """,
            (top_n,),
        )
        return cur.fetchall()


def query_monthly_revenue(conn: psycopg.Connection) -> list[tuple]:
    with conn.cursor() as cur:
        cur.execute("""
            WITH monthly AS (
                SELECT
                    date_trunc('month', o.order_purchase_timestamp) AS month_start,
                    SUM(oi.price + oi.freight_value)                AS revenue
                FROM orders o
                INNER JOIN order_items oi ON o.order_id = oi.order_id
                GROUP BY month_start
            )
            SELECT
                month_start,
                revenue,
                revenue - LAG(revenue) OVER (ORDER BY month_start) AS delta_prev_month
            FROM monthly
            ORDER BY month_start
        """)
        return cur.fetchall()


def query_above_average_orders(conn: psycopg.Connection) -> list[tuple]:
    with conn.cursor() as cur:
        cur.execute("""
            WITH order_totals AS (
                SELECT order_id,
                       SUM(price + freight_value) AS order_total
                FROM order_items
                GROUP BY order_id
            )
            SELECT order_id, SUM(order_total) AS order_total
            FROM order_totals
            GROUP BY order_id
            HAVING SUM(order_total) > (SELECT AVG(order_total) FROM order_totals)
            ORDER BY order_total DESC
            LIMIT 20
        """)
        return cur.fetchall()


if __name__ == "__main__":
    lines: list[str] = []

    with get_connection_sales() as conn:
        count = query_orders_by_status(conn, "delivered", date(2017, 1, 1), date(2018, 8, 31))
        lines.append(f"Задание 4 — заказов со статусом 'delivered': {count}")

        top = query_top_products(conn, top_n=10)
        lines.append("\nЗадание 5 — топ-10 продуктов по выручке:")
        for product_id, revenue in top:
            lines.append(f"  {product_id}  {revenue:.2f}")

        monthly = query_monthly_revenue(conn)
        lines.append(f"\nЗадание 6 — динамика выручки по месяцам ({len(monthly)} строк):")
        for month_start, revenue, delta in monthly:
            delta_str = f"{delta:+.2f}" if delta is not None else "—"
            lines.append(f"  {str(month_start)[:7]}  {revenue:>14.2f}  {delta_str}")

        above_avg = query_above_average_orders(conn)
        lines.append("\nЗадание 7 — топ-20 заказов выше среднего:")
        for order_id, total in above_avg:
            lines.append(f"  {order_id}  {total:.2f}")

    output = "\n".join(lines)
    print(output)

    result_path = "result/sql_analytics.txt"
    with open(result_path, "w", encoding="utf-8") as f:
        f.write(output + "\n")
    print(f"\nРезультат сохранён в {result_path}")
