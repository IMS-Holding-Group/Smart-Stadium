from flask import Blueprint, redirect, render_template, request, session, url_for
from werkzeug.security import generate_password_hash

from database import get_connection

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


def _admin_only():
    return session.get('role') == 'admin'


@admin_bp.route('/users')
def users_list():
    if not session.get('user_id') or not _admin_only():
        return redirect(url_for('dashboard.index'))
    conn = get_connection()
    rows = conn.execute(
        'SELECT id, username, role, full_name, created_at FROM users ORDER BY id'
    ).fetchall()
    conn.close()
    return render_template('admin/users.html', rows=rows)


@admin_bp.route('/users/add', methods=['POST'])
def users_add():
    if not session.get('user_id') or not _admin_only():
        return redirect(url_for('dashboard.index'))
    username = (request.form.get('username') or '').strip()
    password = request.form.get('password') or ''
    role = request.form.get('role')
    full_name = (request.form.get('full_name') or '').strip()
    if role not in ('admin', 'staff', 'fan'):
        return redirect(url_for('admin.users_list'))
    if not username or not password or not full_name:
        return redirect(url_for('admin.users_list'))
    conn = get_connection()
    if conn.execute('SELECT id FROM users WHERE username=?', (username,)).fetchone():
        conn.close()
        return redirect(url_for('admin.users_list'))
    pw = generate_password_hash(password)
    conn.execute(
        'INSERT INTO users (username, password, role, full_name) VALUES (?, ?, ?, ?)',
        (username, pw, role, full_name),
    )
    conn.commit()
    conn.close()
    return redirect(url_for('admin.users_list'))


@admin_bp.route('/users/<int:user_id>/delete', methods=['POST'])
def users_delete(user_id):
    if not session.get('user_id') or not _admin_only():
        return redirect(url_for('dashboard.index'))
    if user_id == session.get('user_id'):
        return redirect(url_for('admin.users_list'))
    conn = get_connection()
    fan = conn.execute('SELECT id FROM fans WHERE user_id=?', (user_id,)).fetchone()
    if fan:
        fid = fan['id']
        seat_row = conn.execute('SELECT seat_id FROM fans WHERE id=?', (fid,)).fetchone()
        if seat_row:
            conn.execute('UPDATE seats SET is_occupied=0 WHERE id=?', (seat_row['seat_id'],))
        conn.execute('DELETE FROM fans WHERE id=?', (fid,))
    conn.execute('DELETE FROM users WHERE id=?', (user_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin.users_list'))
