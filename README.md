# Agri Learning Platform
### Agricultural Learning Management System (LMS)

A production-standard web-based LMS for indigenous and modern
agricultural education. Learners enroll in courses, progress
through modules, watch videos, read materials, and submit
assignments. Admins manage all content and grade learners.

---

## Tech Stack

| Layer       | Technology                          |
|-------------|-------------------------------------|
| Frontend    | HTML5 · Pure CSS3 · Vanilla JS      |
| Backend     | Python · Flask                      |
| Database    | PostgreSQL · SQLAlchemy · Migrate   |
| Auth        | Flask-Login · Werkzeug hashing      |
| Security    | Flask-WTF CSRF · RBAC               |

---

## Quick Start

```bash
# 1. Clone
git clone <repo-url>
cd Agri_LMS

# 2. Virtual environment
python -m venv venv
venv\Scripts\Activate.ps1      # Windows PowerShell

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
# Edit .env — set DATABASE_URL and SECRET_KEY

# 5. Create database
createdb agri_lms_db

# 6. Run migrations
flask db init
flask db migrate -m "Initial schema"
flask db upgrade

# 7. Run
flask run