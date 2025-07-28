import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join("database", "attendance.db")


def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()

        
        c.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                roll TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                image_path TEXT
            )
        """)

       
        c.execute("""
            CREATE TABLE IF NOT EXISTS attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                timestamp TEXT,
                status TEXT,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        """)

        conn.commit()



def add_user(name, email, roll, password, image_path):
    try:
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            c.execute("""
                INSERT INTO users (name, email, roll, password, image_path)
                VALUES (?, ?, ?, ?, ?)
            """, (name, email, roll, password, image_path))
            conn.commit()
            return True
    except sqlite3.IntegrityError:
        return False



def validate_login(email, password):
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE email=? AND password=?", (email, password))
        user = c.fetchone()
        return user



def get_user_by_email(email):
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE email=?", (email,))
        return c.fetchone()



def mark_attendance(user_id, status="Present"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        
        c.execute("""
            SELECT * FROM attendance
            WHERE user_id = ? AND DATE(timestamp) = DATE(?)
        """, (user_id, timestamp))
        already_marked = c.fetchone()

        if not already_marked:
            c.execute("""
                INSERT INTO attendance (user_id, timestamp, status)
                VALUES (?, ?, ?)
            """, (user_id, timestamp, status))
            conn.commit()
            return True
        else:
            return False



def get_all_attendance():
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row  
        c = conn.cursor()
        c.execute("""
            SELECT users.name, users.roll, attendance.timestamp, attendance.status
            FROM attendance
            JOIN users ON attendance.user_id = users.id
            ORDER BY attendance.timestamp DESC
        """)
        rows = c.fetchall()
        return [dict(row) for row in rows]



def get_attendance_by_user(user_id):
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("""
            SELECT timestamp, status FROM attendance
            WHERE user_id = ?
            ORDER BY timestamp DESC
        """, (user_id,))
        return c.fetchall()


def register_user(name, email, roll, password, image_path):
    return add_user(name, email, roll, password, image_path)

def authenticate_user(email, password):
    return validate_login(email, password)

def log_attendance(user_id):
    return mark_attendance(user_id)

def fetch_attendance():
    return get_all_attendance()
