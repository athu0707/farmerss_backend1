import psycopg2
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import os

# Local fallback for your PC + Render support
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://neondb_owner:npg_dgZW6ikeqps2@ep-winter-hill-abxhds7q-pooler.eu-west-2.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
)

def get_db_connection():
    return psycopg2.connect(DATABASE_URL)


# ---------------------------
# USER MODEL
# ---------------------------
class User(UserMixin):
    def __init__(self, id, username, role):
        self.id = id
        self.username = username
        self.role = role


# ---------------------------
# USER FUNCTIONS
# ---------------------------
def get_user_by_username(username):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT id, username, role FROM users WHERE username = %s",
        (username,)
    )
    
    row = cursor.fetchone()
    conn.close()

    if row:
        id, username, role = row
        return User(id=id, username=username, role=role)

    return None


def register_user(username, password, role):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    hashed_password = generate_password_hash(password)

    cursor.execute(
        "INSERT INTO users (username, password, role) VALUES (%s, %s, %s)",
        (username, hashed_password, role)
    )
    
    conn.commit()
    conn.close()


def verify_user(username, password):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT id, username, role, password FROM users WHERE username = %s",
        (username,)
    )
    
    row = cursor.fetchone()
    conn.close()

    if row:
        id, username, role, hashed_password = row
        if check_password_hash(hashed_password, password):
            return User(id=id, username=username, role=role)

    return None
