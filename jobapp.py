from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import sqlite3
import hashlib
import webbrowser
import threading
import smtplib
import random
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)
app.secret_key = "getjob_secret_key_2024"
DB_PATH = "database.db"

# ── Email config (Gmail) ──────────────────────────────────────────────────────
EMAIL_ADDRESS  = "smartstudentmanager@gmail.com"
EMAIL_PASSWORD = "lksnrfilwiqfdgrt"
OTP_EXPIRY_SECONDS = 300
# ─────────────────────────────────────────────────────────────────────────────

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_skills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            skill TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS applied_jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            job_title TEXT NOT NULL,
            company TEXT NOT NULL,
            portal TEXT NOT NULL,
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    conn.commit()
    conn.close()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def generate_otp():
    return str(random.randint(100000, 999999))

def send_otp_email(to_email, name, otp):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Your GetJob OTP — Verify Your Email"
    msg["From"]    = EMAIL_ADDRESS
    msg["To"]      = to_email

    html = f"""
    <div style="font-family:Arial,sans-serif;max-width:480px;margin:auto;
                border:1px solid #e0e0e0;border-radius:10px;overflow:hidden;">
      <div style="background:#1a73e8;padding:24px;text-align:center;">
        <h1 style="color:#fff;margin:0;font-size:28px;">Get<span style="color:#ffd700;">Job</span></h1>
      </div>
      <div style="padding:32px;">
        <p style="font-size:16px;color:#333;">Hi <strong>{name}</strong>,</p>
        <p style="color:#555;">Use the OTP below to complete your registration.
           It expires in <strong>5 minutes</strong>.</p>
        <div style="text-align:center;margin:28px 0;">
          <span style="font-size:40px;font-weight:bold;letter-spacing:10px;
                       color:#1a73e8;background:#f0f6ff;padding:16px 28px;
                       border-radius:8px;">{otp}</span>
        </div>
        <p style="color:#999;font-size:13px;">
          If you didn't request this, please ignore this email.
        </p>
      </div>
      <div style="background:#f5f5f5;padding:12px;text-align:center;
                  font-size:12px;color:#aaa;">
        © 2024 GetJob Portal
      </div>
    </div>
    """
    msg.attach(MIMEText(html, "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.sendmail(EMAIL_ADDRESS, to_email, msg.as_string())


# ── Skills & Job Data ─────────────────────────────────────────────────────────

ALL_SKILLS = [
    "Python", "HTML", "CSS", "Bootstrap", "JavaScript",
    "SQL", "Flask", "Django", "Java", "React",
    "Node.js", "PHP", "MySQL", "MongoDB", "Git"
]

JOB_DB = [
    {"title": "Python Developer", "company": "Infosys", "location": "Bangalore", "exp": "0-2 yrs", "salary": "3-6 LPA", "skills": ["Python", "SQL", "Flask"], "portal": "LinkedIn", "link": "https://linkedin.com/jobs/search/?keywords=python+developer"},
    {"title": "Frontend Developer", "company": "TCS", "location": "Hyderabad", "exp": "0-2 yrs", "salary": "3-5 LPA", "skills": ["HTML", "CSS", "JavaScript", "Bootstrap"], "portal": "Naukri", "link": "https://naukri.com/python-jobs"},
    {"title": "Web Developer (Fresher)", "company": "Wipro", "location": "Chennai", "exp": "0-1 yrs", "salary": "3-4.5 LPA", "skills": ["HTML", "CSS", "JavaScript", "Bootstrap", "Python"], "portal": "Glassdoor", "link": "https://glassdoor.com/Job/web-developer-jobs"},
    {"title": "SQL / Database Analyst", "company": "HCL", "location": "Noida", "exp": "0-2 yrs", "salary": "3-5 LPA", "skills": ["SQL", "MySQL", "Python"], "portal": "Indeed", "link": "https://indeed.com/q-SQL-jobs.html"},
    {"title": "Junior Python Developer", "company": "Cognizant", "location": "Mumbai", "exp": "0-2 yrs", "salary": "4-6 LPA", "skills": ["Python", "Flask", "SQL", "HTML"], "portal": "LinkedIn", "link": "https://linkedin.com/jobs/search/?keywords=junior+python"},
    {"title": "UI Developer", "company": "Tech Mahindra", "location": "Pune", "exp": "0-2 yrs", "salary": "3-5 LPA", "skills": ["HTML", "CSS", "Bootstrap", "JavaScript"], "portal": "Naukri", "link": "https://naukri.com/ui-developer-jobs"},
    {"title": "Full Stack Trainee", "company": "Accenture", "location": "Bangalore", "exp": "0-1 yrs", "salary": "3.5-5 LPA", "skills": ["HTML", "CSS", "JavaScript", "Python", "SQL"], "portal": "Glassdoor", "link": "https://glassdoor.com/Job/full-stack-jobs"},
    {"title": "Backend Developer (Python)", "company": "Mphasis", "location": "Hyderabad", "exp": "0-2 yrs", "salary": "4-7 LPA", "skills": ["Python", "Django", "Flask", "SQL", "MySQL"], "portal": "Indeed", "link": "https://indeed.com/q-Python-Backend-jobs.html"},
    {"title": "Web Designer", "company": "Byju's", "location": "Bangalore", "exp": "0-2 yrs", "salary": "3-4 LPA", "skills": ["HTML", "CSS", "Bootstrap", "JavaScript"], "portal": "LinkedIn", "link": "https://linkedin.com/jobs/search/?keywords=web+designer"},
    {"title": "Data Entry + SQL", "company": "Capgemini", "location": "Chennai", "exp": "0-1 yrs", "salary": "2.5-4 LPA", "skills": ["SQL", "MySQL", "Python"], "portal": "Naukri", "link": "https://naukri.com/sql-jobs"},
    {"title": "PHP + MySQL Developer", "company": "LTIMindtree", "location": "Pune", "exp": "0-2 yrs", "salary": "3-5 LPA", "skills": ["PHP", "MySQL", "HTML", "CSS", "JavaScript"], "portal": "Indeed", "link": "https://indeed.com/q-PHP-Developer-jobs.html"},
    {"title": "JavaScript Developer", "company": "Zoho", "location": "Chennai", "exp": "0-2 yrs", "salary": "4-7 LPA", "skills": ["JavaScript", "HTML", "CSS", "Bootstrap"], "portal": "Glassdoor", "link": "https://glassdoor.com/Job/javascript-developer-jobs"},
    {"title": "Django Developer (Fresher)", "company": "Freshworks", "location": "Chennai", "exp": "0-1 yrs", "salary": "4-6 LPA", "skills": ["Python", "Django", "SQL", "HTML", "CSS"], "portal": "LinkedIn", "link": "https://linkedin.com/jobs/search/?keywords=django+developer"},
    {"title": "React + Bootstrap UI Dev", "company": "Razorpay", "location": "Bangalore", "exp": "0-2 yrs", "salary": "5-8 LPA", "skills": ["JavaScript", "Bootstrap", "HTML", "CSS", "React"], "portal": "Naukri", "link": "https://naukri.com/react-developer-jobs"},
    {"title": "Trainee Software Engineer", "company": "Mindtree", "location": "Bangalore", "exp": "0 yrs (Fresher)", "salary": "3-4.5 LPA", "skills": ["Python", "SQL", "HTML", "CSS", "JavaScript", "Git"], "portal": "Indeed", "link": "https://indeed.com/q-Software-Trainee-jobs.html"},
]

def get_matching_jobs(skills):
    if not skills:
        return []
    matched = []
    for job in JOB_DB:
        match_count = sum(1 for s in job["skills"] if s in skills)
        if match_count > 0:
            job_copy = dict(job)
            job_copy["match_count"] = match_count
            job_copy["match_percent"] = round((match_count / len(job["skills"])) * 100)
            job_copy["matched_skills"] = [s for s in job["skills"] if s in skills]
            job_copy["other_skills"] = [s for s in job["skills"] if s not in skills]
            matched.append(job_copy)
    matched.sort(key=lambda x: x["match_percent"], reverse=True)
    return matched


# ── Routes ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("skills"))
    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name     = request.form.get("name", "").strip()
        email    = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm  = request.form.get("confirm_password", "")

        if not name or not email or not password:
            flash("All fields are required.", "error")
            return render_template("register.html")
        if len(password) < 6:
            flash("Password must be at least 6 characters.", "error")
            return render_template("register.html")
        if password != confirm:
            flash("Passwords do not match.", "error")
            return render_template("register.html")

        conn = get_db()
        existing = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
        conn.close()
        if existing:
            flash("Email already registered. Please login.", "error")
            return render_template("register.html")

        otp = generate_otp()
        try:
            send_otp_email(email, name, otp)
        except Exception as e:
            flash(f"Could not send OTP. Check your email config. ({e})", "error")
            return render_template("register.html")

        session["pending_reg"] = {
            "name":     name,
            "email":    email,
            "password": hash_password(password),
            "otp":      otp,
            "sent_at":  time.time()
        }
        flash(f"OTP sent to {email}. Please check your inbox.", "success")
        return redirect(url_for("verify_otp"))

    return render_template("register.html")


@app.route("/verify-otp", methods=["GET", "POST"])
def verify_otp():
    pending = session.get("pending_reg")
    if not pending:
        return redirect(url_for("register"))

    if request.method == "POST":
        action = request.form.get("action", "verify")

        if action == "resend":
            otp = generate_otp()
            try:
                send_otp_email(pending["email"], pending["name"], otp)
                pending["otp"]     = otp
                pending["sent_at"] = time.time()
                session["pending_reg"] = pending
                flash("A new OTP has been sent to your email.", "success")
            except Exception as e:
                flash(f"Failed to resend OTP: {e}", "error")
            return render_template("verify_otp.html", email=pending["email"])

        entered = request.form.get("otp", "").strip()
        elapsed = time.time() - pending["sent_at"]

        if elapsed > OTP_EXPIRY_SECONDS:
            flash("OTP has expired. Please request a new one.", "error")
            return render_template("verify_otp.html", email=pending["email"])

        if entered != pending["otp"]:
            flash("Incorrect OTP. Please try again.", "error")
            return render_template("verify_otp.html", email=pending["email"])

        try:
            conn = get_db()
            conn.execute(
                "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
                (pending["name"], pending["email"], pending["password"])
            )
            conn.commit()
            conn.close()
        except sqlite3.IntegrityError:
            flash("Email already registered.", "error")
            session.pop("pending_reg", None)
            return redirect(url_for("login"))

        session.pop("pending_reg", None)
        flash("Account created successfully! Please login.", "success")
        return redirect(url_for("login"))

    return render_template("verify_otp.html", email=pending["email"])


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email    = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        conn = get_db()
        user = conn.execute(
            "SELECT * FROM users WHERE email = ? AND password = ?",
            (email, hash_password(password))
        ).fetchone()
        conn.close()
        if user:
            session["user_id"]   = user["id"]
            session["user_name"] = user["name"]
            return redirect(url_for("skills"))
        else:
            flash("Invalid email or password.", "error")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/skills", methods=["GET", "POST"])
def skills():
    if "user_id" not in session:
        return redirect(url_for("login"))
    if request.method == "POST":
        selected = request.form.getlist("skills")
        if not selected:
            flash("Please select at least one skill.", "error")
            return render_template("skills.html", all_skills=ALL_SKILLS, selected=[])
        conn = get_db()
        conn.execute("DELETE FROM user_skills WHERE user_id = ?", (session["user_id"],))
        for skill in selected:
            conn.execute(
                "INSERT INTO user_skills (user_id, skill) VALUES (?, ?)",
                (session["user_id"], skill)
            )
        conn.commit()
        conn.close()
        return redirect(url_for("jobs"))
    conn = get_db()
    saved = [row["skill"] for row in conn.execute(
        "SELECT skill FROM user_skills WHERE user_id = ?", (session["user_id"],)
    ).fetchall()]
    conn.close()
    return render_template("skills.html", all_skills=ALL_SKILLS, selected=saved)


@app.route("/jobs")
def jobs():
    if "user_id" not in session:
        return redirect(url_for("login"))
    conn = get_db()
    user_skills = [row["skill"] for row in conn.execute(
        "SELECT skill FROM user_skills WHERE user_id = ?", (session["user_id"],)
    ).fetchall()]
    applied = [row["job_title"] + row["company"] for row in conn.execute(
        "SELECT job_title, company FROM applied_jobs WHERE user_id = ?", (session["user_id"],)
    ).fetchall()]
    conn.close()
    if not user_skills:
        return redirect(url_for("skills"))
    portal_filter = request.args.get("portal", "All")
    matched_jobs  = get_matching_jobs(user_skills)
    portals       = ["All", "LinkedIn", "Naukri", "Glassdoor", "Indeed"]
    portal_counts = {p: sum(1 for j in matched_jobs if j["portal"] == p) for p in portals[1:]}
    portal_counts["All"] = len(matched_jobs)
    if portal_filter != "All":
        matched_jobs = [j for j in matched_jobs if j["portal"] == portal_filter]
    for job in matched_jobs:
        job["is_applied"] = (job["title"] + job["company"]) in applied
    return render_template("jobs.html", jobs=matched_jobs, user_skills=user_skills,
                           portals=portals, portal_counts=portal_counts,
                           active_portal=portal_filter, total_applied=len(applied))


@app.route("/apply_ajax", methods=["POST"])
def apply_ajax():
    if "user_id" not in session:
        return jsonify({"status": "error"}), 401
    data      = request.get_json()
    job_title = data.get("job_title")
    company   = data.get("company")
    portal    = data.get("portal")
    conn = get_db()
    existing = conn.execute(
        "SELECT id FROM applied_jobs WHERE user_id=? AND job_title=? AND company=?",
        (session["user_id"], job_title, company)
    ).fetchone()
    if not existing:
        conn.execute(
            "INSERT INTO applied_jobs (user_id, job_title, company, portal) VALUES (?, ?, ?, ?)",
            (session["user_id"], job_title, company, portal)
        )
        conn.commit()
    conn.close()
    return jsonify({"status": "success"})


@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))
    conn = get_db()
    applied = conn.execute(
        "SELECT * FROM applied_jobs WHERE user_id = ? ORDER BY applied_at DESC",
        (session["user_id"],)
    ).fetchall()
    skills = [row["skill"] for row in conn.execute(
        "SELECT skill FROM user_skills WHERE user_id = ?", (session["user_id"],)
    ).fetchall()]
    conn.close()
    return render_template("dashboard.html", applied=applied, skills=skills)


if __name__ == "__main__":
    init_db()
    threading.Timer(1.0, lambda: webbrowser.open("http://127.0.0.1:5000")).start()
    app.run(debug=False, use_reloader=False)
