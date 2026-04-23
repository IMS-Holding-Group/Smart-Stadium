import json

from flask import Blueprint, jsonify, redirect, render_template, session, url_for

from database import get_connection, simulate_sensor_readings

sensors_bp = Blueprint('sensors', __name__, url_prefix='/sensors')
sensor_api_bp = Blueprint('sensor_api', __name__)


def _staff_or_admin():
    return session.get('role') in ('admin', 'staff')


@sensors_bp.route('')
def monitor():
    if not session.get('user_id') or not _staff_or_admin():
        return redirect(url_for('dashboard.index'))
    conn = get_connection()
    rows = conn.execute('SELECT * FROM sensors ORDER BY zone, id').fetchall()
    conn.close()
    payload = [dict(r) for r in rows]
    return render_template(
        'sensors/monitor.html',
        sensors=rows,
        sensors_json=json.dumps(payload, ensure_ascii=False),
    )


@sensors_bp.route('/history')
def history():
    if not session.get('user_id') or not _staff_or_admin():
        return redirect(url_for('dashboard.index'))
    conn = get_connection()
    rows = conn.execute(
        'SELECT r.id, s.sensor_code, r.temperature, r.humidity, r.recorded_at FROM sensor_readings r JOIN sensors s ON s.id=r.sensor_id ORDER BY datetime(r.recorded_at) DESC LIMIT 200'
    ).fetchall()
    conn.close()
    return render_template('sensors/history.html', rows=rows)


@sensor_api_bp.route('/api/sensors/live')
def api_sensors_live():
    if not session.get('user_id'):
        return jsonify({'error': 'غير مصرح'}), 401
    if not _staff_or_admin():
        return jsonify({'error': 'غير مصرح'}), 403
    conn = get_connection()
    rows = conn.execute('SELECT * FROM sensors ORDER BY zone, id').fetchall()
    conn.close()
    data = [dict(r) for r in rows]
    return jsonify({'sensors': data})


@sensor_api_bp.route('/api/sensors/simulate', methods=['POST'])
def api_sensors_simulate():
    if not session.get('user_id'):
        return jsonify({'error': 'غير مصرح'}), 401
    if not _staff_or_admin():
        return jsonify({'error': 'غير مصرح'}), 403
    conn = get_connection()
    simulate_sensor_readings(conn)
    conn.close()
    return jsonify({'ok': True, 'message': 'تمت محاكاة القراءات.'})
