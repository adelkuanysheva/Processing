import re
import swagger_ui_bundle
import connexion
from connexion import NoContent
import json
import datetime 
import requests
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import yaml
import logging
import logger
import logging.config
import uuid
from base import Base
from stats import Stats
import os
from apscheduler.schedulers.background import BackgroundScheduler
from flask_cors import CORS, cross_origin
import os 
import sqlite3




if "TARGET_ENV" in os.environ and os.environ["TARGET_ENV"] == "test":
    print("In Test Environment")
    app_conf_file = "/config/app_conf.yml"
    log_conf_file = "/config/log_conf.yml"
else:
    print("In Dev Environment")
    app_conf_file = "app_conf.yml"
    log_conf_file = "log_conf.yml"

logger = logging.getLogger('basicLogger')

with open(app_conf_file, 'r') as f:
    app_config = yaml.safe_load(f.read())

with open(log_conf_file, 'r') as f:
    log_config = yaml.safe_load(f.read())
    logging.config.dictConfig(log_config)

logger.info("App Conf File: %s" % app_conf_file)
logger.info("Log Conf File: %s" % log_conf_file)

DATABASE = app_config['datastore']['filename']
DB_ENGINE = create_engine(f"sqlite:///{DATABASE}")
Base.metadata.bind = DB_ENGINE
DB_SESSION = sessionmaker(bind=DB_ENGINE)


def populate_stats():
    """ Periodically update stats """

    logger.info('Start Periodic Processing')

    current_time = datetime.datetime.now()   
    current_time_str = current_time.strftime("%Y-%m-%dT%H:%M:%SZ")
    print("Current time: " + current_time_str)

    if os.path.exists(DATABASE):
        session = DB_SESSION()
        results = session.query(Stats).order_by(Stats.last_updated.desc()).first()
    else: 
        results = Stats(50000, 20, 10000, 100, datetime.datetime(2022, 10, 13, 1, 2, 3))
    num_r = int(results.num_ride_readings)
    num_h = int(results.num_heartrate_readings)
    last_updated = results.last_updated.strftime("%Y-%m-%dT%H:%M:%SZ")
    logger.info("Last Updated on: " + last_updated)
    print(last_updated)
    
    # Ride GET request
    req_ride = requests.get(app_config['eventstore1']['url'] + '?start_timestamp=' + last_updated + "&end_timestamp=" + current_time_str, 
                                    headers={'Content-Type': 'application/json'})
    

    if req_ride.status_code != 200:
        logger.error("Request has failed!")

    ride_data = req_ride.json()
    logger.info(f"Request: {ride_data}")
    print(ride_data)
    ride_len = len(ride_data)
    print(ride_len)
    ride_newlen = ride_len + num_r

    # print the events and find average speed
    ride_max = int(results.max_speed_reading)
    for event in ride_data:
        logger.debug(("Event processed: ", event))
        if int(event["avg_speed"]) > ride_max:
            ride_max = event["avg_speed"]


    ride_oldlenstr = str(ride_len)
    ride_lenstr = str(ride_newlen)
    
    logger.info('Number of ride data events received: ' + ride_oldlenstr)
    logger.debug(ride_data)  
    # Heartrate GET request
    req_heartrate = requests.get(app_config['eventstore2']['url'] + '?start_timestamp=' + last_updated + "&end_timestamp=" + current_time_str, 
                                    headers={'Content-Type': 'application/json'})

    if req_heartrate.status_code != 200:
        logger.error("Request has failed!")

    hr_data = req_heartrate.json()
    print(hr_data)
    hr_len = len(hr_data)
    hr_newlen = hr_len + num_h

    hr_max = int(results.max_heartrate_reading)
    for event in hr_data:
        logger.debug(("Event processed: " , event))
        if int(event["heart_rate"]) > hr_max:
            hr_max = event["heart_rate"]

    heartrate_oldlenstr = str(hr_len)
    heartrate_lenstr = str(hr_newlen)
    
    logger.info('Number of heartrate data events received: ' + heartrate_oldlenstr)
    logger.debug(ride_data)  

    stats = Stats(num_r,
                  ride_max,
                  num_h,
                  hr_max,
                  current_time) 

    logger.debug('''New statistics:\n Number of Ride Readings: %s\n Number of HR Readings %s\n Max Speed Reading %s\n Max HR Reading %s''' 
                    % (num_r, num_h, ride_max, hr_max))

    session.add(stats)
    session.commit()
    session.close()



def get_stats():
    """ Receives statistics data event"""
    
    session = DB_SESSION()
    logger.info('')
    logger.info('Statistics request started.')
    
    results = session.query(Stats).order_by(Stats.last_updated.desc())
    print(results)
    session.close()

    if len(results.all()) > 0:
        result_dict = results[0].to_dict()
    else:
        return "Statistics is empty"

    logger.debug(f"The last updated statistics are:\n{result_dict}\n")
    logger.info("Statistics request completed.")

    return result_dict, 200


def init_scheduler():
    sched = BackgroundScheduler(daemon=True)
    sched.add_job(populate_stats,'interval', seconds=app_config['scheduler']['period_sec'])
    sched.start()



def health():
    logger.info("Health Check returned 200")
    return 200


app = connexion.FlaskApp(__name__, specification_dir='')
CORS(app.app)
app.app.config['CORS_HEADERS'] = 'Content-Type'
app.add_api("openapi.yml", strict_validation=True, validate_responses=True)


if not os.path.isfile(DATABASE):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('''
            CREATE TABLE stats
            (id INTEGER PRIMARY KEY ASC,
            num_ride_readings INTEGER NOT NULL,
            max_speed_reading INTEGER NOT NULL,
            num_heartrate_readings INTEGER,
            max_heartrate_reading INTEGER,
            last_updated VARCHAR(100) NOT NULL)
            ''')
    conn.commit()
    conn.close()
    logger.info("Database created.")

if __name__ == "__main__":
    init_scheduler()
    app.run(port=8100, use_reloader=False)
