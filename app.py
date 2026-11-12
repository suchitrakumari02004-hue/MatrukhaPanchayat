
import os
import uuid
import sqlite3
import requests

from functools import wraps
from datetime import datetime

from flask import (
    Flask, render_template, request, redirect,
    url_for, session, flash, jsonify, abort
)

from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename


app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "panchayat.db")

app.secret_key = os.environ.get(
    "SECRET_KEY",
    "change-this-secret-key-before-deployment"
)

UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp", "pdf"}

OLLAMA_URL = os.environ.get(
    "OLLAMA_URL",
    "http://localhost:11434/api/chat"
)

OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "phi3:latest")


# DATABASE CONNECTION

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# DATABASE INITIALIZATION

def init_db():
    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS notices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            date TEXT NOT NULL
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS complaints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            subject TEXT NOT NULL,
            message TEXT NOT NULL,
            date TEXT NOT NULL,
            status TEXT DEFAULT 'Pending'
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            message TEXT NOT NULL,
            date TEXT NOT NULL
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS uploads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            category TEXT NOT NULL,
            filename TEXT NOT NULL,
            original_filename TEXT NOT NULL,
            uploaded_at TEXT NOT NULL
        )
    """)

    admin = conn.execute(
        "SELECT id FROM admins WHERE username = ?",
        ("admin",)
    ).fetchone()

    if not admin:
        conn.execute(
            "INSERT INTO admins (username, password) VALUES (?, ?)",
            ("admin", generate_password_hash("admin123"))
        )

    count = conn.execute(
        "SELECT COUNT(*) FROM notices"
    ).fetchone()[0]

    if count == 0:
        today = datetime.now().strftime("%d-%m-%Y")

        conn.execute("""
            INSERT INTO notices (title, description, date)
            VALUES (?, ?, ?)
        """, (
            "Welcome to Gram Panchayat Matrukha",
            "Welcome to the information portal of Gram Panchayat Matrukha.",
            today
        ))

        conn.execute("""
            INSERT INTO notices (title, description, date)
            VALUES (?, ?, ?)
        """, (
            "Government Schemes Information",
            "Residents can contact the Panchayat office for information about government schemes.",
            today
        ))

    conn.commit()
    conn.close()


# ADMIN LOGIN PROTECTION

def admin_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if "admin" not in session:
            return redirect(url_for("admin_login"))
        return func(*args, **kwargs)
    return wrapper


# FILE VALIDATION

def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )


# HOME PAGE

@app.route("/")
def home():
    conn = get_db()

    notices = conn.execute("""
        SELECT * FROM notices
        ORDER BY id DESC
        LIMIT 3
    """).fetchall()

    conn.close()

    return render_template("index.html", notices=notices)
# LANGUAGE SWITCH

@app.route("/set-language/<lang>")
def set_language(lang):

    if lang in ["hi", "en"]:
        session["language"] = lang
        session["lang"] = lang

    return redirect(request.referrer or url_for("home"))

# ABOUT PAGE

@app.route("/about")
def about():
    return render_template("about.html")


# SERVICES PAGE

@app.route("/services")
def services():
    return render_template("services.html")


@app.route("/panchayat-team")
def panchayat_team():

    team = [
        {
            "name_hi": "रविन्द्र कुमार",
            "name_en": "Ravindra Kumar",
            "designation_hi": "मुखिया",
            "designation_en": "Village Head"
        },
        {
            "name_hi": "प्रियंका कुमारी",
            "name_en": "Priyanka Kumari",
            "designation_hi": "पंचायत सचिव",
            "designation_en": "Panchayat Secretary"
        },
        {
            "name_hi": "रंजीत शर्मा",
            "name_en": "Ranjeet Sharma",
            "designation_hi": "रोजगार सेवक",
            "designation_en": "Employment Assistant"
        },
        {
            "name_hi": "उमेश कुमार महतो",
            "name_en": "Umesh Kumar Mahto",
            "designation_hi": "राजस्व कर्मचारी",
            "designation_en": "Revenue Employee"
        },
        {
            "name_hi": "विजय राणा",
            "name_en": "Vijay Rana",
            "designation_hi": "उप-मुखिया",
            "designation_en": "Deputy Village Head"
        },
        {
            "name_hi": "उमेश प्रभाकर",
            "name_en": "Umesh Prabhakar",
            "designation_hi": "जनसेवक",
            "designation_en": "Public Service Worker"
        },
        {
            "name_hi": "ललन कुमार",
            "name_en": "Lalan Kumar",
            "designation_hi": "कनीय अभियंता मनरेगा",
            "designation_en": "Junior Engineer (MGNREGA)"
        },
        {
            "name_hi": "संतोष माथा",
            "name_en": "Santosh Matha",
            "designation_hi": "सहायक अभियंता",
            "designation_en": "Assistant Engineer"
        },
        {
            "name_hi": "अजीत मंडल",
            "name_en": "Ajit Mandal",
            "designation_hi": "पंचायत सहायक",
            "designation_en": "Panchayat Assistant"
        },
        {
            "name_hi": "राखी कुमारी",
            "name_en": "Rakhi Kumari",
            "designation_hi": "पंचायत सहायक",
            "designation_en": "Panchayat Assistant"
        }
    ]

    return render_template("panchayat_team.html", team=team)

# NOTICES PAGE

@app.route("/notices")
def notices():
    conn = get_db()

    all_notices = conn.execute("""
        SELECT * FROM notices
        ORDER BY id DESC
    """).fetchall()

    conn.close()

    return render_template("notices.html", notices=all_notices)


# COMPLAINT PAGE

@app.route("/complaint", methods=["GET", "POST"])
def complaint():

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        phone = request.form.get("phone", "").strip()
        subject = request.form.get("subject", "").strip()
        message = request.form.get("message", "").strip()

        if not all([name, phone, subject, message]):
            flash("Please fill in all fields.", "danger")
            return redirect(url_for("complaint"))

        if len(phone) > 20 or len(message) > 3000:
            flash("Please check your phone number and message length.", "danger")
            return redirect(url_for("complaint"))

        conn = get_db()

        conn.execute("""
            INSERT INTO complaints
            (name, phone, subject, message, date)
            VALUES (?, ?, ?, ?, ?)
        """, (
            name,
            phone,
            subject,
            message,
            datetime.now().strftime("%d-%m-%Y %H:%M")
        ))

        conn.commit()
        conn.close()

        flash("Your complaint has been submitted successfully.", "success")

        return redirect(url_for("complaint"))

    return render_template("complaint.html")


# CONTACT PAGE

@app.route("/contact", methods=["GET", "POST"])
def contact():

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        message = request.form.get("message", "").strip()

        if not all([name, email, message]):
            flash("Please fill in all fields.", "danger")
            return redirect(url_for("contact"))

        conn = get_db()

        conn.execute("""
            INSERT INTO messages (name, email, message, date)
            VALUES (?, ?, ?, ?)
        """, (
            name,
            email,
            message,
            datetime.now().strftime("%d-%m-%Y %H:%M")
        ))

        conn.commit()
        conn.close()

        flash("Your message has been submitted.", "success")

        return redirect(url_for("contact"))

    return render_template("contact.html")


# ADMIN LOGIN

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():

    if "admin" in session:
        return redirect(url_for("admin_dashboard"))

    if request.method == "POST":

        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        conn = get_db()

        admin = conn.execute("""
            SELECT * FROM admins
            WHERE username = ?
        """, (username,)).fetchone()

        conn.close()

        if admin and check_password_hash(admin["password"], password):

            session.clear()
            session["admin"] = admin["username"]

            return redirect(url_for("admin_dashboard"))

        flash("Invalid username or password.", "danger")

    return render_template("admin_login.html")


# ADMIN DASHBOARD

@app.route("/admin/dashboard")
@admin_required
def admin_dashboard():

    conn = get_db()

    all_notices = conn.execute("""
        SELECT * FROM notices
        ORDER BY id DESC
    """).fetchall()

    all_complaints = conn.execute("""
        SELECT * FROM complaints
        ORDER BY id DESC
    """).fetchall()

    all_messages = conn.execute("""
        SELECT * FROM messages
        ORDER BY id DESC
    """).fetchall()

    all_uploads = conn.execute("""
        SELECT * FROM uploads
        ORDER BY id DESC
    """).fetchall()

    complaint_count = conn.execute(
        "SELECT COUNT(*) FROM complaints"
    ).fetchone()[0]

    notice_count = conn.execute(
        "SELECT COUNT(*) FROM notices"
    ).fetchone()[0]

    pending_count = conn.execute("""
        SELECT COUNT(*) FROM complaints
        WHERE status = 'Pending'
    """).fetchone()[0]

    upload_count = conn.execute(
        "SELECT COUNT(*) FROM uploads"
    ).fetchone()[0]

    conn.close()

    return render_template(
        "admin_dashboard.html",
        notices=all_notices,
        complaints=all_complaints,
        messages=all_messages,
        uploads=all_uploads,
        complaint_count=complaint_count,
        notice_count=notice_count,
        pending_count=pending_count,
        upload_count=upload_count
    )


# ADD NOTICE

@app.route("/admin/add-notice", methods=["POST"])
@admin_required
def add_notice():

    title = request.form.get("title", "").strip()
    description = request.form.get("description", "").strip()

    if not title or not description:
        flash("Please enter notice title and description.", "danger")
        return redirect(url_for("admin_dashboard"))

    conn = get_db()

    conn.execute("""
        INSERT INTO notices (title, description, date)
        VALUES (?, ?, ?)
    """, (
        title,
        description,
        datetime.now().strftime("%d-%m-%Y")
    ))

    conn.commit()
    conn.close()

    flash("Notice added successfully.", "success")

    return redirect(url_for("admin_dashboard"))


# DELETE NOTICE

@app.route("/admin/delete-notice/<int:notice_id>", methods=["POST"])
@admin_required
def delete_notice(notice_id):

    conn = get_db()

    conn.execute(
        "DELETE FROM notices WHERE id = ?",
        (notice_id,)
    )

    conn.commit()
    conn.close()

    flash("Notice deleted.", "success")

    return redirect(url_for("admin_dashboard"))


# UPDATE COMPLAINT STATUS

@app.route("/admin/update-complaint/<int:complaint_id>", methods=["POST"])
@admin_required
def update_complaint(complaint_id):

    status = request.form.get("status", "")

    if status not in ["Pending", "In Progress", "Resolved"]:
        flash("Invalid complaint status.", "danger")
        return redirect(url_for("admin_dashboard"))

    conn = get_db()

    conn.execute("""
        UPDATE complaints
        SET status = ?
        WHERE id = ?
    """, (status, complaint_id))

    conn.commit()
    conn.close()

    flash("Complaint status updated.", "success")

    return redirect(url_for("admin_dashboard"))


# UPLOAD FILE

@app.route("/admin/upload", methods=["POST"])
@admin_required
def upload_file():

    title = request.form.get("title", "").strip()
    description = request.form.get("description", "").strip()
    category = request.form.get("category", "").strip()
    file = request.files.get("file")

    allowed_categories = [
        "gallery", "notice", "document", "project"
    ]

    if not title or category not in allowed_categories or not file:
        flash("Please fill all required upload fields.", "danger")
        return redirect(url_for("admin_dashboard"))

    if len(title) > 150 or len(description) > 2000:
        flash("Title or description is too long.", "danger")
        return redirect(url_for("admin_dashboard"))

    if not file.filename:
        flash("Please select a file.", "danger")
        return redirect(url_for("admin_dashboard"))

    if not allowed_file(file.filename):
        flash("Allowed files: JPG, JPEG, PNG, WEBP and PDF.", "danger")
        return redirect(url_for("admin_dashboard"))

    extension = file.filename.rsplit(".", 1)[1].lower()

    if category == "gallery" and extension == "pdf":
        flash("Photo Gallery accepts image files only.", "danger")
        return redirect(url_for("admin_dashboard"))

    if category in ["notice", "document"] and extension != "pdf":
        flash("Please upload a PDF file for this category.", "danger")
        return redirect(url_for("admin_dashboard"))

    original_filename = secure_filename(file.filename)

    if not original_filename:
        flash("Invalid filename.", "danger")
        return redirect(url_for("admin_dashboard"))

    saved_filename = f"{uuid.uuid4().hex}.{extension}"

    save_path = os.path.join(
        app.config["UPLOAD_FOLDER"],
        saved_filename
    )

    conn = None

    try:
        file.save(save_path)

        conn = get_db()

        conn.execute("""
            INSERT INTO uploads
            (
                title, description, category,
                filename, original_filename, uploaded_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            title,
            description,
            category,
            saved_filename,
            original_filename,
            datetime.now().strftime("%d-%m-%Y %H:%M")
        ))

        conn.commit()

        flash("File uploaded successfully.", "success")

    except Exception:
        if os.path.isfile(save_path):
            os.remove(save_path)

        flash("Upload failed. Please try again.", "danger")

    finally:
        if conn:
            conn.close()

    return redirect(url_for("admin_dashboard"))


