ML Pipeline – Reference Solution
==============================

Полное решение проекта [AI_Data_Engineering.Project_2](../../../../production/AI_Data_Engineering.Project_2.ID_1577980).

## Что внутри

Зеркало папки `src/` из задания, но все `# TODO` и `raise NotImplementedError` доведены до рабочей реализации:

| Файл                                    | Что сделано                                                                              |
|-----------------------------------------|------------------------------------------------------------------------------------------|
| `configs/config.yaml`                   | Раскомментирован `model: lr`                                                             |
| `configs/dataset/base.yaml`             | Прописан путь к датасету                                                                 |
| `configs/feature/base.yaml`             | Добавлен `target_col: "review_score"`                                                    |
| `satisfaction/entities/models.py`       | Реализован `GBRConfig` с type hints                                                      |
| `satisfaction/data/make_dataset.py`     | `read_data` с merge переводов, `drop_unused_columns`, stratified `split_train_test_data` |
| `satisfaction/features/build_features.py` | `AttributesAdder`, `TargetEncoder`, `build_categorical_pipeline` (onehot/target + SimpleImputer), `build_numerical_pipeline` (OutlierRemover + SimpleImputer + StandardScaler), полный `build_transformer` |
| `satisfaction/models/predict.py`        | `evaluate_model` с RMSE + ROC-AUC по бинаризации `review_score >= 4`                     |
| `satisfaction/train.py`                 | Полный pipeline с cross-validation и сохранением `model + transformer`                   |
| `satisfaction/predict.py`               | CLI для batch inference                                                                  |
| `tests/data/test_make_dataset.py`       | Добавлен `test_split_dataset` (размеры + распределение классов)                          |

## Запуск

Из папки `solution/`:

```
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# тесты
pytest tests

# обучение
python -m satisfaction.train hydra.job.chdir=True model=lr
python -m satisfaction.train hydra.job.chdir=True model=gbr

# инференс
python -m satisfaction.predict \
    --model-path artefacts/<run>/models/lin-reg.pkl \
    --transformer-path artefacts/<run>/models/transformer.pkl \
    --input-path ../../../../production/AI_Data_Engineering.Project_2.ID_1577980/datasets/olist_public_dataset_v2.csv \
    --output-path predictions.csv
```

## Ожидаемые метрики

| Модель                      | RMSE    | ROC-AUC (review_score ≥ 4) |
|-----------------------------|---------|----------------------------|
| LinearRegression            | ~1.2    | ~0.66                      |
| GradientBoostingRegressor   | ~1.15   | ~0.70                      |

Точные цифры зависят от `random_state` и версий sklearn; порог приёмки из
задания – `ROC-AUC > 0.65`.

## Подводные камни

- `workalendar.Brazil` очень медленный через `.apply(axis=1)` на 100k строк.
  В решении используется `lru_cache` по парам дат – прогон падает до ~30 секунд.
- `OneHotEncoder` даёт разреженную матрицу, поэтому `StandardScaler` идёт
  с `with_mean=False` (иначе ошибка про центрирование разреженных данных).
- `transformer` сохраняется отдельным pickle-ом, чтобы `predict.py`
  мог воспроизвести ту же трансформацию на новых данных.
- Split стратифицирован по `review_score`, иначе распределение классов в
  test смещается (см. раздел «Stratified Split» в EDA-ноутбуке).
