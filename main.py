from flask import Flask, render_template, jsonify
import json
from traffic_database import get_latest_traffic_sum
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", default="defaultkey")

# Read coordinates from the JSON file
json_filename = 'coordinates.json'
json_filepath = os.path.join(os.path.abspath(os.path.dirname(__file__)), json_filename)
with open(json_filepath) as file:
    coordinates_data = json.load(file)

@app.route('/')
def home():
    # Fetch the latest traffic data from the database
    traffic_data = get_latest_traffic_sum(7)
    return render_template('map.html', coordinates_data=coordinates_data, traffic_data=traffic_data)

@app.route('/get_coordinates_data')
def get_coordinates_data():
    return jsonify(coordinates_data)

@app.route('/get_traffic_data')
def get_traffic_data():
    # Fetch the latest traffic data from the database
    traffic_data = get_latest_traffic_sum(7)
    return jsonify(traffic_data)

if __name__ == '__main__':
    # For local development, use the Flask development server
    app.run(debug=True)
else:
    gunicorn_options = "-b 0.0.0.0:5000 -w 4"
    os.system(f"gunicorn {gunicorn_options} main:app")
