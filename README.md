# Corporate Business Activity Index

A data pipeline and composite economic indicator that combines multiple FRED macroeconomic series into a single, interpretable business activity index using Principal Component Analysis (PCA).

---

## Overview

This project reads macroeconomic data from a FRED CSV export, stores it in a local SQLite database, resamples all series to a common monthly frequency, and applies PCA to distill five economic indicators into one composite index scaled from 0 (weakest conditions) to 100 (strongest conditions). The result is exported as a publication-ready chart with NBER recession shading and a variance-explained annotation.

---

## Features

- Ingests and cleans FRED data from a CSV source
- Stores raw data in a local SQLite database
- Resamples all series to a common monthly frequency before pivoting, correctly handling daily, monthly, and quarterly source data
- Inverts the credit spread so all five indicators point in the same direction
- Standardizes all series before applying PCA
- Outputs a normalized 0–100 composite activity index
- Generates a chart with a dynamic x-axis, variance-explained label, and recession bands that auto-adjust to the data window

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

| Series ID       | Description                             | Native Frequency |
|-----------------|-----------------------------------------|------------------|
| `INDPRO`        | Industrial Production Index             | Monthly          |
| `BUSLOANS`      | Commercial & Industrial Loans           | Monthly          |
| `JTSJOL`        | Job Openings (JOLTS)                    | Monthly          |
| `BAMLH0A0HYM2`  | High-Yield Credit Spread (inverted)     | Daily            |
| `PNFI`          | Private Nonresidential Fixed Investment | Quarterly        |

> The composite index can only be computed for months where all five series have coverage. The effective date range of the output is therefore determined by whichever series has the shortest history in your `fred_data.csv`. With the current CSV, the index runs from **April 2023 to October 2025** (31 months), limited by the credit spread data. To extend the window back to 2000, re-pull `BAMLH0A0HYM2` from FRED for the full history and rebuild the CSV.

---

## Usage

Run the script from your terminal:

```bash
python Navan_Project1.py
```

The script executes three stages in sequence:

**Stage 1 — Load & Store**
Reads `fred_data.csv`, parses and filters dates to 2000-01-01 onward, and writes all observations into a SQLite database (`activity_index.db`) in a table called `fred_series`.

**Stage 2 — Resample & Pivot**
Reads `fred_series` back into Python and resamples each series individually to month-start frequency using a `to_monthly()` helper before joining them into a wide-format table. The resampling rules differ by native frequency:

| Native frequency | Resampling treatment                                      |
|------------------|-----------------------------------------------------------|
| Daily            | Monthly mean of all observations in the calendar month   |
| Monthly          | Preserved as-is (monthly mean of one value is itself)    |
| Quarterly        | Monthly mean, then forward-filled to fill intervening months |

The resulting wide table is written back to `activity_index.db` as `activity_index_input`.

**Stage 3 — PCA & Visualization**
Reads `activity_index_input`, drops any months with missing values, standardizes the five indicators, extracts the first principal component, rescales it to 0–100, and saves the chart as `activity_index.png`. The chart x-axis and title update dynamically to match the actual data window.

---

## Outputs

| File                | Description                                    |
|---------------------|------------------------------------------------|
| `activity_index.db` | SQLite database with raw and pivoted FRED data |
| `activity_index.png`| Time-series chart of the composite index       |

The console also prints:
- Row count loaded into `fred_series`
- A 5-row preview of `activity_index_input`
- The number of monthly observations used in PCA and their date range
- The variance explained by PC1
- The 10 most recent index values

---

## Methodology

1. **Frequency alignment** — All five series are resampled to month-start frequency before any joining occurs. This ensures that `dropna()` only removes months with genuinely missing data rather than discarding valid observations due to timestamp mismatches between daily, monthly, and quarterly series.
2. **Inversion** — The high-yield credit spread (`BAMLH0A0HYM2`) is multiplied by −1 so that all five indicators are positively correlated with strong business conditions.
3. **Standardization** — Each series is z-scored using `StandardScaler` to remove scale differences before PCA.
4. **PCA** — The first principal component (PC1) captures the shared variance across all five indicators and serves as the composite index. With the current data, PC1 explains approximately **63% of total variance**.
5. **Rescaling** — PC1 scores are min-max normalized to a 0–100 range for interpretability.

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

- **Extending the date range:** The current `fred_data.csv` contains `BAMLH0A0HYM2` data only from April 2023 onward, which constrains the composite index to that window. All other series have coverage back to January 2000. Pulling the full credit spread history from FRED and appending it to the CSV is the only change needed to produce a 25-year index.
- **JOLTS floor:** Even with a complete credit spread history, the index cannot start before December 2000 because `JTSJOL` (JOLTS) was first published then.
- **Relative scale:** The 0–100 score is relative to the sample period in the CSV, not an external benchmark. A reading of 100 represents the strongest conditions observed within the data window, not an absolute maximum.
- **Quarterly forward-fill:** `PNFI` values are carried forward to fill the two months between each quarterly release. This is a standard approximation but slightly smooths the quarterly signal.
- **NBER recession shading:** Bands are hardcoded for the 2001, 2007–2009, and 2020 recessions. The chart only renders a band if it overlaps the actual data window, so no phantom shading appears on an empty axis. Update the `recessions` list in the script to add any future NBER-designated periods.
