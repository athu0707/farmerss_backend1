import mysql.connector

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",  # Replace with your MySQL username
        password="Aai@2601",  # Replace with your MySQL password
        database="crop_supply_chain"
    )

def fetch_crop_prices():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM crop_prices")
    data = cursor.fetchall()
    conn.close()
    return data

def fetch_market_demand():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM market_demand")
    data = cursor.fetchall()
    conn.close()
    return data

def fetch_transportation_routes():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM transportation_routes")
    data = cursor.fetchall()
    conn.close()
    return data

def fetch_storage_recommendations():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM storage_recommendations")
    data = cursor.fetchall()
    conn.close()
    return data

    
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin):
    def __init__(self, id, username, role):
        self.id = id
        self.username = username
        self.role = role

def get_user_by_username(username):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
    user = cursor.fetchone()
    conn.close()
    if user:
        return User(id=user['id'], username=user['username'], role=user['role'])
    return None

def register_user(username, password, role):
    conn = get_db_connection()
    cursor = conn.cursor()
    hashed_password = generate_password_hash(password)
    cursor.execute("INSERT INTO users (username, password, role) VALUES (%s, %s, %s)",
                   (username, hashed_password, role))
    conn.commit()
    conn.close()

def verify_user(username, password):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
    user = cursor.fetchone()
    conn.close()
    if user and check_password_hash(user['password'], password):
        return User(id=user['id'], username=user['username'], role=user['role'])
    return None