# DELETE UPLOADED FILE

@app.route("/admin/delete-upload/<int:upload_id>", methods=["POST"])
@admin_required
def delete_upload(upload_id):

    conn = get_db()

    upload = conn.execute("""
        SELECT * FROM uploads
        WHERE id = ?
    """, (upload_id,)).fetchone()

    if not upload:
        conn.close()
        flash("Upload not found.", "danger")
        return redirect(url_for("admin_dashboard"))

    filename = os.path.basename(upload["filename"])

    file_path = os.path.join(
        app.config["UPLOAD_FOLDER"],
        filename
    )

    try:
        if os.path.isfile(file_path):
            os.remove(file_path)

        conn.execute(
            "DELETE FROM uploads WHERE id = ?",
            (upload_id,)
        )

        conn.commit()

        flash("Uploaded file deleted successfully.", "success")

    except OSError:
        flash("Could not delete the uploaded file.", "danger")

    finally:
        conn.close()

    return redirect(url_for("admin_dashboard"))


# PUBLIC PHOTO GALLERY

@app.route("/gallery")
def gallery():

    conn = get_db()

    items = conn.execute("""
        SELECT * FROM uploads
        WHERE category = 'gallery'
        ORDER BY id DESC
    """).fetchall()

    conn.close()

    return render_template("gallery.html", items=items)


