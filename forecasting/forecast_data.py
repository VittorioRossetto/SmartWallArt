from influxdb import InfluxDBClient
import pandas as pd
from statsmodels.tsa.arima.model import ARIMA
from sklearn.metrics import mean_squared_error, mean_absolute_error
import matplotlib.pyplot as plt

# === Config ===
SENSOR_FIELDS = ['temperature', 'humidity', 'light']
DB_HOST = 'localhost'
DB_PORT = 8086
DB_NAME = 'smartart'

# === Step 1: Read from InfluxDB ===
client = InfluxDBClient(host=DB_HOST, port=DB_PORT, database=DB_NAME)
field_str = ', '.join(['"{}"'.format(f) for f in SENSOR_FIELDS])
query = f'SELECT {field_str} FROM "sensor_data" WHERE time > now() - 6h'
result = client.query(query)
points = list(result.get_points())
df = pd.DataFrame(points)

df['time'] = pd.to_datetime(df['time'])
df.set_index('time', inplace=True)
df = df.dropna()

# === Step 2: Forecasting Function ===
def forecast_series(series, label, order=(2, 1, 2)):
    print(f"\n--- Forecasting {label} ---")
    data = series.resample('1T').mean().interpolate()

    split = int(0.8 * len(data))
    train, test = data[:split], data[split:]

    model = ARIMA(train, order=order)
    model_fit = model.fit()
    forecast = model_fit.forecast(steps=len(test))

    mae = mean_absolute_error(test, forecast)
    mse = mean_squared_error(test, forecast)

    print(f"{label} - MAE: {mae:.2f}, MSE: {mse:.2f}")

    # Plot
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
        forecast_series(df[field], label=field)
    else:
        print(f"Warning: Field '{field}' not found in data.")
