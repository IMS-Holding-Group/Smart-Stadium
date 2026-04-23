(function() {
    var canvas = document.getElementById('navCanvas');
    if (!canvas) return;
    var ctx = canvas.getContext('2d');
    var W = canvas.width;
    var H = canvas.height;
    var cx = W / 2;
    var cy = H / 2;
    var R = Math.min(W, H) / 2 - 50;

    var gateAngles = { G1: -Math.PI / 2, G2: 0, G3: Math.PI / 2, G4: Math.PI };

    function drawBase() {
        ctx.clearRect(0, 0, W, H);
        ctx.beginPath();
        ctx.arc(cx, cy, R, 0, 2 * Math.PI);
        ctx.fillStyle = '#f5f3ff';
        ctx.fill();
        ctx.strokeStyle = '#c4b5fd';
        ctx.stroke();
        ctx.beginPath();
        ctx.arc(cx, cy, R * 0.2, 0, 2 * Math.PI);
        ctx.fillStyle = '#bbf7d0';
        ctx.fill();
        Object.keys(gateAngles).forEach(function(g) {
            var ang = gateAngles[g];
            var gx = cx + Math.cos(ang) * (R + 8);
            var gy = cy + Math.sin(ang) * (R + 8);
            ctx.fillStyle = '#2D1B69';
            ctx.fillRect(gx - 20, gy - 10, 40, 20);
            ctx.fillStyle = '#fff';
            ctx.font = '700 12px IBM Plex Sans Arabic, sans-serif';
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            ctx.fillText(g, gx, gy);
        });
    }

    function blockPoint(block) {
        var map = {
            A: { x: cx + R * 0.45, y: cy - R * 0.1 },
            B: { x: cx + R * 0.35, y: cy + R * 0.35 },
            C: { x: cx - R * 0.35, y: cy + R * 0.35 },
            D: { x: cx - R * 0.45, y: cy - R * 0.1 }
        };
        return map[block] || { x: cx, y: cy };
    }

    function gatePoint(gate) {
        var ang = gateAngles[gate] || -Math.PI / 2;
        return { x: cx + Math.cos(ang) * (R - 20), y: cy + Math.sin(ang) * (R - 20) };
    }

    function drawArrow(from, to) {
        ctx.strokeStyle = '#7C3AED';
        ctx.lineWidth = 4;
        ctx.beginPath();
        ctx.moveTo(from.x, from.y);
        ctx.lineTo(to.x, to.y);
        ctx.stroke();
        var ang = Math.atan2(to.y - from.y, to.x - from.x);
        var ah = 12;
        ctx.beginPath();
        ctx.moveTo(to.x, to.y);
        ctx.lineTo(to.x - ah * Math.cos(ang - 0.4), to.y - ah * Math.sin(ang - 0.4));
        ctx.lineTo(to.x - ah * Math.cos(ang + 0.4), to.y - ah * Math.sin(ang + 0.4));
        ctx.closePath();
        ctx.fillStyle = '#7C3AED';
        ctx.fill();
    }

    function drawMarker(pt, color) {
        ctx.beginPath();
        ctx.arc(pt.x, pt.y, 10, 0, 2 * Math.PI);
        ctx.fillStyle = color;
        ctx.fill();
        ctx.lineWidth = 2;
        ctx.strokeStyle = '#fff';
        ctx.stroke();
    }

    function renderPath(gate, block) {
        drawBase();
        var g = gatePoint(gate);
        var b = blockPoint(block);
        drawMarker(g, '#059669');
        drawArrow(g, b);
        drawMarker(b, '#DC2626');
    }

    drawBase();

    document.getElementById('btnPath').addEventListener('click', function() {
        var gate = document.getElementById('fromGate').value;
        var block = document.getElementById('toBlock').value;
        var row = document.getElementById('toRow').value;
        var seat = document.getElementById('toSeat').value;
        var qs =
            '?gate=' + encodeURIComponent(gate) +
            '&block=' + encodeURIComponent(block) +
            '&row=' + encodeURIComponent(row) +
            '&seat=' + encodeURIComponent(seat);
        fetch('/api/navigation/path' + qs)
            .then(function(r) { return r.json(); })
            .then(function(data) {
                if (data.error) {
                    document.getElementById('pathInfo').textContent = data.error;
                    return;
                }
                renderPath(gate, block);
                document.getElementById('pathInfo').textContent =
                    'المسافة التقديرية: ' + data.distance_meters +
                    ' م — الوقت التقديري: ' + data.estimated_minutes + ' دقيقة';
                var ol = document.getElementById('pathSteps');
                ol.innerHTML = '';
                (data.steps || []).forEach(function(s) {
                    var li = document.createElement('li');
                    li.textContent = s;
                    ol.appendChild(li);
                });
            })
            .catch(function() {
                document.getElementById('pathInfo').textContent = 'تعذر حساب المسار.';
            });
    });
})();
