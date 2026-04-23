import json

from flask import Blueprint, redirect, render_template, session, url_for

from database import get_connection

seats_bp = Blueprint('seats', __name__, url_prefix='/seats')


def _admin_only():
    return session.get('role') == 'admin'


@seats_bp.route('')
def seat_list():
    if not session.get('user_id') or not _admin_only():
        return redirect(url_for('dashboard.index'))
    conn = get_connection()
    rows = conn.execute(
        'SELECT * FROM seats ORDER BY block, row_number, seat_number'
    ).fetchall()
    conn.close()
    return render_template('seats/list.html', rows=rows)


@seats_bp.route('/map')
def seat_map():
    if not session.get('user_id') or not _admin_only():
        return redirect(url_for('dashboard.index'))
    conn = get_connection()
    stats = []
    for block in ('A', 'B', 'C', 'D'):
        total = conn.execute(
            'SELECT COUNT(*) FROM seats WHERE block=?', (block,)
        ).fetchone()[0]
        occ = conn.execute(
            'SELECT COUNT(*) FROM seats WHERE block=? AND is_occupied=1', (block,)
        ).fetchone()[0]
        pct = int(round((occ / total) * 100)) if total else 0
        stats.append({'block': block, 'total': total, 'occupied': occ, 'pct': pct})
    seats = conn.execute(
        'SELECT id, block, row_number, seat_number, gate, is_occupied, cooling_status FROM seats ORDER BY block, row_number, seat_number'
    ).fetchall()
    conn.close()
    seats_json = [dict(r) for r in seats]
    return render_template(
        'seats/map.html',
        stats=stats,
        seats_json=json.dumps(seats_json, ensure_ascii=False),
    )