# PUBLIC DOCUMENTS

@app.route("/documents")
def documents():

    conn = get_db()

    items = conn.execute("""
        SELECT * FROM uploads
        WHERE category IN ('document', 'notice')
        ORDER BY id DESC
    """).fetchall()

    conn.close()

    return render_template("documents.html", items=items)


# PUBLIC DEVELOPMENT PROJECTS

@app.route("/projects")
def projects():

    conn = get_db()

    items = conn.execute("""
        SELECT * FROM uploads
        WHERE category = 'project'
        ORDER BY id DESC
    """).fetchall()

    conn.close()

    return render_template("projects.html", items=items)


# ADMIN LOGOUT

@app.route("/admin/logout")
def admin_logout():

    session.clear()

    return redirect(url_for("home"))


# OLLAMA AI CHATBOT

@app.route("/api/chat", methods=["POST"])
def chatbot():

    data = request.get_json(silent=True) or {}

    question = str(data.get("message", "")).strip()
    language = data.get("language", "hi")

    if language not in ["hi", "en"]:
        language = "hi"

    if not question:
        return jsonify({
            "reply": "Please enter your question."
        }), 400

    if len(question) > 2000:
        return jsonify({
            "reply": "Question is too long."
        }), 400

    if language == "hi":
        language_instruction = """
        उत्तर हमेशा सरल और स्पष्ट हिंदी भाषा में दें।
        सरकारी सेवाओं की जानकारी सरल हिंदी में दें।
        """
    else:
        language_instruction = """
        Always answer in simple and clear English.
        Provide helpful information about Panchayat services.
        """

    system_prompt = f"""
    You are the AI assistant of Gram Panchayat Matrukha.

    The Mukhiya of Gram Panchayat Matrukha is Shri Ravindra Kumar.

    Your responsibilities:
    - Explain Panchayat services.
    - Provide general information about government schemes.
    - Explain birth and death certificate procedures.
    - Answer questions about sanitation, water and roads.
    - Guide citizens about public complaints.

    Language instructions:
    {language_instruction}

    Important rules:
    - Never invent official phone numbers.
    - Never invent government approvals.
    - Never claim a complaint has been officially resolved.
    - Never invent personal records or application status.
    - For unverified local information, direct users to the Panchayat office.
    - Be polite and helpful.
    """

    try:

        response = requests.post(
            OLLAMA_URL,
            json={
                "model": OLLAMA_MODEL,
                "messages": [
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": question
                    }
                ],
                "stream": False
            },
            timeout=120
        )

        response.raise_for_status()

        result = response.json()

        reply = result.get(
            "message", {}
        ).get("content", "")

        if not reply:
            reply = "Sorry, I could not generate an answer."

        return jsonify({"reply": reply})

    except requests.exceptions.ConnectionError:

        return jsonify({
            "reply": "Ollama is not running. Please start Ollama."
        }), 503

    except requests.exceptions.Timeout:

        return jsonify({
            "reply": "AI response timed out. Please try again."
        }), 504

    except requests.exceptions.RequestException:

        return jsonify({
            "reply": "AI service is temporarily unavailable."
        }), 503


# FILE TOO LARGE ERROR

@app.errorhandler(413)
def file_too_large(error):

    return (
        "File is too large. Maximum allowed size is 10 MB.",
        413
    )


# PAGE NOT FOUND

@app.errorhandler(404)
def page_not_found(error):

    return "Page not found.", 404


# START APPLICATION

if __name__ == "__main__":

    init_db()

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )
