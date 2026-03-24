from flask import Flask, render_template, request, redirect, session, send_file
import sqlite3
import os
import qrcode
from datetime import datetime
from reportlab.platypus import SimpleDocTemplate, Paragraph, Image, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import letter
from datetime import datetime
import sqlite3
from flask import render_template
import re

app = Flask(__name__)
app.secret_key = "secret123"

# Create uploads folder
if not os.path.exists("static/uploads"):
    os.makedirs("static/uploads")


print("✅ Table created")
# ---------- DATABASE SETUP ----------
def init_db():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id TEXT UNIQUE,
        name TEXT,
        password TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS requests (
    student_id TEXT,
    parent_name TEXT,
    parent_photo TEXT,
    reason TEXT,
    status TEXT DEFAULT 'Pending',
    scanned INTEGER DEFAULT 0,
    out_time TEXT
    )
    """)

    conn.commit()
    conn.close()

init_db()

# ---------- HOME ----------
@app.route("/")
def index():
    return render_template("index.html")

# ---------- STUDENT LOGIN ----------
@app.route("/student_login", methods=["GET", "POST"])
def student_login():

    if request.method == "POST":

        student_id = request.form.get("student_id", "").strip().upper()
        password = request.form.get("password", "").strip()

        # ✅ Validate ID format
        if not re.match(r"^N\d{6}$", student_id):
            return "❌ Invalid Student ID format! Use N220510"

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM students WHERE student_id=?", (student_id,))
        student = cursor.fetchone()

        conn.close()

        print("DEBUG → Entered:", student_id, password)
        print("DEBUG → DB:", student)

        if student:
            db_password = str(student[3]).strip()

            if db_password == password:
                session["student_id"] = student_id
                return redirect("/student_dashboard")
            else:
                return "❌ Wrong Password"
        else:
            return "❌ Student ID not found"

    return render_template("student_login.html")

# ---------- STUDENT DASHBOARD ----------
@app.route("/student_dashboard", methods=["GET", "POST"])
def student_dashboard():

    if "student_id" not in session:
        return redirect("/student_login")

    student_id = session["student_id"]

    # Submit new request
    if request.method == "POST":

        parent_name = request.form.get("parent_name")
        reason = request.form.get("reason")
        photo = request.files["parent_photo"]

        filename = photo.filename
        photo.save(os.path.join("static/uploads", filename))

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        cursor.execute("""
        INSERT INTO requests (student_id, parent_name, parent_photo, reason)
        VALUES (?, ?, ?, ?)
        """, (student_id, parent_name, filename, reason))

        conn.commit()
        conn.close()

        return redirect("/student_dashboard")

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM requests WHERE student_id=?", (student_id,))
    requests_data = cursor.fetchall()

    conn.close()

    return render_template("student_dashboard.html", requests=requests_data)

# ---------- WARDEN LOGIN ----------
@app.route("/warden_login", methods=["GET", "POST"])
def warden_login():

    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")

        if username == "warden" and password == "admin123":
            session["warden"] = True
            return redirect("/warden_dashboard")
        else:
            return "Invalid Warden Credentials"

    return render_template("warden_login.html")

# ---------- WARDEN DASHBOARD ----------
@app.route("/warden_dashboard")
def warden_dashboard():

    if "warden" not in session:
        return redirect("/warden_login")

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM requests")
    all_requests = cursor.fetchall()

    conn.close()

    return render_template("warden_dashboard.html", requests=all_requests)

# ---------- DELETE REQUEST ----------
@app.route("/delete_request/<int:id>")
def delete_request(id):

    if "warden" not in session:
        return redirect("/warden_login")

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("DELETE FROM requests WHERE id=?", (id,))

    conn.commit()
    conn.close()

    return redirect("/warden_dashboard")

# ---------- APPROVE / REJECT ----------
@app.route("/update_status/<int:id>/<status>")
def update_status(id, status):

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("UPDATE requests SET status=? WHERE id=?", (status, id))
    conn.commit()

    if status == "Approved":

        verify_url = f"http://127.0.0.1:5000/verify/{id}"

        img = qrcode.make(verify_url)
        img.save(f"static/uploads/qr_{id}.png")

    conn.close()

    return redirect("/warden_dashboard")

# ---------- VERIFY QR ----------
@app.route("/verify/<int:id>")
def verify(id):

    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM requests WHERE id=?", (id,))
    request_data = cursor.fetchone()

    # ❌ Invalid QR
    if not request_data:
        conn.close()
        return "Invalid QR ❌"

    # ❌ Not approved
    if request_data["status"] != "Approved":
        conn.close()
        return render_template("verify.html",
                               data=request_data,
                               message="Not Approved ❌")

    # ❌ Already used → EXPIRED
    if request_data["scanned"] == 1:
        conn.close()
        return render_template("verify.html",
                               data=request_data,
                               message="QR Code Expired ❌")

    # ✅ First scan → allow exit
    out_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
    UPDATE requests
    SET scanned=1, out_time=?
    WHERE id=?
    """, (out_time, id))

    conn.commit()
    conn.close()

    return render_template("verify.html",
                           data=request_data,
                           message="Student Exit Recorded ✅",
                           time=out_time)

# ---------- DOWNLOAD OUTPASS ----------
@app.route("/download_pass/<int:id>")
def download_pass(id):

    qr_path = f"static/uploads/qr_{id}.png"

    # Check if QR exists
    if not os.path.exists(qr_path):
        return "QR not generated yet. Please wait for approval."

    return send_file(qr_path, as_attachment=True)

# ---------- LOGOUT ----------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ---------- SECURITY PAGE ----------
@app.route("/security")
def security_scanner():
    return render_template("security_scanner.html")

if __name__ == "__main__":
    app.run(debug=True)