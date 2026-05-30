# Project 3 – решение

Решение проекта «Оркестрация и мониторинг ML-пайплайна»: Airflow + Evidently AI поверх ETL и DW
из проекта 1.

## Структура

```
project_3/
├── docker-compose.yml         Airflow (LocalExecutor) + 3 postgres-источника
├── .env                       креды для исходных баз
├── dags/
│   ├── _common.py             общие default_args (retries, on_failure_callback)
│   ├── hello_olist.py         задание 1 – sanity-DAG
│   ├── olist_ingest.py        задания 2–3 – CSV → source DBs (full / incremental)
│   ├── warehouse_staging.py   задания 4, 6 – source → staging + branch на row-counts
│   ├── warehouse_analytics.py задание 5 – staging → analytics + валидатор
│   ├── ml_training.py         задание 7 – train_lr + train_gbr + quality gate
│   ├── ml_inference.py        задание 8 – batch-inference, datasets-driven
│   ├── master_pipeline.py     задание 9 – TriggerDagRunOperator-цепочка
│   └── drift_monitoring.py    задания 10–12 – Evidently report + TestSuite + react
└── include/
    ├── ddl/                   db_sales.sql, db_catalog.sql, warehouse.sql, drift.sql
    ├── etl/load.py            COPY-загрузка CSV (full / incremental)
    ├── warehouse/staging.py   COPY-стриминг source → warehouse.staging
    ├── warehouse/analytics.py INSERT … SELECT для dim/facts
    ├── alerts/telegram.py     notify_failure / notify_text через Telegram Bot API
    ├── drift/sql.py           общий feature-SQL и описание фич
    ├── drift/report.py        build_drift_report (Evidently 0.4.x)
    ├── drift/tests.py         TestSuite + run_test_suite
    └── ml/training.py         self-contained train_model (lr, gbr)
```

`satisfaction/`-пакет из проекта 2 в include/ копировать необязательно: тренер `include/ml/training.py`
работает напрямую от feature-SQL и совместим с тем же набором признаков, что и проект 2 (`price`,
`freight_value`, `revenue`, `product_category_name_english`, целевая переменная `review_score`).

> **Замечание про quality gate.** Этот тренер – минималистичный baseline без feature engineering из
> проекта 2 (рабочих дней доставки, `is_late`, ценовых отношений и т. д.). На этих 4 признаках он
> упирается в ROC-AUC ~0.55–0.58, поэтому в решении `QUALITY_GATE_THRESHOLD = 0.55`. Если хочешь
> воспроизвести порог 0.65 из README проекта – подключи `satisfaction/` целиком как
> `include/satisfaction/` и вызывай `train_pipeline` оттуда (см. бонусный пункт в задании 7).

## Запуск

```bash
cd solutions/03-de/project_3
docker compose up -d
docker compose ps        # дождись healthy для всех сервисов
```

UI – `http://localhost:8080`, логин/пароль `airflow`/`airflow`.

Перед первым запуском в UI (`Admin → Connections`) создай:

| `Conn Id`            | Type     | Host             | Schema       | Login | Password |
|----------------------|----------|------------------|--------------|-------|----------|
| `postgres_sales`     | Postgres | `db_sales`       | `sales`      | `olist` | `olist` |
| `postgres_catalog`   | Postgres | `db_catalog`     | `catalog`    | `olist` | `olist` |
| `postgres_warehouse` | Postgres | `warehouse`      | `warehouse`  | `olist` | `olist` |
| `fs_default`         | File     | –                | –            | –     | (Extra: `{"path":"/opt/airflow/datasets"}`) |

(Опционально) `Admin → Variables`: `tg_token`, `tg_chat_id` – без них Telegram-алерты пишут в лог
warning'ом.

Положи CSV-файлы Olist в `datasets/`: `olist_orders_dataset.csv`, `olist_order_items_dataset.csv`,
`olist_products_dataset.csv`, `product_category_name_translation.csv`,
`olist_order_reviews_dataset.csv`.

## Порядок прогонов

1. `hello_olist` – проверь, что connection `postgres_sales` живой.
2. `olist_ingest` – загружает CSV в `db_sales` и `db_catalog` (~10–20 секунд).
3. `warehouse_staging` – переносит в `warehouse.staging.*`.
4. `warehouse_analytics` – строит `dim_products`, `facts_sales`, `facts_reviews`.
5. `ml_training` – обучает две модели, выбирает победителя, обновляет симлинк
   `artefacts/latest`. Это автоматически триггерит `ml_inference` через `Datasets`.
6. `master_pipeline` – тот же путь от ingest до inference, но триггерится по cron `0 2 * * *`.
7. `drift_monitoring` – еженедельно сравнивает свежее окно с reference.

## Проверка дрифта

После полного прогона протестируй реакцию на drift:

```sql
UPDATE analytics.facts_sales
SET price = price * 1.5
WHERE order_id IN (
    SELECT order_id FROM analytics.facts_sales ORDER BY random() LIMIT 30000
);
```

Запусти `drift_monitoring` – `dataset_drift = true` в `analytics.drift_metrics`, инцидент в
`analytics.drift_incidents`, новый запуск `ml_training`. Откатить можно повторным прогоном
`warehouse_analytics` (он перестроит `facts_sales` из staging).

## Ожидаемые row-counts

| Таблица | Rows |
|---------|------|
| `staging.orders` | 99 441 |
| `staging.order_items` | 112 650 |
| `staging.products` | 32 951 |
| `staging.category_translation` | 71 |
| `staging.reviews` | 99 224 |
| `analytics.dim_products` | 32 951 |
| `analytics.facts_sales` | 112 650 |
| `analytics.facts_reviews` | 99 224 |

## Известные нюансы

- **Logical date alignment.** `ExternalTaskSensor` выровнен на полночь (`execution_date_fn`), поэтому
  при ручном triggering всех трёх DAG'ов (`olist_ingest`, `warehouse_staging`, `warehouse_analytics`)
  передавай одну и ту же `-e 2026-04-27T00:00:00+00:00`, иначе сенсор не найдёт upstream. Через
  `master_pipeline` (TriggerDagRunOperator) выравнивание происходит автоматически.
- **`schedule=[Dataset]` и manual trigger.** `ml_inference` запускается автоматически после успеха
  `ml_training` через `Datasets`. При ручном `airflow dags trigger ml_inference` Airflow 2.10 для
  Dataset-расписаний не разворачивает task'и в новом dag_run'е. Чтобы прогнать inference вручную с
  конкретной датой – используй `airflow tasks test ml_inference <task_id> 2018-08-01` (см. раздел
  «Проверка дрифта» ниже).
- **Окно inference.** В Olist данных нет за сегодняшний день, поэтому `extract_recent_orders` имеет
  fallback: если за окно `data_interval_start..data_interval_end` нет заказов – берёт последние 365
  дней от `data_interval_end`.
