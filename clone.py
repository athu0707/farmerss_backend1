from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from database import get_user_by_username, verify_user, register_user, User, get_db_connection
import requests
import os
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')  # Use the secret key from .env

# Verify that the API key is loaded
print("OpenWeatherMap API Key:", os.getenv("OPENWEATHERMAP_API_KEY"))
# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    conn.close()
    if user:
        return User(id=user['id'], username=user['username'], role=user['role'])
    return None

# Function to fetch weather data
def get_weather(city):
    API_KEY = os.getenv("OPENWEATHERMAP_API_KEY")  # Get API key from .env
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric"
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for HTTP errors
        data = response.json()
        return data
    except requests.exceptions.RequestException as e:
        print(f"Error fetching weather data: {e}")
        return None

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = verify_user(username, password)
        if user:
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('predict'))  # Redirect to the prediction page after login
        else:
            flash('Invalid username or password', 'error')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        role = request.form.get('role')
        if get_user_by_username(username):
            flash('Username already exists', 'error')
        else:
            register_user(username, password, role)
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', user=current_user)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('index'))


import requests
def get_crop_price(crop_name, state="Maharashtra", district="Pune"):
    API_KEY = os.getenv("CROP_MARKET_PRICE_API_KEY")
    if not API_KEY:
        print("Error: AGMARKNET_API_KEY is not set in .env file.")
        return None

    # Agmarknet API endpoint
    url = f"https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070"
    params = {
        "api-key": API_KEY,
        "format": "json",
        "filters[state]": state,
        "filters[district]": district,
        "filters[commodity]": crop_name,
        "limit": 1  # Fetch only the latest price
    }

    try:
        response = requests.get(url, params=params)
        print("API URL:", response.url)  # Debug statement
        print("API Response:", response.status_code, response.text)  # Debug statement
        response.raise_for_status()
        data = response.json()
        
        # Check if records are available
        if data.get("total", 0) > 0 and data.get("records"):
            return data['records'][0]['modal_price']  # Return the modal price
        else:
            print("No records found for the given filters.")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Error fetching crop price data: {e}")
        return None

@app.route('/predict', methods=['GET', 'POST'])
@login_required
def predict():
    if request.method == 'POST':
        crop_name = request.form.get('crop_name')

        # Fetch weather data
        weather_data = get_weather("Ahmednagar")
        if weather_data:
            weather_description = weather_data['weather'][0]['description']
            temperature = weather_data['main']['temp']
            humidity = weather_data['main']['humidity']
        else:
            weather_description = "Weather data unavailable"
            temperature = "N/A"
            humidity = "N/A"

        # Fetch crop market price data
        crop_price = get_crop_price(crop_name)
        if crop_price is None:
            crop_price = "Crop price data unavailable"

        # Predict crop price and demand
        predicted_price = predict_crop_price(crop_name)
        predicted_demand = predict_market_demand(crop_name)

        # Fetch transportation and storage data
        routes = fetch_transportation_routes()
        storage = fetch_storage_recommendations()

        return render_template('results.html',
                              crop_name=crop_name,
                              predicted_price=predicted_price,
                              predicted_demand=predicted_demand,
                              routes=routes,
                              storage=storage,
                              weather_description=weather_description,
                              temperature=temperature,
                              humidity=humidity,
                              crop_price=crop_price)
    return render_template('predict.html')
    

# Helper functions (replace with your actual implementations)
def predict_crop_price(crop_name):
    # Dummy implementation
    return 100.0

def predict_market_demand(crop_name):
    # Dummy implementation
    return 500.0

def fetch_transportation_routes():
    # Dummy implementation
    return [("Farm A", "Market X", 50, 100)]

def fetch_storage_recommendations():
    # Dummy implementation
    return [("Wheat", "Silo")]

if __name__ == '__main__':
    app.run(debug=True)

print("Secret Key:", app.secret_key)




def get_weather(city):
    API_KEY = os.getenv("OPENWEATHERMAP_API_KEY")  # Get API key from .env
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric"
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for HTTP errors
        data = response.json()
        return data
    except requests.exceptions.RequestException as e:
        print(f"Error fetching weather data: {e}")
        return None

def get_weather(city):
    API_KEY = os.getenv("OPENWEATHERMAP_API_KEY")
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric"
    try:
        response = requests.get(url)
        print("API Response:", response.status_code, response.text)  # Debug statement
        response.raise_for_status()
        data = response.json()
        return data
    except requests.exceptions.RequestException as e:
        print(f"Error fetching weather data: {e}")
        return None



print("Fetching crop price data...")
crop_price_data = get_crop_price(crop_name)
print("Crop price data:", crop_price_data)

import requests

API_KEY = "your_agmarknet_api_key"
url = "https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070"
params = {
    "api-key": API_KEY,
    "format": "json",
    "filters[state]": "Maharashtra",
    "filters[district]": "Ahmednagar",
    "filters[commodity]": "Rice",
    "limit": 1
}

response = requests.get(url, params=params)
if response.status_code == 200:
    data = response.json()
    print("API Response:", data)
else:
    print("Error:", response.status_code, response.text)