(function() {
    var prio = 'all';
    var res = 'open';

    function applyFilters() {
        document.querySelectorAll('#alertsTable tbody tr').forEach(function(tr) {
            var p = tr.getAttribute('data-prio') || '';
            var r = tr.getAttribute('data-resolved') === '1';
            var okP = prio === 'all' || p === prio;
            var okR =
                res === 'all' ||
                (res === 'open' && !r) ||
                (res === 'done' && r);
            tr.style.display = okP && okR ? '' : 'none';
        });
    }

    document.querySelectorAll('#prioFilters .toggle-btn').forEach(function(btn) {
        btn.addEventListener('click', function() {
            document.querySelectorAll('#prioFilters .toggle-btn').forEach(function(b) {
                b.classList.remove('active');
            });
            btn.classList.add('active');
            prio = btn.getAttribute('data-prio') || 'all';
            applyFilters();
        });
    });

    document.querySelectorAll('#resFilters .toggle-btn').forEach(function(btn) {
        btn.addEventListener('click', function() {
            document.querySelectorAll('#resFilters .toggle-btn').forEach(function(b) {
                b.classList.remove('active');
            });
            btn.classList.add('active');
            res = btn.getAttribute('data-res') || 'open';
            applyFilters();
        });
    });

    document.querySelectorAll('.resolve-btn').forEach(function(btn) {
        btn.addEventListener('click', function() {
            var id = btn.getAttribute('data-id');
            fetch('/api/alerts/' + id + '/resolve', { method: 'PUT' })
                .then(function(r) { return r.json(); })
                .then(function(data) {
                    if (data.ok) window.location.reload();
                })
                .catch(function() {});
        });
    });

    var modal = document.getElementById('alertModal');
    var openBtn = document.getElementById('btnOpenAlert');
    var cancelBtn = document.getElementById('btnCancelAlert');
    if (modal && openBtn) {
        openBtn.addEventListener('click', function() {
            modal.classList.add('show');
        });
    }
    if (modal && cancelBtn) {
        cancelBtn.addEventListener('click', function() {
            modal.classList.remove('show');
        });
    }
    if (modal) {
        modal.addEventListener('click', function(ev) {
            if (ev.target === modal) modal.classList.remove('show');
        });
    }

    applyFilters();
})();
