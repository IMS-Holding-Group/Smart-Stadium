(function() {
    var msg = document.getElementById('coolingMsg');
    function show(t) {
        if (msg) msg.textContent = t || '';
    }

    function updateRow(seatId, level) {
        var btn0 = document.querySelector('.cool-btn[data-seat="' + seatId + '"]');
        if (!btn0) return;
        var tr = btn0.closest('tr');
        if (!tr) return;
        var statusCell = tr.querySelector('.cool-status');
        if (statusCell) statusCell.textContent = level;
        tr.querySelectorAll('.cool-btn').forEach(function(b) {
            b.classList.toggle('on', b.getAttribute('data-level') === level);
        });
    }

    document.querySelectorAll('.cool-btn').forEach(function(btn) {
        btn.addEventListener('click', function() {
            var seatId = btn.getAttribute('data-seat');
            var level = btn.getAttribute('data-level');
            fetch('/api/cooling/set', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ seat_id: Number(seatId), level: level })
            })
                .then(function(r) { return r.json(); })
                .then(function(data) {
                    if (data.ok) {
                        updateRow(String(data.seat_id), data.cooling_status);
                        show('تم التحديث.');
                    } else {
                        show(data.error || 'خطأ');
                    }
                })
                .catch(function() { show('خطأ في الاتصال.'); });
        });
    });

    document.querySelectorAll('.set-all').forEach(function(btn) {
        btn.addEventListener('click', function() {
            var level = btn.getAttribute('data-level');
            fetch('/api/cooling/set-all', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ level: level })
            })
                .then(function(r) { return r.json(); })
                .then(function(data) {
                    if (data.ok) {
                        document.querySelectorAll('.cool-btn').forEach(function(b) {
                            var tr = b.closest('tr');
                            var st = tr ? tr.querySelector('.cool-status') : null;
                            if (st) st.textContent = level;
                            b.classList.toggle('on', b.getAttribute('data-level') === level);
                        });
                        show('تم تطبيق المستوى على كل المقاعد.');
                    } else {
                        show(data.error || 'خطأ');
                    }
                })
                .catch(function() { show('خطأ في الاتصال.'); });
        });
    });

    var filter = document.getElementById('blockFilter');
    if (filter) {
        filter.addEventListener('change', function() {
            var v = filter.value;
            document.querySelectorAll('#coolingTable tbody tr').forEach(function(tr) {
                var b = tr.getAttribute('data-block');
                if (!b) return;
                tr.style.display = v === 'all' || b === v ? '' : 'none';
            });
        });
    }
})();
