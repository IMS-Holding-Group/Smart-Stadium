from flask import Blueprint, jsonify, redirect, render_template, request, session, url_for

navigation_bp = Blueprint('navigation', __name__, url_prefix='/navigation')
navigation_api_bp = Blueprint('navigation_api', __name__)

GATE_POSITIONS = {
    'G1': {'block': 'A', 'desc': 'البوابة الرئيسية الشمالية'},
    'G2': {'block': 'B', 'desc': 'البوابة الشرقية'},
    'G3': {'block': 'C', 'desc': 'البوابة الجنوبية'},
    'G4': {'block': 'D', 'desc': 'البوابة الغربية'},
}


def _gate_block(gate):
    info = GATE_POSITIONS.get(gate)
    return info['block'] if info else 'A'


def calculate_path(from_gate, to_block, to_row, to_seat):
    gate = from_gate if from_gate in GATE_POSITIONS else 'G1'
    steps = []
    steps.append(f"ادخل من {GATE_POSITIONS[gate]['desc']}")
    start_block = _gate_block(gate)
    if start_block == to_block:
        steps.append(f"اتجه مباشرة إلى القطاع {to_block}")
    else:
        steps.append('اتجه يساراً عبر الممر الدائري')
        steps.append(f"ادخل إلى القطاع {to_block}")
    steps.append(f"ابحث عن الصف رقم {to_row}")
    steps.append(f"مقعدك رقم {to_seat} في هذا الصف")
    tr = int(to_row)
    distance = abs(ord(start_block) - ord(to_block)) * 50 + tr * 3
    return {
        'steps': steps,
        'distance_meters': distance,
        'estimated_minutes': max(2, distance // 40),
        'from_gate': gate,
        'to_block': to_block,
        'to_row': tr,
        'to_seat': int(to_seat),
    }


@navigation_bp.route('')
def guide():
    if not session.get('user_id'):
        return redirect(url_for('auth.login'))
    return render_template('navigation/guide.html')


@navigation_api_bp.route('/api/navigation/path')
def api_navigation_path():
    if not session.get('user_id'):
        return jsonify({'error': 'غير مصرح'}), 401
    gate = request.args.get('gate', 'G1')
    block = request.args.get('block', 'A')
    row = request.args.get('row', '1')
    seat = request.args.get('seat', '1')
    if block not in ('A', 'B', 'C', 'D'):
        return jsonify({'error': 'قطاع غير صالح'}), 400
    try:
        tr = int(row)
        ts = int(seat)
    except ValueError:
        return jsonify({'error': 'أرقام غير صالحة'}), 400
    if gate not in GATE_POSITIONS:
        return jsonify({'error': 'بوابة غير صالحة'}), 400
    data = calculate_path(gate, block, tr, ts)
    return jsonify(data)
