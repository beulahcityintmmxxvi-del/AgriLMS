# =============================================================
# Agri LMS — Gunicorn Production Configuration
# =============================================================
# File    : gunicorn.conf.py
# Usage   : gunicorn -c gunicorn.conf.py run:app
# =============================================================

import multiprocessing

# ── Server socket ─────────────────────────────────────────────
bind            = '0.0.0.0:5000'
backlog         = 2048

# ── Worker processes ──────────────────────────────────────────
workers         = multiprocessing.cpu_count() * 2 + 1
worker_class    = 'sync'
worker_connections = 1000
timeout         = 120
keepalive       = 5

# ── Process naming ────────────────────────────────────────────
proc_name       = 'agri_lms'

# ── Logging ───────────────────────────────────────────────────
accesslog       = '-'        # stdout
errorlog        = '-'        # stderr
loglevel        = 'info'
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s'

# ── Security ──────────────────────────────────────────────────
limit_request_line   = 4096
limit_request_fields = 100