
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
query = f'SELECT {field_str} FROM "sensor_data" WHERE time > now() - 6h'  # Query last 6 hours of data
result = client.query(query)  # Execute query
points = list(result.get_points())  # Get results as list of dicts
df = pd.DataFrame(points)  # Convert to DataFrame

df['time'] = pd.to_datetime(df['time'])  # Convert time column to datetime
df.set_index('time', inplace=True)  # Set time as index
df = df.dropna()  # Drop rows with missing values


# === Step 2: Forecasting Function ===
def forecast_series(series, label, order=(2, 1, 2)):
    # Forecast a single sensor field using ARIMA
    print(f"\n--- Forecasting {label} ---")
    data = series.resample('1T').mean().interpolate()  # Resample to 1-minute intervals and interpolate missing values

    split = int(0.8 * len(data))  # 80% for training, 20% for testing
    train, test = data[:split], data[split:]

    model = ARIMA(train, order=order)  # Create ARIMA model
    model_fit = model.fit()  # Fit model to training data
    forecast = model_fit.forecast(steps=len(test))  # Forecast for test period

    mae = mean_absolute_error(test, forecast)  # Mean Absolute Error
    mse = mean_squared_error(test, forecast)   # Mean Squared Error

    print(f"{label} - MAE: {mae:.2f}, MSE: {mse:.2f}")  # Print evaluation metrics

    # Plot actual vs. forecasted values
    plt.figure(figsize=(10, 4))
    plt.plot(test.index, test.values, label='Actual')
    plt.plot(test.index, forecast, label='Forecast')
    plt.title(f'{label.capitalize()} Forecast')
    plt.legend()
    plt.grid(True)
    plt.show()


# === Step 3: Forecast Each Field ===
for field in SENSOR_FIELDS:
    if field in df.columns:
        forecast_series(df[field], label=field)  # Forecast for each sensor field
    else:
        print(f"Warning: Field '{field}' not found in data.")  # Warn if field missing
