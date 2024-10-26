
import threading
import time
from flask import Flask, jsonify, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import os
import requests
from datetime import datetime, timedelta
import logging
from sqlalchemy import text
import pytz
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)

# Configuration for SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:tejas@localhost/weather_monitoring'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = True
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv('EMAIL_USER')  # Add your email here or fetch from env variable
app.config['MAIL_PASSWORD'] = os.getenv('EMAIL_PASS')  # Add your email password here or fetch from env variable
app.config['MAIL_DEFAULT_SENDER'] = app.config['MAIL_USERNAME']

# Initialize SQLAlchemy with app
db = SQLAlchemy(app)

def get_ist_time():
    """Helper function to get current time in IST"""
    ist = pytz.timezone('Asia/Kolkata')
    return datetime.now(ist)

class WeatherSummary(db.Model):
    __tablename__ = 'weathersummaries'
    id = db.Column(db.Integer, primary_key=True)
    city = db.Column(db.String(50), nullable=False)  # Add city column
    date = db.Column(db.DateTime, default=get_ist_time)
    avg_temp = db.Column(db.Float, nullable=False)
    max_temp = db.Column(db.Float, nullable=False)
    min_temp = db.Column(db.Float, nullable=False)
    dominant_condition = db.Column(db.String(30), nullable=False)

    def __repr__(self):
        return f'<WeatherSummary {self.city} on {self.date}: {self.avg_temp}°C>'


class DailyWeather(db.Model):
    __tablename__ = 'daily_weather'
    date = db.Column(db.DateTime, primary_key=True, default=datetime.utcnow)
    city = db.Column(db.String(50), primary_key=True,nullable=False)
    average_temperature = db.Column(db.Float, nullable=False)
    max_temperature = db.Column(db.Float, nullable=False)
    min_temperature = db.Column(db.Float, nullable=False)
    dominant_weather_condition = db.Column(db.String(30), nullable=False)

    def __repr__(self):
        return f'<DailyWeather {self.date}: {self.average_temperature}°C>'
# Add this to your models
class AlertThreshold(db.Model):
    __tablename__ = 'alert_thresholds'
    id = db.Column(db.Integer, primary_key=True)
    city = db.Column(db.String(50), nullable=False)
    high_temp_threshold = db.Column(db.Float, nullable=False)
    low_temp_threshold = db.Column(db.Float, nullable=False)
    consecutive_triggers = db.Column(db.Integer, default=2)
    email_recipient = db.Column(db.String(120), nullable=False)
def fetch_weather_data(city):
    """Fetch weather data from OpenWeatherMap API for a given city."""
    API_KEY = os.getenv('OPENWEATHER_API_KEY')
    if not API_KEY:
        logger.error("No API key found in environment variables")
        return None

    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric"
    logger.debug(f"Fetching weather data from: {url}")
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        logger.debug(f"Received weather data: {data}")
        return data
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching weather data: {str(e)}")
        return None
    

def send_alert_email(subject, to_email, body):
    from_email = yourmail@gmail.com"  # Your full Gmail address
    app_password = "your 16 character app_password "     # Use your App Password here

    # Create the message
    msg = MIMEMultipart()
    
    # Encode subject if it contains non-ASCII characters
    msg['Subject'] = subject.encode('utf-8').decode('utf-8')
    msg['From'] = from_email
    msg['To'] = to_email

    # Create text part with explicit UTF-8 encoding
    text_part = MIMEText(body, 'plain', 'utf-8')
    msg.attach(text_part)

    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(from_email, app_password)
            # Convert the entire message to string with proper encoding
            server.send_message(msg)
            logger.info("Alert email sent successfully")
    except Exception as e:
        logger.error(f"Failed to send alert email: {str(e)}")
        raise
