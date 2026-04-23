from flask import Blueprint, redirect, render_template, request, session, url_for
from werkzeug.security import generate_password_hash

from database import get_connection

fans_bp = Blueprint('fans', __name__, url_prefix='/fans')


def _admin_only():
    return session.get('role') == 'admin'


@fans_bp.route('')
def fan_list():
    if not session.get('user_id'):
        return redirect(url_for('auth.login'))
    if not _admin_only():
        return redirect(url_for('dashboard.index'))
    conn = get_connection()
    rows = conn.execute(
        'SELECT f.id, u.full_name, f.ticket_number, f.nationality, s.block, s.row_number, s.seat_number, s.is_occupied FROM fans f JOIN users u ON u.id=f.user_id JOIN seats s ON s.id=f.seat_id ORDER BY f.id'
    ).fetchall()
    conn.close()
    return render_template('fans/list.html', rows=rows)


@fans_bp.route('/<int:fan_id>')
def fan_detail(fan_id):
    if not session.get('user_id'):
        return redirect(url_for('auth.login'))
    conn = get_connection()
    fan = conn.execute(
        'SELECT f.*, u.full_name, u.username, s.block, s.row_number, s.seat_number, s.gate, s.cooling_status FROM fans f JOIN users u ON u.id=f.user_id JOIN seats s ON s.id=f.seat_id WHERE f.id=?',
        (fan_id,),
    ).fetchone()
    conn.close()
    if not fan:
        return redirect(url_for('dashboard.index'))
    if session.get('role') == 'fan' and session.get('fan_id') != fan_id:
        return redirect(url_for('fans.fan_detail', fan_id=session['fan_id']))
    if session.get('role') not in ('admin', 'fan'):
        return redirect(url_for('dashboard.index'))
    return render_template('fans/detail.html', fan=fan)


@fans_bp.route('/add', methods=['GET', 'POST'])
def fan_add():
    if not session.get('user_id') or not _admin_only():
        return redirect(url_for('dashboard.index'))
    conn = get_connection()
    if request.method == 'GET':
        free_seats = conn.execute(
            "SELECT id, block, row_number, seat_number FROM seats WHERE is_occupied=0 ORDER BY block, row_number, seat_number LIMIT 500"
        ).fetchall()
        conn.close()
        return render_template('fans/add.html', free_seats=free_seats)

    username = (request.form.get('username') or '').strip()
    password = request.form.get('password') or ''
    full_name = (request.form.get('full_name') or '').strip()
    ticket_number = (request.form.get('ticket_number') or '').strip()
    seat_id = request.form.get('seat_id')
    nationality = (request.form.get('nationality') or '').strip() or None
    phone = (request.form.get('phone') or '').strip() or None
    lang = request.form.get('language_pref') or 'ar'
    if lang not in ('ar', 'en'):
        lang = 'ar'

    if not all([username, password, full_name, ticket_number, seat_id]):
        free_seats = conn.execute(
            "SELECT id, block, row_number, seat_number FROM seats WHERE is_occupied=0 ORDER BY block, row_number, seat_number LIMIT 500"
        ).fetchall()
        conn.close()
        return render_template(
            'fans/add.html',
            free_seats=free_seats,
            error='يرجى تعبئة جميع الحقول المطلوبة.',
        )

    dup = conn.execute('SELECT id FROM users WHERE username=?', (username,)).fetchone()
    if dup:
        free_seats = conn.execute(
            "SELECT id, block, row_number, seat_number FROM seats WHERE is_occupied=0 ORDER BY block, row_number, seat_number LIMIT 500"
        ).fetchall()
        conn.close()
        return render_template('fans/add.html', free_seats=free_seats, error='اسم المستخدم مستخدم مسبقاً.')

    seat = conn.execute('SELECT * FROM seats WHERE id=? AND is_occupied=0', (seat_id,)).fetchone()
    if not seat:
        free_seats = conn.execute(
            "SELECT id, block, row_number, seat_number FROM seats WHERE is_occupied=0 ORDER BY block, row_number, seat_number LIMIT 500"
        ).fetchall()
        conn.close()
        return render_template('fans/add.html', free_seats=free_seats, error='المقعد غير متاح.')

    ticket_dup = conn.execute('SELECT id FROM fans WHERE ticket_number=?', (ticket_number,)).fetchone()
    if ticket_dup:
        free_seats = conn.execute(
            "SELECT id, block, row_number, seat_number FROM seats WHERE is_occupied=0 ORDER BY block, row_number, seat_number LIMIT 500"
        ).fetchall()
        conn.close()
        return render_template('fans/add.html', free_seats=free_seats, error='رقم التذكرة مستخدم مسبقاً.')

    pw = generate_password_hash(password)
    cur = conn.execute(
        'INSERT INTO users (username, password, role, full_name) VALUES (?, ?, ?, ?)',
        (username, pw, 'fan', full_name),
    )
    uid = cur.lastrowid
    conn.execute(
        'INSERT INTO fans (user_id, ticket_number, seat_id, nationality, phone, language_pref) VALUES (?, ?, ?, ?, ?, ?)',
        (uid, ticket_number, seat_id, nationality, phone, lang),
    )
    conn.execute('UPDATE seats SET is_occupied=1 WHERE id=?', (seat_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('fans.fan_list'))


@fans_bp.route('/<int:fan_id>/delete', methods=['POST'])
def fan_delete(fan_id):
    if not session.get('user_id') or not _admin_only():
        return redirect(url_for('dashboard.index'))
    conn = get_connection()
    fan = conn.execute('SELECT * FROM fans WHERE id=?', (fan_id,)).fetchone()
    if not fan:
        conn.close()
        return redirect(url_for('fans.fan_list'))
    seat_id = fan['seat_id']
    user_id = fan['user_id']
    conn.execute('DELETE FROM fans WHERE id=?', (fan_id,))
    conn.execute('DELETE FROM users WHERE id=?', (user_id,))
    conn.execute('UPDATE seats SET is_occupied=0 WHERE id=?', (seat_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('fans.fan_list'))
