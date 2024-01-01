from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from datetime import datetime, timedelta
import os
import logging
import pytz

logging.basicConfig(filename='error_log.txt', level=logging.ERROR)

app = Flask(__name__)
database_filename = 'traffic_db2.db'
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(os.path.abspath(os.path.dirname(__file__)), database_filename)}'
db = SQLAlchemy(app)

class TrafficData(db.Model):
    """
    Represents the TrafficData table in the database.

    Attributes:
        id (int): Primary key.
        device (str): Device identifier.
        detector (str): Detector identifier.
        traffic_amount (int): Amount of traffic.
        reliab_value (float): Reliability value.
        timestamp (datetime): Timestamp of the data.
    """
    __tablename__ = 'trafficdata'
    id = db.Column(db.Integer, primary_key=True)
    device = db.Column(db.String(50))
    detector = db.Column(db.String(50))
    traffic_amount = db.Column(db.Integer)
    reliab_value = db.Column(db.Float)
    timestamp = db.Column(db.DateTime)

detectors_to_include = {
                '216': ['c50', 'a90', 'b60'],
                '212': ['a20', 'b55'],
                '134': ['c50', 'b60_1', 'b60_2', 'a60_1', 'a60_2'],
                '133': ['b60_1', 'b60_2', 'f50', 'd50', 'c60', 'a60'],
                '132': ['b100_1', 'b100_2', 'c50', 'a60_1', 'a60_2'],
                '144': ['a60', 'd30', 'b60_1', 'b60_2', 'c25'],
                '103': ['a55', 'b55', 'c60_1', 'c60_2', 'd30', 'e55'],
                '227': ['a55_1', 'a55_2', 'b50', 'c45', 'e45', 'f55'],
                '112_114': ['a17_1', 'a17_2', 'b100_1', 'b100_2', 'e35'],
                '117_575': ['a100_1', 'a100_2', 'c45', 'j93_1', 'j93_2'],
                '120_159': ['a35_1', 'a35_2', 'j120_1', 'j120_2', 'd50', 'e50', 'm45', 'n45'],
                '121': ['a30', 'c30', 'b80', 'e50_1', 'e50_2', 'f50', 'g50'],
                '123': ['a100_1', 'a100_2', 'b100_1', 'b100_2', 'd60'],
                '127': ['a115_1', 'a115_2', 'b115', 'c75_1', 'c75_2', 'd65_1', 'd65_2', 'd65_3', 'd65_4', 'e100_1', 'e100_2', 'e100_3', 
                        'e100_4', 'g80'],
                '150': ['a100_1', 'a100_2', 'b120_1', 'b120_2', 'c110', 'd60']
            }
local_timezone = pytz.timezone('Europe/Helsinki')

def get_latest_traffic_sum(n):
    """
    Fetches the latest sum of traffic amounts for each device.

    Args:
        n (int): Number of recent timestamps to consider.

    Returns:
        dict: A dictionary containing traffic amounts aggregated by timestamp and device.
            Example:
            {
                '2023-01-01 12:00:00': {'device1': 100, 'device2': 150},
                '2023-01-01 11:50:00': {'device1': 80, 'device2': 120},
                ...
            }

    Raises:
        Exception: If an error occurs during the data retrieval process.
    """
    try:
        with app.app_context():
            # Calculate the timestamp cutoff for the last n timestamps
            cutoff_timestamp = datetime.now(local_timezone) - timedelta(minutes=n*10)

            latest_timestamp_subquery = db.session.query(
                TrafficData.device,
                TrafficData.detector,
                func.max(TrafficData.timestamp).label("max_timestamp")
            ).group_by(TrafficData.device).subquery()

            # Retrieve data from wanted devices
            rows_to_include = db.session.query(
                func.replace(latest_timestamp_subquery.c.device, 'tre', '').label("device"),
                TrafficData.traffic_amount.label("traffic_amount"),
                TrafficData.detector.label("detector"),
                TrafficData.timestamp.label("timestamp")
            ).join(
                latest_timestamp_subquery,
                (TrafficData.device == latest_timestamp_subquery.c.device)
            ).filter(
                func.replace(latest_timestamp_subquery.c.device, 'tre', '').in_(detectors_to_include.keys()),
                TrafficData.timestamp >= cutoff_timestamp
            ).order_by(TrafficData.timestamp.desc()).all()

            # Filter out rows with unwanted detectors
            filtered_rows = []
            for row in rows_to_include:
                if row.device in detectors_to_include.keys() and row.detector in detectors_to_include[row.device]:
                    filtered_rows.append(row)

            # Sum the traffic_amounts from filtered rows
            results_by_timestamp = {}
            for row in filtered_rows:
                timestamp_key = row.timestamp.strftime('%Y-%m-%d %H:%M:%S')
                if timestamp_key not in results_by_timestamp:
                    results_by_timestamp[timestamp_key] = {}
                if row.device not in results_by_timestamp[timestamp_key]:
                    results_by_timestamp[timestamp_key][row.device] = row.traffic_amount
                else:
                    results_by_timestamp[timestamp_key][row.device] += row.traffic_amount
                

    except Exception as e:
        logging.error(f"Error in get_latest_traffic_sum: {e}")
        raise

    return results_by_timestamp