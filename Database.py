from sqlalchemy import create_engine, Column, Integer, Float, String, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime

# Database connection settings
DATABASE_URI = "mysql+mysqlconnector://root:tejas@localhost/weather_monitoring"

# Create an engine
engine = create_engine(DATABASE_URI)

# Create a base class for declarative models
Base = declarative_base()

# Define the WeatherMonitoring model
class WeatherMonitoring(Base):
    __tablename__ = "weathersummaries"

    id = Column(Integer, primary_key=True)
    city = Column(String(50), nullable=False)
    date = Column(DateTime, default=datetime.utcnow)
    avg_temp = Column(Float)
    max_temp = Column(Float)
    min_temp = Column(Float)
    dominant_condition = Column(String(50))  # VARCHAR with a maximum length of 50


class DailyWeather(Base):
    __tablename__ = 'daily_weather'
    date = Column(DateTime,primary_key=True, default=datetime.utcnow)
    average_temperature = Column(Float, nullable=False)
    max_temperature = Column(Float, nullable=False)
    min_temperature = Column(Float, nullable=False)
    dominant_weather_condition = Column(String(30), nullable=False)

    def __repr__(self):
        return f'<DailyWeather {self.date}: {self.average_temperature}°C>'
    

class AlertThreshold(Base):
    __tablename__ = 'alert_thresholds'
    id = Column(Integer, primary_key=True)
    city = Column(String(50), nullable=False)
    high_temp_threshold = Column(Float, nullable=False)
    low_temp_threshold = Column(Float, nullable=False)
    consecutive_triggers = Column(Integer, default=2)
    email_recipient = Column(String(120), nullable=False)


# Create all tables in the database
Base.metadata.create_all(engine)

# Create a new session
Session = sessionmaker(bind=engine)
session = Session()

# Close the session
session.close()
