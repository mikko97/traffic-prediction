from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import requests
import traceback
import logging
import os
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(filename='/tmp/script_log.txt', level=logging.DEBUG)

# Load environment variables from a .env file
load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URI')

# Create the db object before the TrafficData class
db = SQLAlchemy(app)

# Define the TrafficData table outside of the conditional block
class TrafficData(db.Model):
    __tablename__ = 'trafficdata'
    id = db.Column(db.Integer, primary_key=True)
    device = db.Column(db.String(50))
    detector = db.Column(db.String(50))
    traffic_amount = db.Column(db.Integer)
    reliab_value = db.Column(db.Float)
    timestamp = db.Column(db.DateTime)

try:
    with app.app_context():
        db.create_all()

except Exception as create_db_error:
    logging.error(f"Failed to create the database: {create_db_error}")

def collect_and_store_data():
    with app.app_context():
        devices_to_fetch = ["tre216", "tre209", "tre212", "tre134", "tre148", "tre144", "tre133", "tre132", "tre124",
                            "tre101", "tre115", "tre103", "tre158", "tre227", "tre112_114", "tre117_575", "tre120_159",
                            "tre121", "tre123", "tre127", "tre150"]
        end_time = datetime.now()
        start_time = end_time - timedelta(minutes=1)

        try:
            for single_device in devices_to_fetch:
                api_url = f"http://trafficlights.tampere.fi/api/v1/trafficAmount/{single_device}?startTime={start_time.isoformat()}&endTime={end_time.isoformat()}"
                headers = {'User-Agent': 'traffic-app/1.0'}

                try:
                    response = requests.get(api_url, headers=headers)
                    response.raise_for_status()
                    api_data = response.json()

                    for result in api_data.get("results", []):
                        timestamp_iso = result.get("tsPeriodEnd")
                        timestamp = datetime.fromisoformat(timestamp_iso)

                        data_to_save = TrafficData(
                            device=single_device,
                            detector=result.get("detector"),
                            traffic_amount=result.get("trafficAmount"),
                            reliab_value=result.get("reliabValue"),
                            timestamp=timestamp
                        )
                        db.session.add(data_to_save)

                    try:
                        db.session.commit()
                    except Exception as commit_error:
                        logging.error(f"Failed to commit changes: {commit_error}")

                except requests.exceptions.RequestException as e:
                    with open("/tmp/error_log.txt", "a") as error_file:
                        error_file.write(f"Failed to fetch data from the API: {e}\n")
                        traceback.print_exc(file=error_file)
                        logging.error('Error occurred during API request.')

        except Exception as outer_error:
            logging.error(f"An unexpected error occurred: {outer_error}")
            traceback.print_exc()
