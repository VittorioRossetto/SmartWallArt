import json
from flask import Flask, request, jsonify
from influxdb import InfluxDBClient
from datetime import datetime

# === Configuration ===
INFLUX_HOST = "localhost"
INFLUX_PORT = 8086
INFLUX_DB = "smartart"

# === Initialize Client ===
influx_client = InfluxDBClient(host=INFLUX_HOST, port=INFLUX_PORT, database=INFLUX_DB)
app = Flask(__name__)

# === API: Get Latest Visual (motion == 1) ===
@app.route('/latest_visual', methods=['GET'])
def latest_visual():
    query = 'SELECT * FROM sensor_data WHERE motion = 1 ORDER BY time DESC LIMIT 1'
    result = influx_client.query(query)
    points = list(result.get_points())
    if points:
        return jsonify(points[0]), 200
    else:
        return jsonify({'error': 'No visual found'}), 404

# === API: Store Rating ===
@app.route('/rate_visual', methods=['POST'])
def rate_visual():
    data = request.json
    required = ['user_id', 'rating', 'visual_time']
    if not all(k in data for k in required):
        return jsonify({'error': 'Missing fields'}), 400
    try:
        json_body = [{
            "measurement": "visual_ratings",
            "tags": {
                "user_id": str(data['user_id'])
            },
            "fields": {
                "rating": int(data['rating']),
                "visual_time": str(data['visual_time']),
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        }]
        influx_client.write_points(json_body)
        return jsonify({'status': 'success'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5050, threaded=True)
