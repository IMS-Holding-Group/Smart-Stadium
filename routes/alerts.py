from flask import Blueprint, jsonify, redirect, render_template, request, session, url_for

from database import get_connection

alerts_bp = Blueprint('alerts', __name__, url_prefix='/alerts')
alerts_api_bp = Blueprint('alerts_api', __name__)


@alerts_bp.route('')
def center():
    if not session.get('user_id'):
        return redirect(url_for('auth.login'))
    conn = get_connection()
    rows = conn.execute(
        'SELECT a.*, u.full_name AS resolver_name FROM alerts a LEFT JOIN users u ON u.id=a.resolved_by ORDER BY datetime(a.created_at) DESC LIMIT 300'
    ).fetchall()
    conn.close()
    is_admin = session.get('role') == 'admin'
    return render_template('alerts/center.html', rows=rows, is_admin=is_admin)


@alerts_bp.route('/add', methods=['POST'])
def add_alert():
    if not session.get('user_id') or session.get('role') != 'admin':
        return redirect(url_for('alerts.center'))
    alert_type = request.form.get('alert_type')
    priority = request.form.get('priority')
    zone = (request.form.get('zone') or '').strip() or None
    message_ar = (request.form.get('message_ar') or '').strip()
    if alert_type not in ('heat', 'crowd', 'device_fault', 'emergency', 'info'):
        return redirect(url_for('alerts.center'))
    if priority not in ('critical', 'high', 'medium', 'low'):
        return redirect(url_for('alerts.center'))
    if not message_ar:
        return redirect(url_for('alerts.center'))
    conn = get_connection()
    conn.execute(
        'INSERT INTO alerts (alert_type, priority, zone, message_ar, message_en, is_resolved) VALUES (?, ?, ?, ?, NULL, 0)',
        (alert_type, priority, zone, message_ar),
    )
    conn.commit()
    conn.close()
    return redirect(url_for('alerts.center'))


@alerts_api_bp.route('/api/alerts/<int:alert_id>/resolve', methods=['PUT'])
def api_resolve(alert_id):
    if not session.get('user_id'):
        return jsonify({'error': 'غير مصرح'}), 401
    if session.get('role') not in ('admin', 'staff'):
        return jsonify({'error': 'غير مصرح'}), 403
    conn = get_connection()
    row = conn.execute('SELECT * FROM alerts WHERE id=?', (alert_id,)).fetchone()
    if not row:
        conn.close()
        return jsonify({'error': 'غير موجود'}), 404
    conn.execute(
        'UPDATE alerts SET is_resolved=1, resolved_by=?, resolved_at=CURRENT_TIMESTAMP WHERE id=?',
        (session['user_id'], alert_id),
    )
    conn.commit()
    conn.close()
    return jsonify({'ok': True})
