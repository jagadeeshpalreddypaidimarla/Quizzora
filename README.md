# Quizzora — free local quiz website

A working local quiz app using FastAPI + SQLite + plain HTML/CSS/JavaScript. No AI-builder credits or paid database required.

## Run on Windows (quickest)\n1. Extract the ZIP.\n2. Double-click `start_quizzora.bat`. The first run installs dependencies and creates `.env`.\n3. In the Notepad window, set `ADMIN_PASSWORD` to a strong password and `SECRET_KEY` to a long random secret, save, and close Notepad.\n4. Double-click `start_quizzora.bat` again.\n5. Open http://127.0.0.1:8000 in your browser. Keep the terminal window open.\n\n## Manual setup
1. Install Python 3.12+ from https://www.python.org/downloads/ if needed.
2. Extract this ZIP to a folder, open Command Prompt/PowerShell in that folder.
3. Create a virtual environment:
   `py -m venv .venv`
4. Activate it:
   PowerShell: `.venv\Scripts\Activate.ps1`
   Command Prompt: `.venv\Scripts\activate.bat`
5. Install packages: `pip install -r requirements.txt`
6. Copy `.env.example` to `.env`, then change `ADMIN_PASSWORD` and `SECRET_KEY`.
7. Start the website: `uvicorn main:app --reload`
8. Open http://127.0.0.1:8000

## Login flow\n- The landing page has separate Student Login and Admin Portal Login buttons.\n- Student account creation does not log the student in automatically. After registration, the student is taken to the Student Login page and must enter their password.\n- Admin accounts can sign in only through Admin Portal Login; student accounts can sign in only through Student Login.\n\n## Features
- Separate admin and student sign-in experiences
- Student self-registration (username, email, password)
- Admin creates a quiz access code and opens/closes the quiz
- 30-minute server-enforced deadline
- 30 supplied questions, independently shuffled per student
- Automatic scoring (1 point per correct answer)
- Student sees only their own score; admin sees results/leaderboard
- SQLite persistence

## Important
This is a local application. To let students use it from their own devices, deploy it to a hosting service and configure HTTPS and a strong secret. Do not publish `.env`. The administrator password is configured in `.env`, not embedded in frontend code. This project does not bypass Lovable credits; it is an alternative you can run for free locally.
