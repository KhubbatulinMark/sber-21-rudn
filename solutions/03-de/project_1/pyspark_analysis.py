from pathlib import Path

import pyspark.sql.functions as F
from pyspark.sql import SparkSession
from pyspark.sql.window import Window

DATASETS = Path(__file__).parent.parent.parent / "production" / "AI_Data_Engineering.Project_1.ID_1577979" / "datasets"

JDBC_URL = "jdbc:postgresql://localhost:5435/warehouse"
JDBC_PROPS = {
    "user": "postgres",
    "password": "postgres",
    "driver": "org.postgresql.Driver",
}

spark = (
    SparkSession.builder
    .appName("OlistAnalysis")
    .config("spark.jars.packages", "org.postgresql:postgresql:42.7.4")
    .getOrCreate()
)
spark.sparkContext.setLogLevel("ERROR")


# --- Задание 11: загрузка данных ---

orders_df = spark.read.jdbc(url=JDBC_URL, table="staging.orders", properties=JDBC_PROPS)
customers_raw = spark.read.csv(str(DATASETS / "olist_customers_dataset.csv"), header=True)
payments_raw = spark.read.csv(str(DATASETS / "olist_order_payments_dataset.csv"), header=True)

print("=== Схемы датафреймов ===")
orders_df.printSchema()
customers_raw.printSchema()
payments_raw.printSchema()

print("\n=== Первые 3 строки ===")
orders_df.show(3)
customers_raw.show(3)
payments_raw.show(3)

print(f"\nCustomers до очистки: {customers_raw.count()}")
customers_df = customers_raw.na.drop()
print(f"Customers после очистки: {customers_df.count()}")

print(f"Payments до очистки: {payments_raw.count()}")
payments_df = payments_raw.na.drop()
print(f"Payments после очистки: {payments_df.count()}")


# --- Задание 12: группировки и ранжирование ---

print("\n=== Бизнес-задача 1: заказы по год-месяц и статусу ===")
orders_with_ym = orders_df.withColumn(
    "order_year_month",
    F.date_format(F.col("order_purchase_timestamp"), "y-M"),
)
answer_1 = (
    orders_with_ym
    .groupBy("order_year_month", "order_status")
    .count()
    .withColumnRenamed("count", "No_of_orders_year_month")
    .orderBy("order_year_month")
)
answer_1.show(10)

print("\n=== Бизнес-задача 2: клиенты по штатам с рангом ===")
rank_window = Window.orderBy(F.desc("No_of_customers_state"))
answer_2 = (
    customers_df
    .groupBy("customer_state")
    .count()
    .withColumnRenamed("count", "No_of_customers_state")
    .withColumn("rank", F.row_number().over(rank_window))
)
answer_2.show(27)


# --- Задание 13: оконные функции ---

print("\n=== Бизнес-задача 3: клиенты с 3+ заказами ===")
orders_customers = orders_df.join(customers_df, on="customer_id", how="left")

repeat_buyers = (
    orders_customers
    .groupBy("customer_unique_id")
    .count()
    .where(F.col("count") >= 3)
)
print(f"Клиентов с 3+ заказами: {repeat_buyers.count()}")

print("\n=== Бизнес-задача 4: дней между 1-м и 3-м заказом ===")
repeat_ids = repeat_buyers.select("customer_unique_id")

w = Window.partitionBy("customer_unique_id").orderBy("order_purchase_timestamp")
ranked = (
    orders_customers
    .join(repeat_ids, on="customer_unique_id", how="inner")
    .withColumn("order_rank", F.row_number().over(w))
)

first_orders = ranked.where(F.col("order_rank") == 1).select(
    "customer_unique_id",
    F.col("order_purchase_timestamp").alias("first_order_ts"),
)
third_orders = ranked.where(F.col("order_rank") == 3).select(
    "customer_unique_id",
    F.col("order_purchase_timestamp").alias("third_order_ts"),
)

result = (
    first_orders
    .join(third_orders, on="customer_unique_id")
    .withColumn("days_to_third", F.datediff("third_order_ts", "first_order_ts"))
)

result.agg(
    F.avg("days_to_third").alias("avg_days"),
    F.min("days_to_third").alias("min_days"),
    F.max("days_to_third").alias("max_days"),
).show()

spark.stop()
