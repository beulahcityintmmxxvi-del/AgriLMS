# =============================================================
# Agri LMS — Application Runner
# =============================================================
# File    : run.py
# Purpose : Entry point for running the Flask development
#           server and for Gunicorn in production.
# Usage   : flask run  |  python run.py  |  gunicorn run:app
# =============================================================

import os
from app import create_app

# Create the application using the environment-specified config
app = create_app(os.environ.get('FLASK_ENV', 'development'))

if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=5050,
        debug=app.config.get('DEBUG', True)
    )