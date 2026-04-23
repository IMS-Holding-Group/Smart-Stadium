from flask import Blueprint, redirect, render_template, session, url_for

from database import count_rows, get_connection

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/dashboard')
def index():
    if not session.get('user_id'):
        return redirect(url_for('auth.login'))
    role = session.get('role')
    if role == 'admin':
        return redirect(url_for('dashboard.admin_home'))
    if role == 'staff':
        return redirect(url_for('dashboard.staff_home'))
    return redirect(url_for('dashboard.fan_home'))


@dashboard_bp.route('/dashboard/admin')
def admin_home():
    if session.get('role') != 'admin':
        return redirect(url_for('dashboard.index'))
    conn = get_connection()
    fans_total = count_rows(conn, 'SELECT COUNT(*) FROM fans')
    seats_total = count_rows(conn, 'SELECT COUNT(*) FROM seats')
    seats_occ = count_rows(conn, 'SELECT COUNT(*) FROM seats WHERE is_occupied=1')
    avg_temp_row = conn.execute('SELECT AVG(last_temp) AS t FROM sensors WHERE status=?', ('active',)).fetchone()
    avg_temp = round(float(avg_temp_row['t'] or 0), 1)
    active_alerts = count_rows(conn, 'SELECT COUNT(*) FROM alerts WHERE is_resolved=0')
    sensors_active = count_rows(conn, "SELECT COUNT(*) FROM sensors WHERE status='active'")
    sensors_inactive = count_rows(conn, "SELECT COUNT(*) FROM sensors WHERE status!='active'")
    cooling_rows = count_rows(conn, "SELECT COUNT(*) FROM cooling_logs WHERE date(logged_at)=date('now','localtime')")
    energy_kwh = round(120.0 + cooling_rows * 0.15 + fans_total * 0.02, 2)
    recent_alerts = conn.execute(
        'SELECT id, alert_type, priority, zone, message_ar, is_resolved, created_at FROM alerts ORDER BY datetime(created_at) DESC LIMIT 10'
    ).fetchall()
    conn.close()
    occ_pct = int(round((seats_occ / seats_total) * 100)) if seats_total else 0
    return render_template(
        'dashboard/admin.html',
        fans_total=fans_total,
        seats_total=seats_total,
        seats_occ=seats_occ,
        occ_pct=occ_pct,
        avg_temp=avg_temp,
        active_alerts=active_alerts,
        sensors_active=sensors_active,
        sensors_inactive=sensors_inactive,
        energy_kwh=energy_kwh,
        recent_alerts=recent_alerts,
    )


@dashboard_bp.route('/dashboard/staff')
def staff_home():
    if session.get('role') != 'staff':
        return redirect(url_for('dashboard.index'))
    conn = get_connection()
    avg_temp_row = conn.execute('SELECT AVG(last_temp) AS t FROM sensors WHERE status=?', ('active',)).fetchone()
    avg_temp = round(float(avg_temp_row['t'] or 0), 1)
    active_alerts = count_rows(conn, 'SELECT COUNT(*) FROM alerts WHERE is_resolved=0')
    sensors_active = count_rows(conn, "SELECT COUNT(*) FROM sensors WHERE status='active'")
    conn.close()
    return render_template(
        'dashboard/staff.html',
        avg_temp=avg_temp,
        active_alerts=active_alerts,
        sensors_active=sensors_active,
    )


@dashboard_bp.route('/dashboard/fan')
def fan_home():
    if session.get('role') != 'fan':
        return redirect(url_for('dashboard.index'))
    if not session.get('fan_id'):
        session.clear()
        return redirect(url_for('auth.login'))
    fan_id = session['fan_id']
    conn = get_connection()
    fan = conn.execute(
        'SELECT f.*, u.full_name, s.block, s.row_number, s.seat_number, s.gate, s.cooling_status FROM fans f JOIN users u ON u.id=f.user_id JOIN seats s ON s.id=f.seat_id WHERE f.id=?',
        (fan_id,),
    ).fetchone()
    zone = fan['block'] if fan else 'A'
    temp_row = conn.execute(
        'SELECT AVG(last_temp) FROM sensors WHERE zone=? AND status=?',
        (zone, 'active'),
    ).fetchone()
    zone_temp = round(float(temp_row[0] or 28), 1)
    fan_alerts = conn.execute(
        "SELECT id, alert_type, priority, zone, message_ar, created_at FROM alerts WHERE is_resolved=0 AND (zone IS NULL OR zone=? OR zone='FIELD') ORDER BY datetime(created_at) DESC LIMIT 5",
        (zone,),
    ).fetchall()
    conn.close()
    return render_template('dashboard/fan.html', fan=fan, zone_temp=zone_temp, fan_alerts=fan_alerts)
