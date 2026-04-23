(function() {
    var cardsRoot = document.getElementById('sensorCards');
    var heat = document.getElementById('heatCanvas');
    if (!cardsRoot) return;

    function tempColor(t) {
        if (t < 25) return '#2563eb';
        if (t < 30) return '#16a34a';
        if (t < 35) return '#eab308';
        return '#dc2626';
    }

    function setMarker(bar, temp) {
        var m = bar.querySelector('.temp-marker');
        if (!m) return;
        var p = Math.max(0, Math.min(100, ((temp - 20) / 20) * 100));
        m.style.left = p + '%';
    }

    function renderCards(list) {
        cardsRoot.innerHTML = '';
        list.forEach(function(s) {
            var card = document.createElement('div');
            card.className = 'sensor-card';
            var active = s.status === 'active';
            card.innerHTML =
                '<div class="sensor-code">' + s.sensor_code + '</div>' +
                '<p class="muted">المنطقة: ' + s.zone + '</p>' +
                '<div class="stat-big temp-val">' + s.last_temp + '°C</div>' +
                '<div class="temp-bar" aria-hidden="true"><span class="temp-marker" style="left:0;"></span></div>' +
                '<p>الرطوبة: <span class="hum-val">' + s.last_humidity + '</span>٪ 💧</p>' +
                '<p class="status-dot ' + (active ? 'status-on' : 'status-off') + '">' +
                (active ? 'نشط' : 'معطل') + '</p>';
            var bar = card.querySelector('.temp-bar');
            setMarker(bar, Number(s.last_temp));
            cardsRoot.appendChild(card);
        });
        drawHeat(list);
    }

    function drawHeat(list) {
        if (!heat) return;
        var ctx = heat.getContext('2d');
        var W = heat.width;
        var H = heat.height;
        ctx.clearRect(0, 0, W, H);
        ctx.fillStyle = '#f8fafc';
        ctx.fillRect(0, 0, W, H);
        ctx.strokeStyle = '#cbd5e1';
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.ellipse(W / 2, H / 2, W * 0.38, H * 0.32, 0, 0, 2 * Math.PI);
        ctx.stroke();
        list.forEach(function(s) {
            var x = (Number(s.location_x) || 0.5) * W;
            var y = (Number(s.location_y) || 0.5) * H;
            ctx.beginPath();
            ctx.arc(x, y, 8, 0, 2 * Math.PI);
            ctx.fillStyle = tempColor(Number(s.last_temp));
            ctx.fill();
        });
    }

    function refresh() {
        fetch('/api/sensors/live')
            .then(function(r) { return r.json(); })
            .then(function(data) {
                if (data.sensors) renderCards(data.sensors);
            })
            .catch(function() {});
    }

    var btn = document.getElementById('btnSimulate');
    if (btn) {
        btn.addEventListener('click', function() {
            fetch('/api/sensors/simulate', { method: 'POST' })
                .then(function() { refresh(); })
                .catch(function() {});
        });
    }

    if (window.INITIAL_SENSORS_JSON) {
        renderCards(window.INITIAL_SENSORS_JSON);
    }
    setInterval(refresh, 5000);
})();
