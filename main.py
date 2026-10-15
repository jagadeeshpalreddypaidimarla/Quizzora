import os, sqlite3, secrets, hashlib, hmac, time, json, random
from pathlib import Path
from contextlib import contextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()
APP_DIR = Path(__file__).parent
DB_PATH = APP_DIR / "quizzora.db"
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "Ksallauddin81@gmail.com").strip().lower()
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")
SECRET_KEY = os.getenv("SECRET_KEY", "local-development-key-change-me")

app = FastAPI(title="Quizzora")
app.mount("/static", StaticFiles(directory=APP_DIR / "static"), name="static")

QUESTIONS = [
("What is one common use of an AI writing tool?", ["Repairing a keyboard","Writing or improving text","Charging a mobile phone","Printing money"], 1),
("In which year was Python first released?", ["1991","1995","1989","2000"], 0),
("What is a prompt in an AI tool?", ["A command or question given to the AI","A saved password","A computer virus","A type of hardware cable"], 0),
("What will be the output of this Python program? x=10; x=x+5; print(x)", ["5","105","15","10"], 2),
("What is a pitch in a hackathon?", ["A project presentation","A database","A sport activity","A coding error"], 0),
("Which information should you avoid sharing with an AI tool?", ["A general topic for discussion","A simple question","A public website address","Private passwords and sensitive personal information"], 3),
("What is the result of 10 % 3?", ["0.3","1","3","10"], 1),
("Who created Python?", ["Guido van Rossum","James Gosling","Bjarne Stroustrup","Dennis Ritchie"], 0),
("What is the type of the value 10.5?", ["float","bool","int","str"], 0),
("What is a variable?", ["A data type","A name that refers to a value","A symbol used only for comments","Constant"], 1),
("Which platform can deploy a frontend project directly from a GitHub repository?", ["Google AI Studio","MySQL","Notepad","Netlify"], 3),
("Which variable assignment stores a floating-point number?", ["floatage = 20.5",'marks = 85.5','name = "Rahul"',"passed = True"], 1),
('What is the output? num=0; if num%2==0: print("Even number") else: print("Odd number")', ["Odd number","Error","Even number","None"], 2),
("What file extension is generally used for Python files?", [".file",".python",".pyt",".py"], 3),
("Which of the following is an OpenAI product/tool?", ["ChatGPT","Gemini","Claude","Perplexity"], 0),
('What is the result of int("25")?', ["The integer 25","The Boolean True",'The string "25"',"The float 25.0"], 0),
("Which of the following is a valid variable name?", ["return","my-name","my_name","2name"], 2),
("What is a prototype?", ["A method of testing software","Final version of product","An early model of a product","A product design document"], 2),
("What is the output of print(bool(0))?", ["True","false","False"], 2),
("Which symbol starts a single-line comment in Python?", ["//","#","/*","--"], 1),
('Which value is a string in the program print("HelloWorld")?', ["HelloWorld",'"HelloWorld"',"print","string"], 1),
("What is an AI chatbot?", ["A type of computer keyboard","A device used only for printing documents","A programming language","A tool that can communicate with users using artificial intelligence"], 3),
("A website consists of", ["Database","Frontend","Backend","All of the above"], 3),
("Which variable assignment stores the integer 20?", ["age=20","age==20",'age="20"',"intage=20"], 0),
("What is the main purpose of Git?", ["Tracking changes in source code","Designing images","Creating websites only","Managing databases"], 0),
("Which type of programming language is Python?", ["Low-level, hardware-specific","Assembly-only","Markup-based","High-level, general-purpose"], 3),
("MVP stands for", ["Maximized viable product","Maximum viable product","Minimum viable product","Main viable product"], 2),
("What does the print() function do?", ["Displays output on the screen","Converts data types","Accepts user input","Defines a variable"], 0),
("What is the purpose of teamwork?", ["Combining different skills","Achieving a common goal","Sharing responsibilities","All of the above"], 3),
("What is List in Python?", ["List is an ordered and mutable collection that allows duplicates","List is an unordered and immutable collection","List is used to store a single value only","List is written with () brackets"], 0),
]

@contextmanager
def db():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    try:
        yield con
        con.commit()
    finally:
        con.close()

