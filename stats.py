from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from base import Base


class Stats(Base):
    """ Processing Statistics """
    __tablename__ = "stats"

    id = Column(Integer, primary_key=True)
    num_ride_readings = Column(Integer, nullable=False)
    max_speed_reading = Column(Integer, nullable=False)
    num_heartrate_readings = Column(Integer, nullable=True)
    max_heartrate_reading = Column(Integer, nullable=True)
    last_updated = Column(DateTime, nullable=False)

    def __init__(self, num_ride_readings, max_speed_reading,
        num_heartrate_readings, max_heartrate_reading,last_updated):
        """ Initializes a processing statistics object """

        self.num_ride_readings = num_ride_readings
        self.max_speed_reading = max_speed_reading
        self.num_heartrate_readings = num_heartrate_readings
        self.max_heartrate_reading = max_heartrate_reading
        self.last_updated = last_updated

    def to_dict(self):
        """ Dictionary Representation of a statistics """
        dict = {}
        dict['num_ride_readings'] = self.num_ride_readings
        dict['max_speed_reading'] = self.max_speed_reading
        dict['num_heartrate_readings'] = self.num_heartrate_readings
        dict['max_heartrate_reading'] = self.max_heartrate_reading
        

        dict['last_updated'] = self.last_updated.strftime("%Y-%m-%dT%H:%M:%SZ")

        return dict