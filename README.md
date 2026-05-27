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

| Column      | Description                             |
|-------------|-----------------------------------------|
| `date`      | Observation date (any parseable format) |
| `series_id` | FRED series identifier                  |
| `value`     | Numeric observation value               |

### FRED Series Used

| Series ID        | Description                                  | Native Frequency |
|------------------|----------------------------------------------|------------------|
| `INDPRO`         | Industrial Production Index                  | Monthly          |
| `BUSLOANS`       | Commercial & Industrial Loans                | Monthly          |
| `JTSJOL`         | Job Openings (JOLTS)                         | Monthly          |
| `BAMLH0A0HYM2`   | High-Yield Credit Spread (inverted)          | Daily            |
| `PNFI`           | Private Nonresidential Fixed Investment      | Quarterly        |

> Data is filtered to observations from **January 1, 2000 onward**. However, see the [Known Issue](#known-issue-frequency-mismatch-causes-data-gap) below — without frequency alignment, the composite index will contain very few usable observations despite this date filter.

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
Creates an `activity_index_input` table in the same database by pivoting the five FRED series into wide format, grouped by exact date.

**Stage 3 — PCA & Visualization**
Standardizes the five indicators, extracts the first principal component, rescales it to 0–100, and saves the chart as `activity_index.png`.

---

## Outputs

| File                  | Description                                       |
|-----------------------|---------------------------------------------------|
| `activity_index.db`   | SQLite database with raw and pivoted FRED data    |
| `activity_index.png`  | Time-series chart of the composite index          |

The console will also print:
- Row count loaded into the database
- A 5-row preview of the pivoted input table
- The variance explained by the first principal component
- The full activity index series

---

## Known Issue: Frequency Mismatch Causes Data Gap

**The chart produced by the current script will appear nearly blank for 2000–2023**, with index values only populating in the most recent window. This is a data alignment problem, not a code error.

**Root cause:** The five FRED series are published at different frequencies — `PNFI` is quarterly, `BAMLH0A0HYM2` is daily, and the remaining three are monthly. The pivot in Stage 2 groups rows by exact date string. After pivoting, `dropna()` in the PCA stage drops every row that is missing any one series. Because these series rarely share an identical timestamp, the vast majority of dates are eliminated.

**Recommended fix:** Resample all series to a common frequency (monthly recommended) before pivoting. Replace the Stage 2 pivot logic with something like the following in Python:

```python
import pandas as pd
import sqlite3

conn = sqlite3.connect('activity_index.db')
df = pd.read_sql('SELECT * FROM fred_series', conn)
conn.close()

df['date'] = pd.to_datetime(df['date'])

# Resample each series to month-end frequency
df_monthly = (
    df.groupby('series_id')
    .apply(lambda g: g.set_index('date')['value'].resample('ME').last())
    .reset_index()
)
df_monthly.columns = ['series_id', 'date', 'value']

# Pivot to wide format
pivot = df_monthly.pivot(index='date', columns='series_id', values='value')
pivot = pivot.rename(columns={
    'INDPRO':        'indpro',
    'BUSLOANS':      'busloans',
    'JTSJOL':        'job_openings',
    'BAMLH0A0HYM2':  'credit_spread',
    'PNFI':          'bus_investment'
})
pivot = pivot[pivot.index >= '2000-01-01'].sort_index()
```

Write this resampled pivot table back to `activity_index_input` before running Stage 3. After this fix, the chart should display a continuous index from 2001 onward (JOLTS data begins December 2000; prior months will still be dropped by `dropna()`).

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

- **Coverage start:** The effective start date for the composite index is approximately **December 2000**, when JOLTS job openings data (`JTSJOL`) begins. Dates prior to that will be dropped by `dropna()` regardless of coverage in the other four series.
- **Relative index:** The 0–100 scale is relative to the sample period, not an external benchmark. A reading of 100 means the strongest conditions observed within the data window, not an absolute maximum.
- **NBER recession shading:** Recession bands are hardcoded for the 2001, 2007–2009, and 2020 downturns. Update the `recessions` list in the script to add any subsequent NBER-designated recession periods.
- **Quarterly series interpolation:** After monthly resampling, `PNFI` values will repeat within each quarter (last-observation-carried-forward via `.last()`). This is a reasonable approximation but slightly smooths the quarterly signal.
