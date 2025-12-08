# Flask + React Starter (Minimal for Beginners)

This is a minimal starter scaffold for a Flask backend and a React frontend (Vite), intended for new developers learning both frameworks.

Project structure (minimal):

- `backend/` — Flask app and simple API
- `frontend/` — React app (Vite)

Quick start — Backend (local, no Docker)

```powershell
# from repo root
Set-Location c:\Users\HAVOC\OneDrive\Desktop\cse471\backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
# create instance folder used by SQLite
if (-not (Test-Path instance)) { mkdir instance }
# run the app (development)
python manage.py run
```

Open `http://localhost:5000/api/v1/ping` to verify the backend responds.

Quick start — Frontend (Vite dev server)

```powershell
Set-Location c:\Users\HAVOC\OneDrive\Desktop\cse471\frontend
npm install
npm run dev
```

Open the Vite URL shown in the terminal (usually `http://localhost:5173`) and use the app's UI to call the backend.

Migrations (Flask-Migrate)

If you want to persist models to a database and manage schema changes, use `Flask-Migrate`. From the `backend` folder run:

```powershell
Set-Location c:\Users\HAVOC\OneDrive\Desktop\cse471\backend
.\venv\Scripts\Activate.ps1
# set FLASK_APP for the manage script
$env:FLASK_APP = 'manage.py'
# initialize migrations folder (only once)
python manage.py db init
# create migration based on models
python manage.py db migrate -m "initial"
# apply migration to the database
python manage.py db upgrade
```

Notes:

- If you use SQLite (default in `.env.example`), ensure the `instance/` directory exists before running `db upgrade` so the DB file can be created.
- For Postgres or other production DBs, set `DATABASE_URL` in your environment before running migration commands.

Next steps (suggested):

- Learn Flask basics: add routes, models, and use `flask_sqlalchemy` for persistence.
- Learn React basics: create components, pages, and call the backend with `axios`.
- When comfortable, we can add migrations, tests, and Docker for deployment.

If you want, I can now:

- Initialize a git repository and make an initial commit
- Add migrations and a sample resource (CRUD endpoints)
- Implement refresh tokens and safer auth cookie flow
