# Corporate Business Activity Index

A data pipeline and composite economic indicator that combines multiple FRED macroeconomic series into a single, interpretable business activity index using Principal Component Analysis (PCA).

---

## Overview

This project fetches macroeconomic data from the Federal Reserve Economic Data (FRED) database, stores it in a local SQLite database, and applies PCA to distill five economic indicators into one composite index scaled from 0 (weakest conditions) to 100 (strongest conditions). The result is exported as a chart with NBER recession shading for context.

---

## Features

- Ingests and cleans FRED data from a CSV source
- Stores raw and pivoted data in a local SQLite database
- Inverts the credit spread so all indicators point in the same direction
- Standardizes all series before applying PCA
- Outputs a normalized 0–100 composite activity index
- Generates a publication-ready chart with recession bands annotated

---

## Requirements

Install dependencies with pip:

```bash
pip install pandas numpy scikit-learn matplotlib
```

SQLite3 is included in Python's standard library — no additional installation needed.

---

## Input Data

The project expects a CSV file named `fred_data.csv` in the working directory with the following columns:

| Column      | Description                          |
|-------------|--------------------------------------|
| `date`      | Observation date (any parseable format) |
| `series_id` | FRED series identifier               |
| `value`     | Numeric observation value            |

### FRED Series Used

| Series ID       | Description                         |
|-----------------|-------------------------------------|
| `INDPRO`        | Industrial Production Index         |
| `BUSLOANS`      | Commercial & Industrial Loans       |
| `JTSJOL`        | Job Openings (JOLTS)                |
| `BAMLH0A0HYM2`  | High-Yield Credit Spread (inverted) |
| `PNFI`          | Private Nonresidential Fixed Investment |

> Data is filtered to observations from **January 1, 2000 onward**.

---

## Usage

Run the script from your terminal:

```bash
python Navan_Project1.py
```

The script executes three stages in sequence:

**Stage 1 — Load & Store**
Reads `fred_data.csv`, parses dates, and writes the data into a SQLite database (`activity_index.db`) with a table called `fred_series`.

**Stage 2 — Pivot**
Creates an `activity_index_input` table in the same database by pivoting the five FRED series into wide format, grouped by date.

**Stage 3 — PCA & Visualization**
Standardizes the five indicators, extracts the first principal component, rescales it to 0–100, and saves the chart as `activity_index.png`.

---

## Outputs

| File                  | Description                                       |
|-----------------------|---------------------------------------------------|
| `activity_index.db`   | SQLite database with raw and pivoted FRED data    |
| `activity_index.png`  | Time-series chart of the composite index (2000–present) |

The console will also print:
- Row count loaded into the database
- A 5-row preview of the pivoted input table
- The variance explained by the first principal component
- The full activity index series

---

## Methodology

1. **Inversion** — The high-yield credit spread (`BAMLH0A0HYM2`) is multiplied by −1 so that all five indicators are positively correlated with strong business conditions.
2. **Standardization** — Each series is z-scored using `StandardScaler` to remove scale differences before PCA.
3. **PCA** — The first principal component (PC1) captures the shared variance across all five indicators and serves as the composite index.
4. **Rescaling** — PC1 scores are min-max normalized to a 0–100 range for interpretability.

---

## Project Structure

```
.
├── Navan_Project1.py       # Main script
├── fred_data.csv           # Input data (user-supplied)
├── activity_index.db       # SQLite output (generated)
└── activity_index.png      # Chart output (generated)
```

---

## Notes

- Rows with any missing values across the five series are dropped before PCA (`dropna()`). Ensure your input data has reasonable coverage across all five series to avoid significant data loss.
- The index is **relative**, not absolute — it reflects conditions within the sample period, not against an external benchmark.
- NBER recession dates are hardcoded for 2001, 2007–2009, and 2020. Update the `recessions` list in the script to extend coverage.
