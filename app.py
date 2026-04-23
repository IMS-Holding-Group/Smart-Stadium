import os
from functools import wraps

from flask import Flask, redirect, send_from_directory, session, url_for

from config import BASE_DIR, DEBUG, SECRET_KEY
from routes.admin import admin_bp
from routes.alerts import alerts_api_bp, alerts_bp
from routes.auth import auth_bp
from routes.cooling import cooling_api_bp, cooling_bp
from routes.dashboard import dashboard_bp
from routes.fans import fans_bp
from routes.navigation import navigation_api_bp, navigation_bp
from routes.reports_view import stats_bp
from routes.sensors import sensor_api_bp, sensors_bp
from routes.seats import seats_bp

app = Flask(__name__, static_folder='static', static_url_path='/static')
app.secret_key = SECRET_KEY


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)

    return decorated


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get('role') != 'admin':
            return redirect(url_for('dashboard.index'))
        return f(*args, **kwargs)

    return decorated


@app.route('/assets/<path:filename>')
def assets(filename):
    return send_from_directory(os.path.join(BASE_DIR, 'assets'), filename)


@app.route('/')
def home():
    if session.get('user_id'):
        return redirect(url_for('dashboard.index'))
    return redirect(url_for('auth.login'))


app.register_blueprint(auth_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(fans_bp)
app.register_blueprint(seats_bp)
app.register_blueprint(sensors_bp)
app.register_blueprint(sensor_api_bp)
app.register_blueprint(cooling_bp)
app.register_blueprint(cooling_api_bp)
app.register_blueprint(navigation_bp)
app.register_blueprint(navigation_api_bp)
app.register_blueprint(alerts_bp)
app.register_blueprint(alerts_api_bp)
app.register_blueprint(stats_bp)
app.register_blueprint(admin_bp)


if __name__ == '__main__':
    app.run(debug=DEBUG, host='127.0.0.1', port=5000)
