(function() {
    var canvas = document.getElementById('stadiumCanvas');
    if (!canvas || !window.SEATS_DATA) return;
    var ctx = canvas.getContext('2d');
    var W = canvas.width;
    var H = canvas.height;
    var cx = W / 2;
    var cy = H / 2;
    var R = Math.min(W, H) / 2 - 40;

    var COLORS = { A: '#bbf7d0', B: '#bfdbfe', C: '#e9d5ff', D: '#fed7aa' };
    var SECTORS = [
        { block: 'A', start: -Math.PI / 4, end: Math.PI / 4 },
        { block: 'B', start: Math.PI / 4, end: (3 * Math.PI) / 4 },
        { block: 'C', start: (3 * Math.PI) / 4, end: (5 * Math.PI) / 4 },
        { block: 'D', start: (5 * Math.PI) / 4, end: (7 * Math.PI) / 4 }
    ];

    var gates = [
        { code: 'G1', angle: -Math.PI / 2 },
        { code: 'G2', angle: 0 },
        { code: 'G3', angle: Math.PI / 2 },
        { code: 'G4', angle: Math.PI }
    ];

    function sectorAt(mx, my) {
        var dx = mx - cx;
        var dy = my - cy;
        var dist = Math.sqrt(dx * dx + dy * dy);
        if (dist > R || dist < R * 0.15) return null;
        var ang = Math.atan2(dy, dx);
        for (var i = 0; i < SECTORS.length; i++) {
            var s = SECTORS[i];
            var a = ang;
            while (a < s.start) a += 2 * Math.PI;
            while (a > s.end + 2 * Math.PI) a -= 2 * Math.PI;
            if (a >= s.start && a <= s.end) return s.block;
        }
        return null;
    }

    function drawField() {
        ctx.clearRect(0, 0, W, H);
        ctx.beginPath();
        ctx.arc(cx, cy, R * 0.14, 0, 2 * Math.PI);
        ctx.fillStyle = '#86efac';
        ctx.fill();

        SECTORS.forEach(function(s) {
            ctx.beginPath();
            ctx.moveTo(cx, cy);
            ctx.arc(cx, cy, R, s.start, s.end);
            ctx.closePath();
            ctx.fillStyle = COLORS[s.block];
            ctx.fill();
            ctx.strokeStyle = '#94a3b8';
            ctx.lineWidth = 2;
            ctx.stroke();
        });

        ctx.beginPath();
        ctx.arc(cx, cy, R * 0.14, 0, 2 * Math.PI);
        ctx.strokeStyle = '#64748b';
        ctx.stroke();

        gates.forEach(function(g) {
            var gx = cx + Math.cos(g.angle) * (R + 10);
            var gy = cy + Math.sin(g.angle) * (R + 10);
            ctx.fillStyle = '#2D1B69';
            ctx.fillRect(gx - 18, gy - 12, 36, 24);
            ctx.fillStyle = '#fff';
            ctx.font = '700 12px IBM Plex Sans Arabic, sans-serif';
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            ctx.fillText(g.code, gx, gy);
        });

        ctx.fillStyle = '#1C1B2E';
        ctx.font = '700 16px IBM Plex Sans Arabic, sans-serif';
        ctx.textAlign = 'center';
        SECTORS.forEach(function(s) {
            var mid = (s.start + s.end) / 2;
            var tx = cx + Math.cos(mid) * (R * 0.55);
            var ty = cy + Math.sin(mid) * (R * 0.55);
            ctx.fillText('قطاع ' + s.block, tx, ty);
        });
    }

    var statsEl = document.getElementById('sectorStats');
    function statsFor(block) {
        if (!statsEl) return { total: 0, occ: 0, pct: 0 };
        var span = statsEl.querySelector('[data-block="' + block + '"]');
        if (!span) return { total: 0, occ: 0, pct: 0 };
        return {
            total: Number(span.getAttribute('data-total') || 0),
            occ: Number(span.getAttribute('data-occ') || 0),
            pct: Number(span.getAttribute('data-pct') || 0)
        };
    }

    var selectedBlock = null;
    var filterMode = 'all';
    var tooltip = document.getElementById('mapTooltip');

    function renderTable() {
        var body = document.getElementById('seatDetailBody');
        if (!body) return;
        body.innerHTML = '';
        if (!selectedBlock) {
            var tr0 = document.createElement('tr');
            tr0.innerHTML = '<td colspan="5">اختر قطاعاً من الخريطة.</td>';
            body.appendChild(tr0);
            return;
        }
        window.SEATS_DATA.filter(function(seat) {
            if (seat.block !== selectedBlock) return false;
            if (filterMode === 'occ') return seat.is_occupied === 1;
            if (filterMode === 'free') return seat.is_occupied === 0;
            return true;
        }).forEach(function(seat) {
            var tr = document.createElement('tr');
            var st = seat.is_occupied ? 'مشغول' : 'فارغ';
            tr.innerHTML =
                '<td>' + seat.seat_number + '</td>' +
                '<td>' + seat.row_number + '</td>' +
                '<td>' + seat.gate + '</td>' +
                '<td>' + st + '</td>' +
                '<td>' + seat.cooling_status + '</td>';
            body.appendChild(tr);
        });
    }

    canvas.addEventListener('mousemove', function(ev) {
        var rect = canvas.getBoundingClientRect();
        var mx = (ev.clientX - rect.left) * (canvas.width / rect.width);
        var my = (ev.clientY - rect.top) * (canvas.height / rect.height);
        var b = sectorAt(mx, my);
        if (!tooltip) return;
        if (!b) {
            tooltip.style.display = 'none';
            return;
        }
        var st = statsFor(b);
        tooltip.style.display = 'block';
        tooltip.style.left = ev.clientX + 12 + 'px';
        tooltip.style.top = ev.clientY + 12 + 'px';
        tooltip.textContent =
            'قطاع ' + b + ' — المقاعد: ' + st.total +
            ' — الإشغال: ' + st.pct + '٪';
    });

    canvas.addEventListener('mouseleave', function() {
        if (tooltip) tooltip.style.display = 'none';
    });

    canvas.addEventListener('click', function(ev) {
        var rect = canvas.getBoundingClientRect();
        var mx = (ev.clientX - rect.left) * (canvas.width / rect.width);
        var my = (ev.clientY - rect.top) * (canvas.height / rect.height);
        var b = sectorAt(mx, my);
        if (b) {
            selectedBlock = b;
            renderTable();
        }
    });

    document.querySelectorAll('.map-filters .toggle-btn').forEach(function(btn) {
        btn.addEventListener('click', function() {
            document.querySelectorAll('.map-filters .toggle-btn').forEach(function(x) {
                x.classList.remove('active');
            });
            btn.classList.add('active');
            filterMode = btn.getAttribute('data-filter') || 'all';
            renderTable();
        });
    });

    drawField();
})();
