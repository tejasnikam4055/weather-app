# Weather Monitoring Application

A robust Flask-based weather monitoring system that tracks weather conditions across multiple Indian cities, provides daily summaries, and sends email alerts for extreme weather conditions.

## Features

- **Real-time Weather Monitoring**: Tracks weather data for major Indian cities (Delhi, Mumbai, Chennai, Bangalore, Kolkata, Hyderabad)
- **Automated Data Collection**: Fetches weather data every 5 minutes using OpenWeatherMap API
- **Daily Weather Summaries**: Generates daily aggregated reports including:
  - Average temperature
  - Maximum temperature
  - Minimum temperature
  - Dominant weather condition
- **Alert System**: 
  - Configurable temperature thresholds for each city
  - Email notifications for extreme weather conditions
  - Consecutive trigger monitoring
  - Customizable alert recipients
- **Web Interface**:
  - Dashboard for real-time weather monitoring
  - Alert management interface
  - Daily weather reports

## Technologies Used

- **Backend**: Python, Flask
- **Database**: MySQL
- **ORM**: SQLAlchemy
- **External APIs**: OpenWeatherMap API
- **Email Service**: SMTP (Gmail)
- **Additional Libraries**:
  - `pytz` for timezone handling
  - `requests` for API calls
  - `threading` for background tasks

## Prerequisites

- Python 3.x
- MySQL Server
- OpenWeatherMap API key
- Gmail account (for sending alerts)

## Installation

1. Clone the repository:
```bash
git clone [your-repository-url]
cd weather-app
```

2. Install required packages:
```bash
pip install -r requirements.txt
```

3. Set up the MySQL database:
```sql
CREATE DATABASE weather_monitoring;
```

4. Configure environment variables:
```bash
export OPENWEATHER_API_KEY='your_api_key'
export EMAIL_USER='your_gmail_address'
export EMAIL_PASS='your_app_password'
```

5. Run the database initialization script:
```bash
python database_setup.py
```

## Configuration

### Database Configuration
Update the database connection string in both main application and database setup files:
```python
DATABASE_URI = "mysql+mysqlconnector://username:password@localhost/weather_monitoring"
```

### Email Configuration
Update the email configuration in the main application:
```python
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
```

## Email Alert Setup

### Gmail Configuration

1. **Gmail Account Setup**:
   - You need a Gmail account to send weather alerts
   - Replace `from_email` in the code with your Gmail address:
     ```python
     from_email = "your.email@gmail.com"
     ```

2. **Generate App Password**:
   - Google requires an App Password for sending emails through scripts
   - To generate an App Password:
     1. Go to your Google Account settings (https://myaccount.google.com)
     2. Navigate to Security
     3. Enable 2-Step Verification if not already enabled
     4. Go to App passwords (under 2-Step Verification)
     5. Select 'Mail' and your device
     6. Click Generate
     7. Google will provide a 16-character password

3. **Configure App Password**:
   - Replace the existing app_password in the code with your generated password:
     ```python
     app_password = "your-16-character-app-password"
     ```
   - Keep this password secure and never share it
   - If compromised, you can revoke it from your Google Account settings

**Important Security Notes:**
- Never commit your real app password to version control
- Consider using environment variables for production:
  ```python
  app_password = os.getenv('EMAIL_APP_PASSWORD')
  ```
- Revoke and regenerate the app password if it's ever exposed

## Usage

1. Start the application:
```bash
python app.py
```

2. Access the web interface:
- Dashboard: `http://localhost:5000/`
- Manage Alerts: `http://localhost:5000/manage-alerts`

3. API Endpoints:
- Get weather for specific city: `GET /weather/<city>`
- Get daily report: `GET /daily_report/<city>`
- Verify database connection: `GET /verify_db`
- Manage alert thresholds: `GET/POST /alert-thresholds`

## Alert System Setup

1. Navigate to the alert management interface
2. Configure thresholds for each city:
   - High temperature threshold
   - Low temperature threshold
   - Number of consecutive triggers
   - Email recipient

## Data Models

### WeatherSummary
- Stores real-time weather data
- Fields: city, date, avg_temp, max_temp, min_temp, dominant_condition

### DailyWeather
- Stores daily aggregated weather data
- Fields: date, city, average_temperature, max_temperature, min_temperature, dominant_weather_condition

### AlertThreshold
- Stores alert configuration
- Fields: city, high_temp_threshold, low_temp_threshold, consecutive_triggers, email_recipient

## Background Tasks

The application runs two background threads:
1. Weather data collection (every 5 minutes)
2. Daily aggregation (runs at 8:06 AM IST)

## OpenWeatherMap API Setup

1. Sign up for a free account at OpenWeatherMap: https://openweathermap.org/api
2. Get your API key from your account dashboard
3. Add the API key to your environment variables:
```bash
export OPENWEATHER_API_KEY='your_api_key'
```

## Database Schema

### Create necessary tables:
```sql
CREATE TABLE weathersummaries (
    id INT AUTO_INCREMENT PRIMARY KEY,
    city VARCHAR(50) NOT NULL,
    date DATETIME DEFAULT CURRENT_TIMESTAMP,
    avg_temp FLOAT NOT NULL,
    max_temp FLOAT NOT NULL,
    min_temp FLOAT NOT NULL,
    dominant_condition VARCHAR(30) NOT NULL
);

CREATE TABLE daily_weather (
    date DATETIME,
    city VARCHAR(50),
    average_temperature FLOAT NOT NULL,
    max_temperature FLOAT NOT NULL,
    min_temperature FLOAT NOT NULL,
    dominant_weather_condition VARCHAR(30) NOT NULL,
    PRIMARY KEY (date, city)
);

CREATE TABLE alert_thresholds (
    id INT AUTO_INCREMENT PRIMARY KEY,
    city VARCHAR(50) NOT NULL,
    high_temp_threshold FLOAT NOT NULL,
    low_temp_threshold FLOAT NOT NULL,
    consecutive_triggers INT DEFAULT 2,
    email_recipient VARCHAR(120) NOT NULL
);
```
## IMP
for getting daily report of each city you have to change 
def run_daily_aggregation():
    """Function to run daily aggregation periodically"""
    with app.app_context():
        while True:
            current_time = get_ist_time()
            if current_time.hour ==  11 and current_time.minute == 6:
                logger.info("Running daily aggregation...")
                calculate_daily_aggregate()
                time.sleep(10)  # 55 minutes
            else:
                time.sleep(30)  # Check again in 30 seconds
                
## current_time.hour as per your requirement to calculate daily report of each city 
## Troubleshooting

Common issues and solutions:

1. **Database Connection Issues**:
   - Verify MySQL server is running
   - Check database credentials
   - Ensure database exists

2. **Email Alert Issues**:
   - Verify Gmail app password is correct
   - Check 2-Step Verification is enabled
   - Ensure proper email configuration

3. **API Issues**:
   - Verify OpenWeatherMap API key is valid
   - Check API rate limits
   - Ensure internet connectivity

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- OpenWeatherMap API for providing weather data
- Flask community for the excellent web framework
- SQLAlchemy team for the ORM
