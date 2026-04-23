from flask import Blueprint, jsonify, redirect, render_template, request, session, url_for

from database import fan_for_user, get_connection, log_cooling_change

cooling_bp = Blueprint('cooling', __name__, url_prefix='/cooling')
cooling_api_bp = Blueprint('cooling_api', __name__)

AUTO_COOLING_THRESHOLD = 32.0

LEVELS = ('off', 'low', 'medium', 'high', 'auto')


def _staff_or_admin():
    return session.get('role') in ('admin', 'staff')


def auto_adjust_cooling(db_conn, seat_id, current_temp):
    if current_temp >= AUTO_COOLING_THRESHOLD + 3:
        new_level = 'high'
    elif current_temp >= AUTO_COOLING_THRESHOLD:
        new_level = 'medium'
    elif current_temp >= AUTO_COOLING_THRESHOLD - 3:
        new_level = 'low'
    else:
        new_level = 'off'
    db_conn.execute('UPDATE seats SET cooling_status=? WHERE id=?', (new_level, seat_id))
    db_conn.commit()
    return new_level


@cooling_bp.route('')
def control_page():
    if not session.get('user_id') or not _staff_or_admin():
        return redirect(url_for('dashboard.index'))
    conn = get_connection()
    counts = {}
    for lvl in LEVELS:
        counts[lvl] = conn.execute(
            'SELECT COUNT(*) FROM seats WHERE cooling_status=?', (lvl,)
        ).fetchone()[0]
    rows = conn.execute(
        'SELECT id, block, row_number, seat_number, cooling_status, is_occupied FROM seats ORDER BY block, row_number, seat_number'
    ).fetchall()
    conn.close()
    return render_template('cooling/control.html', rows=rows, counts=counts)


@cooling_api_bp.route('/api/cooling/set', methods=['POST'])
def api_cooling_set():
    if not session.get('user_id'):
        return jsonify({'error': 'غير مصرح'}), 401
    role = session.get('role')
    if role not in ('admin', 'staff', 'fan'):
        return jsonify({'error': 'غير مصرح'}), 403
    body = request.get_json(silent=True) or {}
    seat_id = body.get('seat_id')
    level = body.get('level')
    if seat_id is None or level not in ('off', 'low', 'medium', 'high', 'auto'):
        return jsonify({'error': 'بيانات غير صالحة'}), 400
    conn = get_connection()
    if role == 'fan':
        fan = fan_for_user(conn, session['user_id'])
        if not fan or int(fan['seat_id']) != int(seat_id):
            conn.close()
            return jsonify({'error': 'غير مسموح'}), 403
    seat = conn.execute('SELECT * FROM seats WHERE id=?', (seat_id,)).fetchone()
    if not seat:
        conn.close()
        return jsonify({'error': 'المقعد غير موجود'}), 404
    old = seat['cooling_status']
    triggered = 'admin' if role in ('admin', 'staff') else 'fan'
    conn.execute('UPDATE seats SET cooling_status=? WHERE id=?', (level, seat_id))
    conn.commit()
    log_cooling_change(conn, seat_id, f'set_{level}', triggered, old, level)
    conn.close()
    return jsonify({'ok': True, 'seat_id': seat_id, 'cooling_status': level})


@cooling_api_bp.route('/api/cooling/set-all', methods=['POST'])
def api_cooling_set_all():
    if not session.get('user_id'):
        return jsonify({'error': 'غير مصرح'}), 401
    if not _staff_or_admin():
        return jsonify({'error': 'غير مصرح'}), 403
    body = request.get_json(silent=True) or {}
    level = body.get('level')
    if level not in ('off', 'low', 'medium', 'high', 'auto'):
        return jsonify({'error': 'مستوى غير صالح'}), 400
    conn = get_connection()
    seats = conn.execute('SELECT id, cooling_status FROM seats').fetchall()
    for s in seats:
        log_cooling_change(conn, s['id'], f'set_all_{level}', 'admin', s['cooling_status'], level)
    conn.execute('UPDATE seats SET cooling_status=?', (level,))
    conn.commit()
    conn.close()
    return jsonify({'ok': True, 'level': level})
