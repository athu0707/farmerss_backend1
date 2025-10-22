import pandas as pd
from sklearn.ensemble import RandomForestRegressor
import joblib
import os
import logging
import numpy as np
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
MODEL_DIR = "ml_models"
DATA_FILE = "Ricedata.csv"





os.makedirs(MODEL_DIR, exist_ok=True)

def load_and_preprocess_data():
    """Load and preprocess the crop price data with proper date handling"""
    try:
        logger.info(f"Loading data from {DATA_FILE}")
        df = pd.read_csv(DATA_FILE)
        
        # Basic validation
        required_columns = {'Date', 'Commodity', 'Modal_Price'}
        if not required_columns.issubset(df.columns):
            missing = required_columns - set(df.columns)
            raise ValueError(f"CSV missing required columns: {missing}")
        
        # Convert and clean data
        df['date'] = pd.to_datetime(df['Date'], dayfirst=True)
        df['year'] = df['date'].dt.year
        df['month'] = df['date'].dt.month
        df['day'] = df['date'].dt.day
        df['price'] = pd.to_numeric(df['Modal_Price'], errors='coerce')
        df = df.dropna(subset=['price'])
        
        # Feature engineering
        df['price_moving_avg'] = df.groupby('Commodity')['price'].transform(
            lambda x: x.rolling(window=30, min_periods=1).mean()
        )
        
        logger.info(f"Data loaded successfully. {len(df)} records available.")
        logger.debug(f"Sample data:\n{df.head()}")
        return df
    
    except Exception as e:
        logger.error(f"Error loading data: {str(e)}")
        raise

df = load_and_preprocess_data()
print("Unique commodities in CSV:", df['Commodity'].unique())

print("👉 Commodity counts:")
for crop in df['Commodity'].unique():
    count = len(df[df['Commodity'] == crop])
    print(f"  - {crop}: {count} rows")



def train_price_model(crop_name, df):
    """Train and save a price prediction model for specific crop"""
    try:
        logger.info(f"Training price model for {crop_name}")
        crop_df = df[df['Commodity'] == crop_name].copy()
    
        if len(crop_df) < 30:
            logger.warning(f"Insufficient data for {crop_name} ({len(crop_df)} records)")
            return None
        
        # Prepare features
        features = ['year', 'month', 'day', 'price_moving_avg']
        X = crop_df[features]
        y = crop_df['price']
        
        # Train model
        model = RandomForestRegressor(n_estimators=100, random_state=42)
        model.fit(X, y)
        
        # Save model
        model_path = os.path.join(MODEL_DIR, f"{crop_name}_price_model.joblib")
        joblib.dump(model, model_path)
        logger.info(f"Model saved to {model_path}")
        return model_path
        
    except Exception as e:
        logger.error(f"Error training model for {crop_name}: {str(e)}")
        return None

def predict_crop_price(crop_name):
    """Predict crop price using trained ML model"""
    try:
        model_path = os.path.join(MODEL_DIR, f"{crop_name}_price_model.joblib")
        if not os.path.exists(model_path):
            logger.warning(f"No model found for {crop_name}")
            return None
            
        model = joblib.load(model_path)
        logger.info(f"Loaded model for {crop_name}")
        
        # Get current date features
        today = datetime.now()
        # Compute price_moving_avg safely
        try:
            df = pd.read_csv(f"data/{crop_name.lower()}data.csv")
            df.columns = [col.strip().lower() for col in df.columns]
            df['date'] = pd.to_datetime(df['date'], format='%d-%m-%Y', errors='coerce')
            df = df.dropna(subset=['date'])

            recent_prices = df[df['date'] < pd.Timestamp.today()].sort_values('date').tail(30)
            price_moving_avg = (
                recent_prices['modal_price'].mean()
                if 'modal_price' in df.columns
                else recent_prices['price'].mean()
            )
        except Exception as e:
            price_moving_avg = 0
            print(f"[WARN] Could not calculate price_moving_avg: {e}")

        # Now create the features DataFrame
        features = pd.DataFrame({
            'year': [today.year],
            'month': [today.month],
            'day': [today.day],
            'price_moving_avg': [price_moving_avg]
        })
        
        prediction = model.predict(features)[0]
        logger.info(f"Predicted price: {prediction}")
        logger.info(f"Features used for prediction: {features}")

        return round(prediction, 2)
        
    except Exception as e:
        logger.error(f"Prediction error: {str(e)}")
        return None


