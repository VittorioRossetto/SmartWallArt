import pandas as pd
from influxdb import InfluxDBClient
from sklearn.ensemble import RandomForestRegressor
import joblib

# === Config ===
INFLUX_HOST = "localhost"
INFLUX_PORT = 8086
INFLUX_DB = "smartart"
MODEL_PATH = "best_rating_model.pkl"

# === Connect to InfluxDB ===
client = InfluxDBClient(host=INFLUX_HOST, port=INFLUX_PORT, database=INFLUX_DB)

# === Extract Ratings ===
print("Fetching ratings from InfluxDB...")
ratings = list(client.query('SELECT * FROM visual_ratings').get_points())

sensor_rows = []
window_ns = 5 * 1_000_000_000  # 5 seconds in nanoseconds
for r in ratings:
    visual_time = r.get('visual_time')
    if not visual_time:
        continue
    try:
        vt_ns = int(pd.to_datetime(visual_time).value)
    except Exception as e:
        print(f"Could not parse visual_time {visual_time}: {e}")
        continue
    query = (
        f"SELECT * FROM sensor_data WHERE time >= {vt_ns - window_ns} AND time <= {vt_ns + window_ns} LIMIT 1"
    )
    sensor = list(client.query(query).get_points())
    if sensor:
        row = {**sensor[0], 'rating': r['rating']}
        sensor_rows.append(row)

if not sensor_rows:
    print("No matched sensor-rating pairs found.")
    exit(1)

# === Build DataFrame ===
df = pd.DataFrame(sensor_rows)
print(f"Extracted {len(df)} samples.")

# === Prepare Data ===
features = ['light', 'temperature', 'humidity']
X = df[features]
y = df['rating']

# === Train Model ===
print("Training RandomForestRegressor...")
model = RandomForestRegressor(n_estimators=100, random_state=42)
model.fit(X, y)

print("Feature importances:")
for f, imp in zip(features, model.feature_importances_):
    print(f"  {f}: {imp:.3f}")

# === Save Model ===
joblib.dump(model, MODEL_PATH)
print(f"Model saved to {MODEL_PATH}")
