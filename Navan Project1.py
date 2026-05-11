import pandas as pd
import sqlite3
df = pd.read_csv('fred_data.csv')
df['date']= pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')
df = df[df['date']>='2000-01-01']
conn = sqlite3.connect('activity_index.db')
cursor = conn.cursor()

cursor.execute("""
    CREATE TABLE IF NOT EXISTS fred_series (
        date      TEXT NOT NULL,
        series_id TEXT NOT NULL,
        value     REAL,
        PRIMARY KEY (date, series_id)
    )
""")

# Step 4 — Write your DataFrame into it
df.to_sql('fred_series', conn, if_exists='replace', index=False)
print(f"Loaded {len(df)} rows into fred_series")

# Step 5 — Build the pivot table (the analytical dataset for PCA)
cursor.execute("DROP TABLE IF EXISTS activity_index_input")
cursor.execute("""
    CREATE TABLE activity_index_input AS
    SELECT
        date,
        MAX(CASE WHEN series_id = 'INDPRO'        THEN value END) AS indpro,
        MAX(CASE WHEN series_id = 'BUSLOANS'      THEN value END) AS busloans,
        MAX(CASE WHEN series_id = 'JTSJOL'        THEN value END) AS job_openings,
        MAX(CASE WHEN series_id = 'BAMLH0A0HYM2' THEN value END) AS credit_spread,
        MAX(CASE WHEN series_id = 'PNFI'          THEN value END) AS bus_investment
    FROM fred_series
    WHERE date >= '2000-01-01'
    GROUP BY date
    ORDER BY date
""")

conn.commit()
conn.close()
print("Done! activity_index.db is ready.")

with sqlite3.connect('activity_index.db') as conn:
    result = pd.read_sql("SELECT * FROM activity_index_input LIMIT 5", conn)
    print(result)

# Build composite index with PCA

import numpy as np
import pandas as pd
import sqlite3
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA

conn = sqlite3.connect('activity_index.db')
df = pd.read_sql('SELECT * FROM activity_index_input ORDER BY date', conn)
conn.close()

df['date'] = pd.to_datetime(df['date'])
df = df.set_index('date').dropna()

# Invert credit spread so higher = better business conditions
df['credit_spread'] = -df['credit_spread']

# Standardize all series
scaler = StandardScaler()
scaled = scaler.fit_transform(df)

# Extract first principal component as composite index
pca = PCA(n_components=1)
index_raw = pca.fit_transform(scaled).flatten()

# Rescale to 0-100 for interpretability
index_min, index_max = index_raw.min(), index_raw.max()
df['activity_index'] = 100 * (index_raw - index_min) / (index_max - index_min)

print(f'Variance explained by PC1: {pca.explained_variance_ratio_[0]:.1%}')

# Visualize & export executive brief

import matplotlib.pyplot as plt
import matplotlib.dates as mdates

fig, ax = plt.subplots(figsize=(12, 5))
ax.plot(df.index, df['activity_index'], color='#0F5F6E', linewidth=2)
ax.fill_between(df.index, df['activity_index'], alpha=0.15, color='#0F5F6E')

# Annotate recessions (NBER dates)
recessions = [('2001-03','2001-11'), ('2007-12','2009-06'), ('2020-02','2020-04')]
for start, end in recessions:
    ax.axvspan(pd.to_datetime(start), pd.to_datetime(end),
               alpha=0.12, color='gray', label='_nolegend_')

ax.set_title('Corporate Business Activity Index', fontsize=14, fontweight='bold', color='#0F5F6E')
ax.set_ylabel('Index (0 = weakest, 100 = strongest)', fontsize=11)
ax.xaxis.set_major_locator(mdates.YearLocator(2))
ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
ax.grid(axis='y', linestyle='--', alpha=0.4)
plt.tight_layout()
plt.savefig('activity_index.png', dpi=150)
plt.show()

print(df['activity_index'])