def predict_market_demand(crop_name, prediction_date=None):
    """Predict demand using price trends and seasonality"""
    try:
        # Load data
        df = load_and_preprocess_data()
        crop_data = df[df['Commodity'] == crop_name]
        
        if len(crop_data) < 60:  # Need at least 2 months of data
            logger.warning(f"Insufficient data for demand prediction ({len(crop_data)} records)")
            return None
        
        # Feature Engineering
        X = crop_data[['year', 'month', 'price_moving_avg']]
        X['price_change'] = crop_data['price'].pct_change(periods=7)  # Weekly price change
        X['day_of_year'] = crop_data['date'].dt.dayofyear  # Seasonal effect
        X = X.dropna()
        y = crop_data['price'].iloc[len(crop_data)-len(X):]  # Align targets
        
        # Train model (or load if exists)
        model_path = f"{MODEL_DIR}/{crop_name}_demand_model.joblib"
        if os.path.exists(model_path):
            model = joblib.load(model_path)
        else:
            model = RandomForestRegressor(n_estimators=100)
            model.fit(X, y)
            joblib.dump(model, model_path)
        
        # Prepare prediction features
        target_date = pd.to_datetime(prediction_date) if prediction_date else datetime.now()
        features = pd.DataFrame({
            'year': [target_date.year],
            'month': [target_date.month],
            'price_moving_avg': [crop_data['price_moving_avg'].iloc[-1]],
            'price_change': [crop_data['price'].pct_change(periods=7).iloc[-1]],
            'day_of_year': [target_date.dayofyear]
        }).fillna(0)
        
        # Predict demand (in standardized units)
        return max(0, round(model.predict(features)[0], 2))
        
    except Exception as e:
        logger.error(f"Demand prediction error: {str(e)}")
        return None


import warnings
from sklearn.exceptions import InconsistentVersionWarning

def load_model_safely(model_path):
    """Safely load model with version conflict handling"""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", InconsistentVersionWarning)
        try:
            return joblib.load(model_path)
        except Exception as e:
            logger.error(f"Model loading failed: {str(e)}")
            return None


def recover_models():
    """Recreate models if they fail to load"""
    df = load_and_preprocess_data()
    for model_file in os.listdir(MODEL_DIR):
        if model_file.endswith('.joblib'):
            crop_name = model_file.split('_')[0]
            model_path = os.path.join(MODEL_DIR, model_file)
            
            # Try loading existing model
            model = safe_load_model(model_path)
            if model is None:
                logger.info(f"Retraining model for {crop_name}")
                train_price_model(crop_name, df)


os.makedirs(MODEL_DIR, exist_ok=True)

def train_model(crop_name, df, future_months=12):
    """Train and save model with future prediction capability"""
    try:
        # Feature engineering
        df['date'] = pd.to_datetime(df['Date'])
        df['days'] = (df['date'] - df['date'].min()).dt.days
        df['month'] = df['date'].dt.month
        df['year'] = df['date'].dt.year
        
        # Prepare training data
        X = df[['days', 'month', 'year']]
        y = df['Modal_Price']
        
        # Train model
        model = RandomForestRegressor(n_estimators=100)
        model.fit(X, y)
        
        # Save model
        model_path = os.path.join(MODEL_DIR, f"{crop_name}_model.joblib")
        joblib.dump(model, model_path)
        
        return model_path
    except Exception as e:
        print(f"Training failed: {str(e)}")
        return None

def predict_future_price(crop_name, target_month, target_year):
    """Predict price for a future month/year"""
    try:
        # Load model
        model_path = os.path.join(MODEL_DIR, f"{crop_name}_model.joblib")
        model = joblib.load(model_path)
        
        # Calculate days from first training date
        first_date = datetime.strptime("2023-01-01", "%Y-%m-%d")  # Update with your actual first date
        target_date = datetime(target_year, target_month, 1)
        days = (target_date - first_date).days
        
        # Make prediction
        prediction = model.predict([[days, target_month, target_year]])
        return prediction[0]
    except Exception as e:
        print(f"Prediction failed: {str(e)}")
        return None