class AlertTracker:
    def __init__(self):
        self.temperature_history = {}  # {city: [temp1, temp2, ...]}
        
    def check_temperature(self, city, temperature, threshold):
        if city not in self.temperature_history:
            self.temperature_history[city] = []
            
        history = self.temperature_history[city]
        history.append(temperature)
        
        # Keep only the last N readings where N is consecutive_triggers
        if len(history) > threshold.consecutive_triggers:
            history.pop(0)
            
        # Check if we have enough consecutive readings above/below threshold
        if len(history) == threshold.consecutive_triggers:
            if all(t >= threshold.high_temp_threshold for t in history):
                return 'high', history
            if all(t <= threshold.low_temp_threshold for t in history):
                return 'low', history
        return None, history

alert_tracker = AlertTracker()

def check_for_alerts(weather_data):
    """Enhanced alert checking function"""
    try:
        city = weather_data['name']
        current_temp = weather_data['main']['temp']
        weather_condition = weather_data['weather'][0]['main']
        
        # Get thresholds for this city
        thresholds = AlertThreshold.query.filter_by(city=city).all()
        
        for threshold in thresholds:
            # Check temperature thresholds
            alert_type, history = alert_tracker.check_temperature(
                city, current_temp, threshold
            )
            
            if alert_type:
                # Prepare alert message
                if alert_type == 'high':
                    subject = f"High Temperature Alert: {city}"
                    body = (f"Alert! Temperature in {city} has been above "
                           f"{threshold.high_temp_threshold}°C for "
                           f"{threshold.consecutive_triggers} consecutive readings.\n"
                           f"Temperature history: {', '.join(map(str, history))}°C")
                else:
                    subject = f"Low Temperature Alert: {city}"
                    body = (f"Alert! Temperature in {city} has been below "
                           f"{threshold.low_temp_threshold}°C for "
                           f"{threshold.consecutive_triggers} consecutive readings.\n"
                           f"Temperature history: {', '.join(map(str, history))}°C")
                
                # Send email alert
                send_alert_email(subject, threshold.email_recipient, body)
                
            # Check for extreme weather conditions
            extreme_conditions = ['Storm', 'Extreme', 'Tornado', 'Hurricane']
            if weather_condition in extreme_conditions:
                subject = f"Extreme Weather Alert: {city}"
                body = f"Alert! Extreme weather condition ({weather_condition}) detected in {city}."
                send_alert_email(subject, threshold.email_recipient, body)
                
    except Exception as e:
        logger.error(f"Error in check_for_alerts: {str(e)}")

def store_weather_data(weather_data, city):
    """Store the fetched weather data in the database."""
    try:
        if not all(key in weather_data['main'] for key in ['temp', 'temp_max', 'temp_min']):
            logger.error("Missing required temperature data in weather_data")
            return False

        if not weather_data.get('weather'):
            logger.error("Missing weather condition data")
            return False

        ist_time = get_ist_time()

        summary = WeatherSummary(
            city=city,  # Add the city name here
            date=ist_time,
            avg_temp=weather_data['main']['temp'],
            max_temp=weather_data['main']['temp_max'],
            min_temp=weather_data['main']['temp_min'],
            dominant_condition=weather_data['weather'][0]['main']
        )

        logger.debug(f"Attempting to store weather summary for {city}: {summary}")

        db.session.add(summary)
        db.session.commit()
        check_for_alerts(weather_data)
        logger.info(f"Weather data for {city} stored successfully!")
        return True
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error storing weather data for {city}: {str(e)}")
        return False


def fetch_weather_for_all_cities():
    """Continuously fetch weather data for all cities at the specified interval."""
    cities = ["Delhi", "Mumbai", "Chennai", "Bangalore", "Kolkata", "Hyderabad"]
    interval = 300  # 5 minutes

    with app.app_context():
        while True:
            logger.info("Fetching weather data for all cities...")
            for city in cities:
                weather_data = fetch_weather_data(city)
                if weather_data:
                    store_weather_data(weather_data, city)  # Pass city name here
                else:
                    logger.error(f"Failed to fetch weather data for {city}.")
            logger.info(f"Waiting for {interval} seconds before the next fetch...")
            time.sleep(interval)

def calculate_daily_aggregate():
    """Calculate daily rollup for average, max, min temperatures, and dominant weather condition for each city."""
    try:
        today = get_ist_time().date()  # Get current date in IST
        # Get unique cities from WeatherSummary
        cities = WeatherSummary.query.with_entities(WeatherSummary.city).distinct().all()  
        
        for city in cities:
            city_name = city[0]  # Extract city name
            
            # Query daily weather entries for the specific city
            daily_entries = WeatherSummary.query.filter(
                db.func.date(WeatherSummary.date) == today,
                WeatherSummary.city == city_name
            ).all()

            if not daily_entries:
                logger.info(f"No weather data available for {today} in {city_name}.")
                continue  # Skip to the next city

            # Calculate aggregates
            avg_temp = sum(entry.avg_temp for entry in daily_entries) / len(daily_entries)
            max_temp = max(entry.max_temp for entry in daily_entries)
            min_temp = min(entry.min_temp for entry in daily_entries)

            # Count dominant weather condition
            condition_count = {}
            for entry in daily_entries:
                condition = entry.dominant_condition
                condition_count[condition] = condition_count.get(condition, 0) + 1
            
            # Determine the dominant weather condition
            dominant_condition = max(condition_count, key=condition_count.get)

            # Check if an entry for today and the specific city already exists
            existing_entry = DailyWeather.query.filter(
                db.func.date(DailyWeather.date) == today,
                DailyWeather.city == city_name
            ).first()

            if existing_entry:
                # Update existing entry
                existing_entry.average_temperature = avg_temp
                existing_entry.max_temperature = max_temp
                existing_entry.min_temperature = min_temp
                existing_entry.dominant_weather_condition = dominant_condition
            else:
                # Create a new daily summary entry
                daily_summary = DailyWeather(
                    date=datetime.combine(today, datetime.min.time()),
                    city=city_name,  # Include city
                    average_temperature=avg_temp,
                    max_temperature=max_temp,
                    min_temperature=min_temp,
                    dominant_weather_condition=dominant_condition
                )
                db.session.add(daily_summary)

        db.session.commit()  # Commit the session after processing all cities
        logger.info(f"Daily weather summaries stored for {today}.")
        return True

    except Exception as e:
        db.session.rollback()  # Rollback the session on error
        logger.error(f"Error in calculating daily aggregate: {str(e)}")
        return False
         


def run_daily_aggregation():
    """Function to run daily aggregation periodically"""
    with app.app_context():
        while True:
            current_time = get_ist_time()
            
            if current_time.hour ==  8 and current_time.minute == 6:
                logger.info("Running daily aggregation...")
                calculate_daily_aggregate()
                time.sleep(10)  # 55 minutes
            else:
                time.sleep(30)  # Check again in 30 seconds

def start_background_threads():
    """Start all background threads"""
    weather_thread = threading.Thread(target=fetch_weather_for_all_cities)
    weather_thread.daemon = True
    weather_thread.start()
    
    aggregation_thread = threading.Thread(target=run_daily_aggregation)
    aggregation_thread.daemon = True
    aggregation_thread.start()



