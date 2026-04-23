from flask import Blueprint, redirect, render_template, session, url_for

from database import count_rows, get_connection

stats_bp = Blueprint('stats', __name__, url_prefix='/stats')


@stats_bp.route('')
def overview():
    if not session.get('user_id') or session.get('role') != 'admin':
        return redirect(url_for('dashboard.index'))
    conn = get_connection()
    fans_total = count_rows(conn, 'SELECT COUNT(*) FROM fans')
    seats_total = count_rows(conn, 'SELECT COUNT(*) FROM seats')
    seats_occ = count_rows(conn, 'SELECT COUNT(*) FROM seats WHERE is_occupied=1')
    alerts_resolved = count_rows(conn, 'SELECT COUNT(*) FROM alerts WHERE is_resolved=1')
    occ_pct = int(round((seats_occ / seats_total) * 100)) if seats_total else 0
    satisfaction = round(3.6 + min(1.4, fans_total * 0.05), 1)
    chart_rows = conn.execute(
        "SELECT strftime('%H', recorded_at) AS h, AVG(temperature) AS avg_t FROM sensor_readings WHERE date(recorded_at)=date('now','localtime') GROUP BY h ORDER BY h"
    ).fetchall()
    if not chart_rows:
        chart_rows = conn.execute(
            "SELECT strftime('%H', recorded_at) AS h, AVG(temperature) AS avg_t FROM sensor_readings GROUP BY h ORDER BY datetime(recorded_at) DESC LIMIT 24"
        ).fetchall()
    nat_rows = conn.execute(
        "SELECT COALESCE(NULLIF(TRIM(nationality), ''), 'غير محدد') AS nat, COUNT(*) AS c FROM fans GROUP BY 1 ORDER BY c DESC"
    ).fetchall()
    conn.close()
    chart_labels = [r['h'] or '0' for r in chart_rows]
    chart_values = [round(float(r['avg_t'] or 0), 1) for r in chart_rows]
    return render_template(
        'stats/overview.html',
        fans_total=fans_total,
        occ_pct=occ_pct,
        alerts_resolved=alerts_resolved,
        satisfaction=satisfaction,
        chart_labels=chart_labels,
        chart_values=chart_values,
        nat_rows=nat_rows,
    )
