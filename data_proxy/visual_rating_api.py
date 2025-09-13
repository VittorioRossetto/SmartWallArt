
# Import required libraries
import json  # For JSON handling
from flask import Flask, request, jsonify  # For API endpoints
from influxdb import InfluxDBClient  # For connecting to InfluxDB
from datetime import datetime  # For timestamps


# === Configuration ===
INFLUX_HOST = "localhost"  # InfluxDB host
INFLUX_PORT = 8086         # InfluxDB port
INFLUX_DB = "smartart"    # InfluxDB database name


# === Initialize Client ===
influx_client = InfluxDBClient(host=INFLUX_HOST, port=INFLUX_PORT, database=INFLUX_DB)  # Connect to InfluxDB
app = Flask(__name__)  # Create Flask app


# === API: Get Latest Visual (motion == 1) ===
@app.route('/latest_visual', methods=['GET'])
def latest_visual():
    # Query InfluxDB for the latest sensor entry where motion == 1, in sensor_data only measurements that generated a visual are stored 
    query = 'SELECT * FROM sensor_data ORDER BY time DESC LIMIT 1'
    result = influx_client.query(query)  # Execute query
    points = list(result.get_points())  # Get results as list
    if points:
        return jsonify(points[0]), 200  # Return latest visual as JSON
    else:
        return jsonify({'error': 'No visual found'}), 404  # Return error if not found


# === API: Store Rating ===
@app.route('/rate_visual', methods=['POST'])
def rate_visual():
    # Store a rating for a visual in InfluxDB
    data = request.json  # Get JSON payload from request
    required = ['user_id', 'rating', 'visual_time']  # Required fields
    if not all(k in data for k in required):
        return jsonify({'error': 'Missing fields'}), 400  # Error if missing fields
    try:
        # Prepare InfluxDB entry
        json_body = [{
            "measurement": "visual_ratings",
            "tags": {
                "user_id": str(data['user_id'])  # Store user ID as tag
            },
            "fields": {
                "rating": int(data['rating']),  # Store rating value
                "visual_time": str(data['visual_time']),  # Store visual timestamp
                "timestamp": datetime.utcnow().isoformat() + "Z"  # Store current UTC timestamp
            }
        }]
        influx_client.write_points(json_body)  # Write to InfluxDB
        return jsonify({'status': 'success'}), 200  # Success response
    except Exception as e:
        return jsonify({'error': str(e)}), 500  # Error response


# === Main Entrypoint ===
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5050, threaded=True)  # Run Flask app on port 5050
