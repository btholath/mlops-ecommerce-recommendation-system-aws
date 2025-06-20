#Domain-Specific Feature Creation
# Example: Creating features for a time-series dataset
# Simulating a time-series dataset
import pandas as pd
import numpy as np
import logging



dates = pd.date_range('2020-01-01', '2023-12-31', freq='D')
ts_data = pd.DataFrame({
    'date': dates,
    'sales': np.random.normal(1000, 200, len(dates)) + 
             50 * np.sin(2 * np.pi * np.arange(len(dates)) / 365.25)  # Annual seasonality
})

# Time-based features
ts_data['year'] = ts_data['date'].dt.year
ts_data['month'] = ts_data['date'].dt.month
ts_data['day_of_week'] = ts_data['date'].dt.dayofweek
ts_data['day_of_year'] = ts_data['date'].dt.dayofyear
ts_data['quarter'] = ts_data['date'].dt.quarter
ts_data['is_weekend'] = (ts_data['day_of_week'] >= 5).astype(int)

# Cyclical encoding for periodic features
ts_data['month_sin'] = np.sin(2 * np.pi * ts_data['month'] / 12)
ts_data['month_cos'] = np.cos(2 * np.pi * ts_data['month'] / 12)
ts_data['day_sin'] = np.sin(2 * np.pi * ts_data['day_of_week'] / 7)
ts_data['day_cos'] = np.cos(2 * np.pi * ts_data['day_of_week'] / 7)

# Rolling statistics
ts_data['sales_ma_7'] = ts_data['sales'].rolling(window=7).mean()
ts_data['sales_ma_30'] = ts_data['sales'].rolling(window=30).mean()
ts_data['sales_std_7'] = ts_data['sales'].rolling(window=7).std()

# Lag features
for lag in [1, 7, 30]:
    ts_data[f'sales_lag_{lag}'] = ts_data['sales'].shift(lag)

print("Time-series features created:")
print(ts_data.columns.tolist())