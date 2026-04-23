from flask import Blueprint, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash

from database import fan_for_user, get_connection

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        if session.get('user_id'):
            return redirect(url_for('dashboard.index'))
        return render_template('login.html')

    username = (request.form.get('username') or '').strip()
    password = request.form.get('password') or ''
    if not username or not password:
        return render_template('login.html', error='يرجى إدخال اسم المستخدم وكلمة المرور.')

    conn = get_connection()
    user = conn.execute('SELECT * FROM users WHERE username=?', (username,)).fetchone()
    conn.close()

    if not user or not check_password_hash(user['password'], password):
        return render_template('login.html', error='بيانات الدخول غير صحيحة.')

    session['user_id'] = user['id']
    session['username'] = user['username']
    session['role'] = user['role']
    session['full_name'] = user['full_name']

    conn = get_connection()
    fan = fan_for_user(conn, user['id'])
    conn.close()
    session['fan_id'] = fan['id'] if fan else None

    return redirect(url_for('dashboard.index'))


@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))
