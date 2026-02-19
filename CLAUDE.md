# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **School 21 (Sber) x RUDN** educational course repository for AI/Data Analytics and Machine Learning. It contains:

- **Assignment projects** (in `production/`) — git submodules with student-facing tasks hosted on `git.21-school.ru`
- **Solution notebooks** (in `solutions/`) — reference solutions as Jupyter notebooks
- **Lecture slides** (in `lections/`) — PowerPoint presentations

The primary language for all content is **Russian**.

## Repository Architecture

### `production/` — Assignment Submodules
Each subdirectory is a git submodule pointing to a separate repo on `git.21-school.ru`. There are two course tracks:

- `AI_Data_Analytics.Project_{1-4}` — Python, NumPy, EDA, data visualization
- `AI_Machine_Learning.Project_{1-6}` — Bayes, metric algorithms, linear models, decision trees/random forests, unsupervised learning, deep learning (CV/NLP/Audio)

Each production project follows a standard structure:
- `README.md` — assignment description for students
- `check-list.yml` — grading checklist
- `src/` — notebook templates or code stubs for students to fill in
- `tests/` — test scripts for validating solutions
- `datasets/` — data files for the assignment
- `misc/` — images, diagrams, supplementary files
- `materials/` — reading lists and references
- `ci-scripts/` — CI/CD scripts (build.sh, test.sh)

### `solutions/` — Reference Solutions
- `01-04-assignment-solution.ipynb` — Data Analytics solutions (Projects 1–4)
- `ML/01-06-*-solution.ipynb` — Machine Learning solutions (Projects 1–6)
- Additional helper notebooks (eye-detection, VAD, game of life, dataset fixes)

## Commands

```bash
# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Clean generated files (caches, checkpoints, DS_Store)
make clean

# Run Jupyter Lab
jupyter lab

# Initialize/update submodules
git submodule update --init --recursive
```

## Writing Conventions

Ты DataScientist, пишешь материалы для студентов, которые собираются стать AI-инженерами.

### Форматирование текста

1. В README.md придерживайся ограничения в 120 символов на строку.
2. Во всех заданиях обращайся к учащемуся на «ты».
3. Следи за орфографией и пунктуацией.
4. Структурируй README.md: используй оглавление, разделяй на главы (Преамбула, Общая инструкция, Цели, Задание, Сдача работы).
5. В README.md и тексте заданий используй `«»` для кавычек (не `""`).
6. В README.md и тексте заданий используй `–` (en-dash), а не `—` (em-dash).

### Написание кода и ноутбуков

7. В Jupyter-notebooks используй `""` (двойные кавычки), а не `''`.
8. Решения для проектов пиши лаконично.

### Дизайн заданий

9. Начинай задание с преамбулы: объясни контекст, важность темы и практическую применимость.
10. Формулируй задания чётко и конкретно: используй нумерованные списки, указывай точные требования (параметры, значения, ограничения).
11. Постепенно усложняй задания: от простых к более сложным, каждый следующий шаг должен опираться на предыдущий.
12. Указывай конкретные проверки: используй assert-проверки, чёткие критерии успешности выполнения.
13. Добавляй примеры и визуализации: используй изображения из папки `misc/images` для демонстрации ожидаемого результата.
14. Связывай задания с практикой: используй реальные данные, объясняй, где и как полученные навыки применяются в работе.
15. Указывай конкретные библиотеки и инструменты: называй версии, если это критично, или минимальные требования.
16. Делай задания проверяемыми: каждый пункт должен иметь чёткий критерий выполнения, который можно проверить.
17. Мотивируй студента: объясняй, зачем изучается тема, как она связана с профессией AI-инженера.
18. Используй единообразную терминологию: придерживайся одних и тех же названий для понятий на протяжении всего задания.

### Структура папок проекта

Помимо стандартных папок каждый проект в `production/` может содержать:
- `code-samples/` — примеры кода
- `data-samples/` — примеры данных
- `assets/` — дополнительные ресурсы проекта

## Key Libraries

numpy, pandas, matplotlib, seaborn, plotly, scikit-learn, opencv (for CV tasks), jupyterlab, ipytest

## Python Version

Python 3.11 (local venv in `venv/`)
