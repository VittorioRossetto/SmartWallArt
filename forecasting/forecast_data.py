
# Import required libraries
from influxdb import InfluxDBClient  # For connecting to InfluxDB
import pandas as pd  # For data manipulation
from statsmodels.tsa.arima.model import ARIMA  # For time series forecasting
from sklearn.metrics import mean_squared_error, mean_absolute_error  # For evaluation
import matplotlib.pyplot as plt  # For plotting results


# === Config ===
SENSOR_FIELDS = ['temperature', 'humidity', 'light']  # Sensor fields to forecast
DB_HOST = 'localhost'  # InfluxDB host
DB_PORT = 8086        # InfluxDB port
DB_NAME = 'smartart'  # InfluxDB database name

# === Step 1: Read from InfluxDB ===
client = InfluxDBClient(host=DB_HOST, port=DB_PORT, database=DB_NAME)  # Connect to InfluxDB
field_str = ', '.join(['"{}"'.format(f) for f in SENSOR_FIELDS])  # Build field string for query
query = f'SELECT {field_str} FROM "sensor_data"'  # Query last 2400 hours of data WHERE time > now() - 6h
print("InfluxDB Query:", query)
result = client.query(query)  # Execute query
points = list(result.get_points())  # Get results as list of dicts
print(f"Retrieved {len(points)} points from InfluxDB.")
print("Sample points:", points[:8])  # Print first 2 points for debugging
df = pd.DataFrame(points)  # Convert to DataFrame

# Check if DataFrame is empty
if df.empty:
    print("No data returned from InfluxDB. DataFrame is empty.")
    exit(1)

# Print columns for debugging
print("DataFrame columns:", df.columns.tolist())

# Check for 'time' column
if 'time' not in df.columns:
    print("Error: 'time' column not found in data. Columns returned:", df.columns.tolist())
    exit(1)

df['time'] = pd.to_datetime(df['time'])  # Convert time column to datetime
df.set_index('time', inplace=True)  # Set time as index
df = df.dropna()  # Drop rows with missing values


# === Step 2: Forecasting Function ===

# === Step 2: Forecasting Function ===
def forecast_series(series, label, ax, order=(2, 1, 2)):
    # Forecast a single sensor field using ARIMA and plot on provided axis
    print(f"\n--- Forecasting {label} ---")
    data = series.resample('5S').mean().interpolate()  # Resample to 5-second intervals and interpolate missing values

    print(f"{label} series length after resample/interpolate: {len(data)}")
    print(f"{label} series head:\n", data.head())

    # Check if data is empty or all NaN
    if data.empty or data.isna().all():
        print(f"Skipping {label}: series is empty or all NaN after resampling/interpolation.")
        return

    # Minimum data points required for ARIMA
    MIN_POINTS = 10
    if len(data) < MIN_POINTS:
        print(f"Skipping {label}: not enough data points for ARIMA (found {len(data)}, need at least {MIN_POINTS}).")
        return

    split = int(0.8 * len(data))  # 80% for training, 20% for testing
    train, test = data[:split], data[split:]

    # Check if train or test is empty
    if train.empty or test.empty:
        print(f"Skipping {label}: train or test split is empty.")
        return

    model = ARIMA(train, order=order)  # Create ARIMA model
    try:
        model_fit = model.fit()  # Fit model to training data
        forecast = model_fit.forecast(steps=len(test))  # Forecast for test period
    except Exception as e:
        print(f"Error fitting ARIMA for {label}: {e}")
        return

    mae = mean_absolute_error(test, forecast)  # Mean Absolute Error
    mse = mean_squared_error(test, forecast)   # Mean Squared Error

    print(f"{label} - MAE: {mae:.2f}, MSE: {mse:.2f}")  # Print evaluation metrics

    # Plot actual vs. forecasted values on the provided axis
    ax.plot(test.index, test.values, label='Actual')
    ax.plot(test.index, forecast, label='Forecast')
    ax.set_title(f'{label.capitalize()} Forecast')
    ax.legend()
    ax.grid(True)


# === Step 3: Forecast Each Field (all plots in one figure) ===
fig, axes = plt.subplots(3, 1, figsize=(12, 10), sharex=True)
plotted = 0
for idx, field in enumerate(SENSOR_FIELDS):
    if field in df.columns:
        forecast_series(df[field], label=field, ax=axes[idx])  # Forecast for each sensor field
        plotted += 1
    else:
        print(f"Warning: Field '{field}' not found in data.")  # Warn if field missing

if plotted:
    plt.tight_layout()
    plt.show()
