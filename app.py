from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from database import get_user_by_username, verify_user, register_user, User, get_db_connection
import requests
from bs4 import BeautifulSoup
import os
from dotenv import load_dotenv
from datetime import datetime
from model import predict_crop_price

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dev_secret_key')

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


# ----------------- PIB Farmer News Function -----------------
def get_farmer_news():
    url = "https://pib.gov.in/PressReleasePage.aspx"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"PIB News Fetch Error: {e}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    news_list = []

    # Try multiple selectors for safety
    selectors = [
        "ul.pressRelease li a",
        ".prlink a",
        "div#pressReleaseDiv li a"
    ]

    for selector in selectors:
        for tag in soup.select(selector):
            title = tag.get_text(strip=True)
            link = tag.get("href", "")
            if not link.startswith("http"):
                link = "https://pib.gov.in/" + link

            if "farmer" in title.lower() or "agriculture" in title.lower():
                news_list.append({"title": title, "link": link})

            if len(news_list) >= 5:
                break
        if news_list:
            break

    return news_list
# ------------------------------------------------------------


def get_weather(city):
    """Fetch weather data from OpenWeatherMap"""
    API_KEY = os.getenv("OPENWEATHERMAP_API_KEY")
    if not API_KEY:
        return None
        
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Weather API Error: {e}")
        return None


def get_crop_price(crop_name, state="haryana", district="gurgaon"):
    """Fetch crop price data from AGMARKNET"""
    API_KEY = os.getenv("AGMARKNET_API_KEY")
    if not API_KEY:
        return None, None, None

    url = "https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070"
    params = {
        "api-key": API_KEY,
        "format": "json",
        "filters[state]": state,
        "filters[district]": district,
        "filters[Commodity]": crop_name,
        "limit": 1
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        if data.get("total", 0) > 0 and data.get("records"):
            record = data['records'][0]
            min_price = float(record.get('min_price', 0)) / 100
            max_price = float(record.get('max_price', 0)) / 100
            modal_price = float(record.get('modal_price', 0)) / 100
            return min_price, max_price, modal_price
            
        return None, None, None
    except Exception as e:
        print(f"Price API Error: {e}")
        return None, None, None


# ------------------- ROUTES -------------------

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = verify_user(username, password)
        if user:
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        flash('Invalid username or password', 'error')
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form.get('role', 'farmer')  # Default role
        
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
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM crops WHERE user_id = %s", (current_user.id,))
    active_crop_count = cursor.fetchone()[0]
    conn.close()

    current_date = datetime.now().strftime("%B %d, %Y")

    # Get PIB Farmer News
    farm_news = get_farmer_news()
    

    return render_template('dashboard.html', 
                         user=current_user,
                         current_date=current_date,
                         active_crop_count=active_crop_count,
                         farm_news=farm_news)
    farm_news = [
        {"title": "Govt launches new crop insurance scheme", "link": "#"},
        {"title": "New subsidies announced for organic farming", "link": "#"},
        {"title": "Farmer training programs to start next month", "link": "#"},
    ]



@app.route('/predict', methods=['GET', 'POST'])
@login_required
def predict():
    if request.method == 'POST':
        crop_name = request.form['crop_name']
        city = request.form.get('city', 'Ahmednagar')

        weather_data = get_weather(city)
        weather_info = {
            'description': weather_data['weather'][0]['description'] if weather_data else 'N/A',
            'temperature': weather_data['main']['temp'] if weather_data else 'N/A',
            'humidity': weather_data['main']['humidity'] if weather_data else 'N/A'
        }

        min_price, max_price, modal_price = get_crop_price(crop_name)

        predicted_price = predict_crop_price(crop_name)
        predicted_demand = None  # Placeholder

        return render_template('results.html',
            crop_name=crop_name,
            predicted_price=predicted_price or "N/A",
            predicted_demand=predicted_demand or "N/A",
            weather=weather_info,
            min_price=min_price or "N/A",
            max_price=max_price or "N/A",
            modal_price=modal_price or "N/A",
            routes=[("Farm A", "Market X", 50, 100)],
            storage=[("Wheat", "Silo")]
        )

    return render_template('predict.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)



    app.run(debug=True)
