import os
from sqlalchemy import create_engine, Column, Integer, Float, String, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
import pytz

print("Starting database initialization...")

# Get database URL from environment variable
DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    raise ValueError("No DATABASE_URL environment variable set")

# Convert postgres:// to postgresql://
if DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

print(f"Using database URL: {DATABASE_URL.split('@')[0]}@******")

# Create an engine
engine = create_engine(DATABASE_URL)

# Create a base class for declarative models
Base = declarative_base()

def get_ist_time():
    """Helper function to get current time in IST"""
    ist = pytz.timezone('Asia/Kolkata')
    return datetime.now(ist)

# Define your models
class WeatherSummary(Base):
    __tablename__ = "weathersummaries"
    id = Column(Integer, primary_key=True)
    city = Column(String(50), nullable=False)
    date = Column(DateTime, default=get_ist_time)
    avg_temp = Column(Float, nullable=False)
    max_temp = Column(Float, nullable=False)
    min_temp = Column(Float, nullable=False)
    dominant_condition = Column(String(50), nullable=False)

class DailyWeather(Base):
    __tablename__ = 'daily_weather'
    date = Column(DateTime, primary_key=True, default=get_ist_time)
    city = Column(String(50), primary_key=True, nullable=False)
    average_temperature = Column(Float, nullable=False)
    max_temperature = Column(Float, nullable=False)
    min_temperature = Column(Float, nullable=False)
    dominant_weather_condition = Column(String(30), nullable=False)

class AlertThreshold(Base):
    __tablename__ = 'alert_thresholds'
    id = Column(Integer, primary_key=True)
    city = Column(String(50), nullable=False)
    high_temp_threshold = Column(Float, nullable=False)
    low_temp_threshold = Column(Float, nullable=False)
    consecutive_triggers = Column(Integer, default=2)
    email_recipient = Column(String(120), nullable=False)

def init_db():
    """Initialize the database"""
    print("Creating database tables...")
    Base.metadata.create_all(engine)
    print("Database tables created successfully!")

if __name__ == "__main__":
    init_db()