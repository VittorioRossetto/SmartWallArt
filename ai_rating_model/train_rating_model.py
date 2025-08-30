
# Import necessary libraries
import pandas as pd  # For data manipulation
from influxdb import InfluxDBClient  # For connecting to InfluxDB
from sklearn.ensemble import RandomForestRegressor  # For training the model
import joblib  # For saving/loading the trained model


# === Configuration ===
# InfluxDB connection details
INFLUX_HOST = "localhost"
INFLUX_PORT = 8086
INFLUX_DB = "smartart"
# Path to save the trained model
MODEL_PATH = "best_rating_model.pkl"


# === Connect to InfluxDB ===
# Create a client to interact with the database
client = InfluxDBClient(host=INFLUX_HOST, port=INFLUX_PORT, database=INFLUX_DB)


# === Extract Ratings ===
# Fetch all rating entries from the 'visual_ratings' measurement
print("Fetching ratings from InfluxDB...")
ratings = list(client.query('SELECT * FROM visual_ratings').get_points())


# === Match Ratings to Sensor Data ===
# For each rating, find the closest sensor data entry within ±5 seconds
sensor_rows = []  # List to store matched sensor-rating pairs
window_ns = 5 * 1_000_000_000  # 5 seconds in nanoseconds
for r in ratings:
    visual_time = r.get('visual_time')  # ISO8601 timestamp from rating
    if not visual_time:
        continue  # Skip if missing
    try:
        # Convert visual_time to nanoseconds for InfluxDB time comparison
        vt_ns = int(pd.to_datetime(visual_time).value)
    except Exception as e:
        print(f"Could not parse visual_time {visual_time}: {e}")
        continue
    # Query sensor_data for entries within ±5 seconds of visual_time
    query = (
        f"SELECT * FROM sensor_data WHERE time >= {vt_ns - window_ns} AND time <= {vt_ns + window_ns} LIMIT 1"
    )
    sensor = list(client.query(query).get_points())
    if sensor:
        # Merge sensor data and rating into one row
        row = {**sensor[0], 'rating': r['rating']}
        sensor_rows.append(row)


# === Check for Matches ===
if not sensor_rows:
    print("No matched sensor-rating pairs found.")
    exit(1)


# === Build DataFrame ===
# Convert matched rows to a pandas DataFrame for analysis/modeling
df = pd.DataFrame(sensor_rows)
print(f"Extracted {len(df)} samples.")


# === Prepare Data for Model Training ===
# Select sensor features and target variable (rating)
features = ['light', 'temperature', 'humidity']
X = df[features]  # Feature matrix
y = df['rating']  # Target vector


# === Train the AI Model ===
print("Training RandomForestRegressor...")
# Create and train a random forest regressor to predict rating from sensor values
model = RandomForestRegressor(n_estimators=100, random_state=42)
model.fit(X, y)

# Print feature importances to understand which sensors matter most
print("Feature importances:")
for f, imp in zip(features, model.feature_importances_):
    print(f"  {f}: {imp:.3f}")


# === Save the Trained Model ===
# Persist the model to disk for later use in art generation
joblib.dump(model, MODEL_PATH)
print(f"Model saved to {MODEL_PATH}")
