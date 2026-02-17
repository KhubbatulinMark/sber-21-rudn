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

## Writing Conventions (from Cursor Rules)

When writing or editing assignments and solutions:

1. **Audience**: You are a DataScientist writing for students training to become AI engineers. Address students with «ты» (informal "you").
2. **Strings in code**: Use `""` (double quotes), not `''`.
3. **Text in README/assignments**: Use `«»` for quotation marks, `–` (en-dash) instead of `—` (em-dash).
4. **README formatting**: Keep lines under 120 characters. Structure documents with: Преамбула, Общая инструкция, Цели, Задание, Сдача работы.
5. **Assignment design**: Start with context/motivation, use numbered lists, specify exact requirements, include assert-based checks, progress from simple to complex, reference images from `misc/`.
6. **Consistency**: Use uniform terminology throughout assignments.

## Key Libraries

numpy, pandas, matplotlib, seaborn, plotly, scikit-learn, opencv (for CV tasks), jupyterlab, ipytest

## Python Version

Python 3.11 (local venv in `venv/`)
