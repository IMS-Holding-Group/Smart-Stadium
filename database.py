import os
import random
import sqlite3

from config import DATABASE_PATH


def get_connection():
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys = ON')
    return conn


def init_schema(conn):
    stmts = [
        "CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT NOT NULL UNIQUE, password TEXT NOT NULL, role TEXT NOT NULL CHECK(role IN ('admin', 'staff', 'fan')), full_name TEXT NOT NULL, created_at TEXT DEFAULT CURRENT_TIMESTAMP)",
        "CREATE TABLE IF NOT EXISTS seats (id INTEGER PRIMARY KEY AUTOINCREMENT, block TEXT NOT NULL, row_number INTEGER NOT NULL, seat_number INTEGER NOT NULL, gate TEXT NOT NULL, is_occupied INTEGER DEFAULT 0, cooling_status TEXT DEFAULT 'off' CHECK(cooling_status IN ('off', 'low', 'medium', 'high', 'auto')), UNIQUE(block, row_number, seat_number))",
        "CREATE TABLE IF NOT EXISTS sensors (id INTEGER PRIMARY KEY AUTOINCREMENT, sensor_code TEXT NOT NULL UNIQUE, zone TEXT NOT NULL, location_x REAL, location_y REAL, status TEXT DEFAULT 'active' CHECK(status IN ('active', 'inactive', 'fault')), last_temp REAL DEFAULT 25.0, last_humidity REAL DEFAULT 50.0, last_reading_at TEXT DEFAULT CURRENT_TIMESTAMP)",
        "CREATE TABLE IF NOT EXISTS fans (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER REFERENCES users(id), ticket_number TEXT NOT NULL UNIQUE, seat_id INTEGER REFERENCES seats(id), nationality TEXT, phone TEXT, language_pref TEXT DEFAULT 'ar' CHECK(language_pref IN ('ar', 'en')), registered_at TEXT DEFAULT CURRENT_TIMESTAMP)",
        "CREATE TABLE IF NOT EXISTS sensor_readings (id INTEGER PRIMARY KEY AUTOINCREMENT, sensor_id INTEGER REFERENCES sensors(id), temperature REAL NOT NULL, humidity REAL NOT NULL, recorded_at TEXT DEFAULT CURRENT_TIMESTAMP)",
        "CREATE TABLE IF NOT EXISTS cooling_logs (id INTEGER PRIMARY KEY AUTOINCREMENT, seat_id INTEGER REFERENCES seats(id), action TEXT NOT NULL, triggered_by TEXT NOT NULL CHECK(triggered_by IN ('fan', 'auto', 'admin')), old_status TEXT, new_status TEXT, logged_at TEXT DEFAULT CURRENT_TIMESTAMP)",
        "CREATE TABLE IF NOT EXISTS alerts (id INTEGER PRIMARY KEY AUTOINCREMENT, alert_type TEXT NOT NULL CHECK(alert_type IN ('heat', 'crowd', 'device_fault', 'emergency', 'info')), priority TEXT NOT NULL CHECK(priority IN ('critical', 'high', 'medium', 'low')), zone TEXT, message_ar TEXT NOT NULL, message_en TEXT, is_resolved INTEGER DEFAULT 0, resolved_by INTEGER REFERENCES users(id), created_at TEXT DEFAULT CURRENT_TIMESTAMP, resolved_at TEXT)",
        "CREATE TABLE IF NOT EXISTS navigation_logs (id INTEGER PRIMARY KEY AUTOINCREMENT, fan_id INTEGER REFERENCES fans(id), from_gate TEXT, to_seat_id INTEGER REFERENCES seats(id), path_taken TEXT, duration_seconds INTEGER, logged_at TEXT DEFAULT CURRENT_TIMESTAMP)",
    ]
    for sql in stmts:
        conn.execute(sql)
    conn.commit()


def simulate_sensor_readings(db_conn):
    sensors = db_conn.execute(
        "SELECT id, zone FROM sensors WHERE status='active'"
    ).fetchall()
    for sensor in sensors:
        base_temp = 28.0 if sensor['zone'] in ('A', 'B') else 32.0
        temp = round(base_temp + random.uniform(-2, 6), 1)
        humidity = round(random.uniform(40, 70), 1)
        db_conn.execute(
            "UPDATE sensors SET last_temp=?, last_humidity=?, last_reading_at=datetime('now','localtime') WHERE id=?",
            (temp, humidity, sensor['id']),
        )
        db_conn.execute(
            'INSERT INTO sensor_readings (sensor_id, temperature, humidity) VALUES (?, ?, ?)',
            (sensor['id'], temp, humidity),
        )
    db_conn.commit()


def count_rows(conn, sql, params=()):
    row = conn.execute(sql, params).fetchone()
    return int(row[0]) if row and row[0] is not None else 0


def fan_for_user(conn, user_id):
    return conn.execute('SELECT * FROM fans WHERE user_id=?', (user_id,)).fetchone()


def seat_by_id(conn, seat_id):
    return conn.execute('SELECT * FROM seats WHERE id=?', (seat_id,)).fetchone()


def log_cooling_change(conn, seat_id, action, triggered_by, old_status, new_status):
    conn.execute(
        'INSERT INTO cooling_logs (seat_id, action, triggered_by, old_status, new_status) VALUES (?, ?, ?, ?, ?)',
        (seat_id, action, triggered_by, old_status, new_status),
    )
    conn.commit()
