import os

from werkzeug.security import generate_password_hash

from config import DATABASE_PATH
from database import get_connection, init_schema

DEFAULT_USERS = [
    ('admin', 'admin123', 'admin', 'مشرف النظام'),
    ('staff1', 'staff123', 'staff', 'موظف خدمات الملعب'),
    ('fan001', 'fan123', 'fan', 'عبدالله المطيري'),
    ('fan002', 'fan123', 'fan', 'سارة العتيبي'),
    ('fan003', 'fan123', 'fan', 'John Smith'),
]

GATE_BY_BLOCK = {'A': 'G1', 'B': 'G2', 'C': 'G3', 'D': 'G4'}


def seed_users(conn):
    for username, password, role, full_name in DEFAULT_USERS:
        pw = generate_password_hash(password)
        conn.execute(
            'INSERT OR IGNORE INTO users (username, password, role, full_name) VALUES (?, ?, ?, ?)',
            (username, pw, role, full_name),
        )
    conn.commit()


def seed_seats(conn):
    existing = conn.execute('SELECT COUNT(*) FROM seats').fetchone()[0]
    if existing:
        return
    for block in ('A', 'B', 'C', 'D'):
        gate = GATE_BY_BLOCK[block]
        for row in range(1, 11):
            for seat in range(1, 11):
                conn.execute(
                    'INSERT INTO seats (block, row_number, seat_number, gate, is_occupied, cooling_status) VALUES (?, ?, ?, ?, 0, ?)',
                    (block, row, seat, gate, 'off'),
                )
    conn.commit()


def seed_sensors(conn):
    if conn.execute('SELECT COUNT(*) FROM sensors').fetchone()[0]:
        return
    for block in ('A', 'B', 'C', 'D'):
        for n in range(1, 4):
            code = f'SEN-{block}{n}-0{n}'
            x = 0.2 + (ord(block) - ord('A')) * 0.2 + n * 0.02
            y = 0.3 + n * 0.15
            conn.execute(
                "INSERT INTO sensors (sensor_code, zone, location_x, location_y, status, last_temp, last_humidity) VALUES (?, ?, ?, ?, 'active', ?, ?)",
                (code, block, x, y, 26.0 + n, 55.0),
            )
    conn.execute(
        "UPDATE sensors SET status='inactive' WHERE id IN (SELECT id FROM sensors ORDER BY id DESC LIMIT 1)"
    )
    conn.commit()


def seed_alerts(conn):
    if conn.execute('SELECT COUNT(*) FROM alerts').fetchone()[0]:
        return
    samples = [
        ('heat', 'high', 'A', 'ارتفاع ملحوظ في درجة الحرارة بالقطاع أ', None),
        ('crowd', 'medium', 'B', 'ازدحام متوسط عند بوابة الشرق', None),
        ('device_fault', 'critical', 'C', 'خلل في أحد الحساسات بالقطاع ج', None),
        ('emergency', 'critical', 'FIELD', 'تنبيه طوارئ تجريبي — لا يوجد خطر فعلي', None),
        ('info', 'low', 'D', 'تم فتح الممرات الإضافية للخروج', None),
    ]
    for alert_type, priority, zone, msg_ar, msg_en in samples:
        conn.execute(
            'INSERT INTO alerts (alert_type, priority, zone, message_ar, message_en, is_resolved) VALUES (?, ?, ?, ?, ?, 0)',
            (alert_type, priority, zone, msg_ar, msg_en),
        )
    conn.commit()


def seed_sample_readings(conn):
    if conn.execute('SELECT COUNT(*) FROM sensor_readings').fetchone()[0]:
        return
    sensors = conn.execute('SELECT id FROM sensors').fetchall()
    for s in sensors:
        for off in range(0, 24):
            conn.execute(
                "INSERT INTO sensor_readings (sensor_id, temperature, humidity, recorded_at) VALUES (?, ?, ?, datetime('now', 'localtime', ?))",
                (s['id'], 25.0 + (off % 8), 45.0 + (off % 10), '-%d hours' % off),
            )
    conn.commit()


def seed_fans(conn):
    if conn.execute('SELECT COUNT(*) FROM fans').fetchone()[0]:
        return
    fan_users = conn.execute(
        "SELECT id, username FROM users WHERE role='fan' ORDER BY id"
    ).fetchall()
    tickets = ['T-2034-001', 'T-2034-002', 'T-2034-003']
    nationalities = ['السعودية', 'السعودية', 'الولايات المتحدة']
    phones = ['0500000001', '0500000002', '0500000003']
    seat_ids = conn.execute(
        "SELECT id FROM seats WHERE (block='A' AND row_number=1 AND seat_number=1) OR (block='A' AND row_number=1 AND seat_number=2) OR (block='B' AND row_number=1 AND seat_number=1) ORDER BY block, row_number, seat_number"
    ).fetchall()
    seat_id_list = [r[0] for r in seat_ids]
    if len(seat_id_list) < 3:
        seat_id_list = [r[0] for r in conn.execute('SELECT id FROM seats LIMIT 3').fetchall()]
    for i, u in enumerate(fan_users[:3]):
        uid = u['id']
        conn.execute(
            'INSERT INTO fans (user_id, ticket_number, seat_id, nationality, phone, language_pref) VALUES (?, ?, ?, ?, ?, ?)',
            (uid, tickets[i], seat_id_list[i], nationalities[i], phones[i], 'ar' if i < 2 else 'en'),
        )
        conn.execute('UPDATE seats SET is_occupied=1 WHERE id=?', (seat_id_list[i],))
    conn.commit()


def main():
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
    conn = get_connection()
    init_schema(conn)
    seed_users(conn)
    seed_seats(conn)
    seed_sensors(conn)
    seed_alerts(conn)
    seed_sample_readings(conn)
    seed_fans(conn)
    conn.close()
    print('تم تهيئة قاعدة البيانات بنجاح.')


if __name__ == '__main__':
    main()