@app.route('/weather/<city>', methods=['GET'])
def get_weather(city):
    try:
        logger.info(f"Received weather request for city: {city}")
        
        weather_data = fetch_weather_data(city)
        if not weather_data:
            return jsonify({"error": "Failed to fetch weather data"}), 500

        # Pass city to store_weather_data function
        if store_weather_data(weather_data, city):
            weather_data['timestamp_ist'] = get_ist_time().strftime('%Y-%m-%d %H:%M:%S %Z')
            return jsonify({
                "message": "Weather data fetched and stored successfully",
                "data": weather_data
            })
        else:
            return jsonify({"error": "Failed to store weather data"}), 500

    except Exception as e:
        logger.error(f"Unexpected error in get_weather: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/verify_db', methods=['GET'])
def verify_db():
    try:
        db.session.execute(text('SELECT 1'))
        
        try:
            recent_entries = WeatherSummary.query.order_by(WeatherSummary.date.desc()).limit(5).all()
            entries_data = [
                {
                    "date": entry.date.strftime('%Y-%m-%d %H:%M:%S %Z'),
                    "avg_temp": entry.avg_temp,
                    "dominant_condition": entry.dominant_condition
                } for entry in recent_entries
            ]
            
            return jsonify({
                "status": "Database connection successful",
                "current_time_ist": get_ist_time().strftime('%Y-%m-%d %H:%M:%S %Z'),
                "table_exists": True,
                "recent_entries": entries_data
            })
            
        except Exception as table_error:
            logger.error(f"Error querying weather summaries: {str(table_error)}")
            return jsonify({
                "status": "Database connection successful",
                "current_time_ist": get_ist_time().strftime('%Y-%m-%d %H:%M:%S %Z'),
                "table_exists": False,
                "error": "Could not query weather summaries table."
            })
            
    except Exception as e:
        logger.error(f"Database verification failed: {str(e)}")
        return jsonify({
            "status": "Database connection failed",
            "error": str(e)
        }), 500

@app.route('/weather', methods=['GET'])
def get_weath():
    city = request.args.get('city')
    if city:
        return redirect(url_for('get_weather', city=city))
    return redirect(url_for('dashboard'))

@app.route('/')
def dashboard():
    cities = ["Mumbai", "Chennai", "Bangalore", "Kolkata", "Hyderabad", "Delhi"]
    return render_template('index5.html', cities=cities)


@app.route('/daily_report/<city>', methods=['GET'])
def get_daily_report(city):
    try:
        today = get_ist_time().date()
        daily_report = DailyWeather.query.filter(
            db.func.date(DailyWeather.date) == today,
            DailyWeather.city == city
        ).first()
        
        if daily_report:
            return jsonify({
                "success": True,
                "data": {
                    "city": city,
                    "date": today.strftime('%Y-%m-%d'),
                    "average_temperature": round(daily_report.average_temperature, 2),
                    "max_temperature": round(daily_report.max_temperature, 2),
                    "min_temperature": round(daily_report.min_temperature, 2),
                    "dominant_weather_condition": daily_report.dominant_weather_condition
                }
            })
        else:
            return jsonify({
                "success": False,
                "error": f"No daily report available for {city} on {today}"
            }), 404
            
    except Exception as e:
        logger.error(f"Error fetching daily report: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Failed to fetch daily report"
        }), 500

@app.route('/manage-alerts')
def manage_alerts():
    return render_template('alert_thresholds.html', cities=["Delhi", "Mumbai", "Chennai", "Bangalore", "Kolkata", "Hyderabad"])
@app.route('/alert-thresholds', methods=['GET', 'POST'])
def manage_alert_thresholds():
    if request.method == 'POST':
        try:
            data = request.json
            threshold = AlertThreshold(
                city=data['city'],
                high_temp_threshold=float(data['high_temp_threshold']),
                low_temp_threshold=float(data['low_temp_threshold']),
                consecutive_triggers=int(data['consecutive_triggers']),
                email_recipient=data['email_recipient']
            )
            db.session.add(threshold)
            db.session.commit()
            return jsonify({"message": "Alert threshold created successfully"})
        except Exception as e:
            return jsonify({"error": str(e)}), 400
    
    # GET method - fetch all thresholds
    thresholds = AlertThreshold.query.all()
    return jsonify([{
        'id': t.id,
        'city': t.city,
        'high_temp_threshold': t.high_temp_threshold,
        'low_temp_threshold': t.low_temp_threshold,
        'consecutive_triggers': t.consecutive_triggers,
        'email_recipient': t.email_recipient
    } for t in thresholds])


# Initialize application
if __name__ == '__main__':
    with app.app_context():
        try:
            db.create_all()
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Error creating database tables: {str(e)}")
        
        # Start both background threads
        start_background_threads()
    
    app.run(debug=True, port=5000)