def hash_password(password, salt=None):
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 200_000)
    return salt.hex() + "$" + digest.hex()

def verify_password(password, stored):
    try:
        salt_hex, digest_hex = stored.split("$", 1)
        actual = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt_hex), 200_000).hex()
        return hmac.compare_digest(actual, digest_hex)
    except Exception:
        return False

def init_db():
    with db() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, username TEXT NOT NULL, email TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL, role TEXT NOT NULL DEFAULT 'student');
        CREATE TABLE IF NOT EXISTS quiz(id INTEGER PRIMARY KEY, title TEXT NOT NULL, code TEXT UNIQUE, active INTEGER NOT NULL DEFAULT 0, duration_seconds INTEGER NOT NULL DEFAULT 1800);
        CREATE TABLE IF NOT EXISTS questions(id INTEGER PRIMARY KEY, quiz_id INTEGER NOT NULL, prompt TEXT NOT NULL, options_json TEXT NOT NULL, correct_index INTEGER NOT NULL);
        CREATE TABLE IF NOT EXISTS attempts(id INTEGER PRIMARY KEY, quiz_id INTEGER NOT NULL, user_id INTEGER NOT NULL, started_at REAL NOT NULL, deadline REAL NOT NULL, question_order TEXT NOT NULL, answers_json TEXT NOT NULL DEFAULT '{}', submitted_at REAL, score INTEGER);
        """)
        if ADMIN_PASSWORD and not c.execute("SELECT id FROM users WHERE email=?", (ADMIN_EMAIL,)).fetchone():
            c.execute("INSERT INTO users(username,email,password_hash,role) VALUES(?,?,?,'admin')",
                      ("Quizzora Admin", ADMIN_EMAIL, hash_password(ADMIN_PASSWORD)))
        q = c.execute("SELECT id FROM quiz LIMIT 1").fetchone()
        if not q:
            cur = c.execute("INSERT INTO quiz(title, duration_seconds) VALUES(?,1800)", ("Quizzora — Quiz 1",))
            qid = cur.lastrowid
            for prompt, options, correct in QUESTIONS:
                c.execute("INSERT INTO questions(quiz_id,prompt,options_json,correct_index) VALUES(?,?,?,?)",
                          (qid, prompt, json.dumps(options), correct))
init_db()

class Register(BaseModel):
    username: str = Field(min_length=2, max_length=40)
    email: str
    password: str = Field(min_length=8, max_length=128)
class Login(BaseModel):
    email: str
    password: str
    portal: str = "student"
class CodeIn(BaseModel):
    code: str
class AnswerIn(BaseModel):
    answers: dict[str, int]

def current_user(request: Request):
    token = request.cookies.get("q_session")
    if not token or "." not in token:
        return None
    uid_s, sig = token.split(".",1)
    expected = hmac.new(SECRET_KEY.encode(), uid_s.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(sig, expected):
        return None
    with db() as c:
        row = c.execute("SELECT id,username,email,role FROM users WHERE id=?", (uid_s,)).fetchone()
        return dict(row) if row else None

def require_user(request, role=None):
    u = current_user(request)
    if not u: raise HTTPException(401, "Please log in.")
    if role and u["role"] != role: raise HTTPException(403, "Not authorized.")
    return u

def safe_question(row):
    return {"id": row["id"], "prompt": row["prompt"], "options": json.loads(row["options_json"])}

@app.get("/", response_class=HTMLResponse)
def home():
    return (APP_DIR / "static" / "index.html").read_text(encoding="utf-8")

@app.get("/api/me")
def me(request: Request):
    return {"user": current_user(request)}

@app.post("/api/register")
def register(data: Register, request: Request):
    email = data.email.strip().lower()
    if "@" not in email or "." not in email.split("@")[-1]:
        raise HTTPException(400, "Enter a valid email address.")
    if email == ADMIN_EMAIL:
        raise HTTPException(400, "This email is reserved for the administrator.")
    with db() as c:
        try:
            c.execute("INSERT INTO users(username,email,password_hash,role) VALUES(?,?,?,'student')",
                      (data.username.strip(), email, hash_password(data.password)))
        except sqlite3.IntegrityError:
            raise HTTPException(409, "An account with this email already exists.")
    # Registration deliberately does not create a login session. The student must log in next.
    return {"ok": True, "message": "Account created. Please log in with your email and password."}

def set_session(uid):
    sig = hmac.new(SECRET_KEY.encode(), str(uid).encode(), hashlib.sha256).hexdigest()
    response = JSONResponse({"ok": True})
    response.set_cookie("q_session", f"{uid}.{sig}", httponly=True, samesite="lax")
    return response

@app.post("/api/login")
def login(data: Login):
    with db() as c:
        user = c.execute("SELECT id,password_hash,role FROM users WHERE email=?", (data.email.strip().lower(),)).fetchone()
    if not user or not verify_password(data.password, user["password_hash"]):
        raise HTTPException(401, "Email or password is incorrect.")
    if data.portal not in ("admin", "student") or user["role"] != data.portal:
        raise HTTPException(403, "This account cannot sign in through that portal.")
    return set_session(user["id"])

@app.post("/api/logout")
def logout():
    r = JSONResponse({"ok": True}); r.delete_cookie("q_session"); return r

@app.post("/api/admin/code")
def create_code(request: Request):
    require_user(request, "admin")
    code = secrets.token_urlsafe(5).replace("-", "").replace("_", "").upper()[:8]
    with db() as c:
        q = c.execute("SELECT id FROM quiz LIMIT 1").fetchone()
        c.execute("UPDATE quiz SET code=?, active=1 WHERE id=?", (code, q["id"]))
    return {"code": code, "message": "Quiz is now open."}

@app.post("/api/admin/close")
def close_quiz(request: Request):
    require_user(request, "admin")
    with db() as c:
        c.execute("UPDATE quiz SET active=0 WHERE id=(SELECT id FROM quiz LIMIT 1)")
    return {"ok": True}

@app.get("/api/admin/results")
def admin_results(request: Request):
    require_user(request, "admin")
    with db() as c:
        rows = c.execute("""SELECT u.username,u.email,a.score,a.submitted_at,a.started_at
          FROM attempts a JOIN users u ON u.id=a.user_id WHERE a.submitted_at IS NOT NULL
          ORDER BY a.score DESC, a.submitted_at ASC""").fetchall()
        quiz = c.execute("SELECT active,code FROM quiz LIMIT 1").fetchone()
    results = [dict(r) for r in rows]
    return {"results": results, "participants": len(results), "highest": max([r["score"] for r in results], default=0),
            "active": bool(quiz["active"]), "code": quiz["code"]}

@app.post("/api/join")
def join(data: CodeIn, request: Request):
    u = require_user(request, "student")
    with db() as c:
        quiz = c.execute("SELECT * FROM quiz LIMIT 1").fetchone()
        if not quiz or not quiz["active"] or not quiz["code"] or not hmac.compare_digest(data.code.strip().upper(), quiz["code"]):
            raise HTTPException(400, "Invalid code or quiz is not open.")
        old = c.execute("SELECT id,submitted_at FROM attempts WHERE quiz_id=? AND user_id=? ORDER BY id DESC LIMIT 1",
                        (quiz["id"],u["id"])).fetchone()
        if old:
            if old["submitted_at"]: raise HTTPException(409, "You have already completed this quiz.")
            attempt_id = old["id"]
            attempt = c.execute("SELECT * FROM attempts WHERE id=?", (attempt_id,)).fetchone()
        else:
            qrows = c.execute("SELECT id FROM questions WHERE quiz_id=? ORDER BY id", (quiz["id"],)).fetchall()
            order = [r["id"] for r in qrows]; random.SystemRandom().shuffle(order)
            now = time.time()
            cur = c.execute("INSERT INTO attempts(quiz_id,user_id,started_at,deadline,question_order,answers_json) VALUES(?,?,?,?,?,?)",
                            (quiz["id"],u["id"],now,now+quiz["duration_seconds"],json.dumps(order),"{}"))
            attempt = c.execute("SELECT * FROM attempts WHERE id=?", (cur.lastrowid,)).fetchone()
    with db() as c:
        qmap = {r["id"]: r for r in c.execute("SELECT * FROM questions WHERE quiz_id=?", (quiz["id"],)).fetchall()}
    return {"attempt_id": attempt["id"], "deadline": attempt["deadline"], "questions":[safe_question(qmap[i]) for i in json.loads(attempt["question_order"])],
            "answers": json.loads(attempt["answers_json"]), "submitted": bool(attempt["submitted_at"])}

@app.get("/api/attempt")
def get_attempt(request: Request):
    u = require_user(request, "student")
    with db() as c:
        a = c.execute("SELECT * FROM attempts WHERE user_id=? ORDER BY id DESC LIMIT 1", (u["id"],)).fetchone()
        if not a: return {"attempt": None}
        qrows = c.execute("SELECT * FROM questions WHERE quiz_id=?", (a["quiz_id"],)).fetchall()
        qmap = {r["id"]: r for r in qrows}
        questions = [safe_question(qmap[i]) for i in json.loads(a["question_order"])]
    if not a["submitted_at"] and time.time() >= a["deadline"]:
        finalize_attempt(a["id"])
        with db() as c: a = c.execute("SELECT * FROM attempts WHERE id=?", (a["id"],)).fetchone()
    return {"attempt_id":a["id"],"deadline":a["deadline"],"questions":questions,"answers":json.loads(a["answers_json"]),
            "submitted":bool(a["submitted_at"]), "score":a["score"]}

def finalize_attempt(attempt_id, answers=None):
    with db() as c:
        a = c.execute("SELECT * FROM attempts WHERE id=?", (attempt_id,)).fetchone()
        if not a or a["submitted_at"]: return a["score"] if a else None
        stored = json.loads(a["answers_json"])
        if answers is not None: stored.update(answers)
        qrows = c.execute("SELECT id,correct_index FROM questions WHERE quiz_id=?", (a["quiz_id"],)).fetchall()
        correct = {str(r["id"]):r["correct_index"] for r in qrows}
        score = sum(1 for qid, val in stored.items() if qid in correct and val == correct[qid])
        now = time.time()
        c.execute("UPDATE attempts SET answers_json=?,score=?,submitted_at=? WHERE id=? AND submitted_at IS NULL",
                  (json.dumps(stored),score,now,attempt_id))
        return score

@app.post("/api/answers")
def save_answers(data: AnswerIn, request: Request):
    u = require_user(request, "student")
    with db() as c:
        a = c.execute("SELECT * FROM attempts WHERE user_id=? ORDER BY id DESC LIMIT 1", (u["id"],)).fetchone()
        if not a: raise HTTPException(404, "No active attempt.")
        if a["submitted_at"]: return {"submitted":True,"score":a["score"]}
        if time.time() >= a["deadline"]:
            score = finalize_attempt(a["id"]); return {"submitted":True,"score":score}
        order = set(json.loads(a["question_order"]))
        clean = {str(k):v for k,v in data.answers.items() if str(k).isdigit() and int(k) in order and isinstance(v,int) and v >= 0}
        options_count = {}
        for r in c.execute("SELECT id,options_json FROM questions WHERE quiz_id=?", (a["quiz_id"],)).fetchall():
            options_count[str(r["id"])] = len(json.loads(r["options_json"]))
        clean = {k:v for k,v in clean.items() if k in options_count and v < options_count[k]}
        old = json.loads(a["answers_json"]); old.update(clean)
        c.execute("UPDATE attempts SET answers_json=? WHERE id=?", (json.dumps(old),a["id"]))
    return {"ok":True}

@app.post("/api/submit")
def submit(request: Request):
    u = require_user(request, "student")
    with db() as c:
        a = c.execute("SELECT id,deadline,submitted_at,score FROM attempts WHERE user_id=? ORDER BY id DESC LIMIT 1", (u["id"],)).fetchone()
    if not a: raise HTTPException(404, "No attempt found.")
    if a["submitted_at"]: return {"submitted":True,"score":a["score"]}
    score = finalize_attempt(a["id"])
    return {"submitted":True,"score":score}

@app.get("/api/my-result")
def my_result(request: Request):
    u = require_user(request, "student")
    with db() as c:
        a = c.execute("SELECT score,submitted_at FROM attempts WHERE user_id=? ORDER BY id DESC LIMIT 1", (u["id"],)).fetchone()
    if not a or not a["submitted_at"]: return {"submitted":False}
    return {"submitted":True,"score":a["score"],"total":30,"percentage":round(a["score"]/30*100,2)}
