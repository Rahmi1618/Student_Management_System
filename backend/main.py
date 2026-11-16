import hashlib
import secrets
import smtplib
import sqlite3
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, Field, field_validator

app = FastAPI(title="EduCore Student Management System API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = "students.db"
active_tokens = {}

# SMTP Configuration
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = "rahmimuhe6@gmail.com"
SENDER_PASSWORD = "doednumoxivfzuzf"


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def send_email(to_email: str, subject: str, body: str):
    try:
        msg = MIMEMultipart()
        msg["From"] = SENDER_EMAIL
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.send_message(msg)
        server.quit()
        print(f"[EMAIL SENT] Dispatched to {to_email}")
        return True
    except Exception as e:
        print(f"[EMAIL ERROR] Failed to send email to {to_email}: {e}")
        return False


def send_credentials_email(to_email: str, full_name: str, username: str, temp_password: str, student_code: str):
    subject = "EduCore Student Portal - Registration Approved & Login Credentials"
    body = f"""Hello {full_name},

Congratulations! Your registration request for the EduCore Student Management System has been approved by the administrator.

Here are your official student portal login credentials:
--------------------------------------------------
Student ID: {student_code}
Username:   {username}
Password:   {temp_password}
--------------------------------------------------

Please log in to the student portal and change your temporary password immediately for security.

Best regards,
EduCore Administration Team
"""
    send_email(to_email, subject, body)


def send_password_reset_email(to_email: str, full_name: str, username: str, new_temp_password: str):
    subject = "EduCore Student Portal - Password Reset"
    body = f"""Hello {full_name},

We received a password reset request for your EduCore Student Portal account.

Your temporary login credentials are:
--------------------------------------------------
Username:     {username}
New Password: {new_temp_password}
--------------------------------------------------

Please log in using this temporary password and update it immediately in your profile settings.

Best regards,
EduCore Administration Team
"""
    return send_email(to_email, subject, body)


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_code TEXT UNIQUE NOT NULL,
            full_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            department TEXT NOT NULL,
            gpa REAL NOT NULL,
            photo_url TEXT DEFAULT '',
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS student_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            department TEXT NOT NULL,
            gpa REAL NOT NULL,
            photo_url TEXT DEFAULT '',
            status TEXT DEFAULT 'pending',
            submitted_at TEXT NOT NULL
        )
    """)

    # Seed default admin if not exists
    cursor.execute("SELECT * FROM admins WHERE username = ?", ("admin",))
    if not cursor.fetchone():
        cursor.execute(
            "INSERT INTO admins (username, password_hash) VALUES (?, ?)",
            ("admin", hash_password("admin123")),
        )

    conn.commit()
    conn.close()


init_db()


# Pydantic Schemas with Strict Input Validation
class LoginRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=4, max_length=100)
    role: str = Field(..., pattern="^(admin|student)$")


class StudentRegistrationRequest(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    department: str = Field(..., min_length=2, max_length=100)
    gpa: float = Field(..., ge=0.0, le=4.0)
    photo_url: Optional[str] = Field(default="", max_length=2_000_000)

    @field_validator("full_name", "department")
    @classmethod
    def not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Field cannot be blank or whitespace only")
        return v.strip()


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ChangePasswordRequest(BaseModel):
    old_password: str = Field(..., min_length=4)
    new_password: str = Field(..., min_length=6, max_length=100)


class UpdatePhotoRequest(BaseModel):
    photo_url: str = Field(..., max_length=2_000_000)


def get_current_user(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization token")
    token = authorization.split(" ")[1]
    user = active_tokens.get(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired session token")
    return user


def require_admin(user: dict = Depends(get_current_user)):
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Administrator privileges required")
    return user


@app.post("/auth/login")
def login(payload: LoginRequest):
    conn = get_db()
    cursor = conn.cursor()
    pw_hash = hash_password(payload.password)

    if payload.role == "admin":
        cursor.execute(
            "SELECT id, username FROM admins WHERE username = ? AND password_hash = ?",
            (payload.username.strip(), pw_hash),
        )
        admin = cursor.fetchone()
        conn.close()
        if not admin:
            raise HTTPException(status_code=401, detail="Invalid admin username or password")

        token = secrets.token_hex(24)
        active_tokens[token] = {"id": admin["id"], "username": admin["username"], "role": "admin"}
        return {"token": token, "role": "admin", "username": admin["username"]}

    else:
        cursor.execute(
            "SELECT id, student_code, full_name, username, email, department, gpa, photo_url FROM students WHERE username = ? AND password_hash = ?",
            (payload.username.strip(), pw_hash),
        )
        student = cursor.fetchone()
        conn.close()
        if not student:
            raise HTTPException(status_code=401, detail="Invalid student username or password")

        token = secrets.token_hex(24)
        active_tokens[token] = {
            "id": student["id"],
            "username": student["username"],
            "role": "student",
        }
        return {
            "token": token,
            "role": "student",
            "student": dict(student),
        }


@app.post("/auth/forgot-password")
def forgot_password(payload: ForgotPasswordRequest):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, full_name, username, email FROM students WHERE email = ?", (payload.email.lower(),))
    student = cursor.fetchone()
    if not student:
        conn.close()
        raise HTTPException(status_code=404, detail="No approved student account found with that email address")

    new_temp_password = secrets.token_urlsafe(8)
    cursor.execute(
        "UPDATE students SET password_hash = ? WHERE id = ?",
        (hash_password(new_temp_password), student["id"]),
    )
    conn.commit()
    conn.close()

    sent = send_password_reset_email(
        to_email=student["email"],
        full_name=student["full_name"],
        username=student["username"],
        new_temp_password=new_temp_password,
    )
    if not sent:
        raise HTTPException(status_code=500, detail="Password was reset, but email delivery failed. Contact administrator.")

    return {"message": f"A temporary password has been sent to {student['email']}."}


@app.post("/register-request")
def submit_registration_request(payload: StudentRegistrationRequest):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM students WHERE email = ?", (payload.email.lower(),))
    if cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="A student account with this email already exists")

    cursor.execute("SELECT id, status FROM student_requests WHERE email = ?", (payload.email.lower(),))
    existing_req = cursor.fetchone()
    if existing_req:
        conn.close()
        raise HTTPException(
            status_code=400,
            detail=f"A registration request with this email already exists (status: {existing_req['status']})",
        )

    cursor.execute(
        """
        INSERT INTO student_requests (full_name, email, department, gpa, photo_url, status, submitted_at)
        VALUES (?, ?, ?, ?, ?, 'pending', ?)
        """,
        (
            payload.full_name,
            payload.email.lower(),
            payload.department,
            round(payload.gpa, 2),
            payload.photo_url or "",
            datetime.utcnow().isoformat(),
        ),
    )
    conn.commit()
    conn.close()
    return {"message": "Registration request submitted successfully! You will receive an email once approved."}


@app.get("/student-requests")
def get_student_requests(admin: dict = Depends(require_admin)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM student_requests ORDER BY id DESC")
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows


@app.post("/student-requests/{request_id}/approve")
def approve_student_request(request_id: int, admin: dict = Depends(require_admin)):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM student_requests WHERE id = ?", (request_id,))
    req = cursor.fetchone()
    if not req:
        conn.close()
        raise HTTPException(status_code=404, detail="Registration request not found")

    if req["status"] != "pending":
        conn.close()
        raise HTTPException(status_code=400, detail=f"Request is already {req['status']}")

    random_suffix = secrets.randbelow(9000) + 1000
    student_code = f"EDU-{datetime.utcnow().year}-{random_suffix}"
    first_name_clean = "".join(c for c in req["full_name"].split()[0].lower() if c.isalnum())
    username = f"{first_name_clean}{random_suffix}"
    temp_password = secrets.token_urlsafe(8)

    cursor.execute(
        """
        INSERT INTO students (student_code, full_name, email, department, gpa, photo_url, username, password_hash, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            student_code,
            req["full_name"],
            req["email"],
            req["department"],
            req["gpa"],
            req["photo_url"] or "",
            username,
            hash_password(temp_password),
            datetime.utcnow().isoformat(),
        ),
    )

    cursor.execute("UPDATE student_requests SET status = 'approved' WHERE id = ?", (request_id,))
    conn.commit()
    conn.close()

    send_credentials_email(
        to_email=req["email"],
        full_name=req["full_name"],
        username=username,
        temp_password=temp_password,
        student_code=student_code,
    )

    return {
        "message": f"Approved {req['full_name']}. Credentials sent to {req['email']}.",
        "student_code": student_code,
        "username": username,
    }


@app.post("/student-requests/{request_id}/reject")
def reject_student_request(request_id: int, admin: dict = Depends(require_admin)):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM student_requests WHERE id = ?", (request_id,))
    req = cursor.fetchone()
    if not req:
        conn.close()
        raise HTTPException(status_code=404, detail="Registration request not found")

    if req["status"] != "pending":
        conn.close()
        raise HTTPException(status_code=400, detail=f"Request is already {req['status']}")

    cursor.execute("UPDATE student_requests SET status = 'rejected' WHERE id = ?", (request_id,))
    conn.commit()
    conn.close()
    return {"message": f"Registration request for {req['full_name']} has been rejected."}


@app.get("/students")
def list_students(department: Optional[str] = None, search: Optional[str] = None, admin: dict = Depends(require_admin)):
    conn = get_db()
    cursor = conn.cursor()
    query = "SELECT id, student_code, full_name, email, department, gpa, photo_url, username, created_at FROM students WHERE 1=1"
    params = []

    if department and department.strip():
        query += " AND LOWER(department) = LOWER(?)"
        params.append(department.strip())

    if search and search.strip():
        query += " AND (LOWER(full_name) LIKE LOWER(?) OR LOWER(student_code) LIKE LOWER(?) OR LOWER(email) LIKE LOWER(?))"
        term = f"%{search.strip()}%"
        params.extend([term, term, term])

    query += " ORDER BY id DESC"
    cursor.execute(query, params)
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows


@app.delete("/students/{student_id}")
def delete_student(student_id: int, admin: dict = Depends(require_admin)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM students WHERE id = ?", (student_id,))
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Student not found")
    conn.commit()
    conn.close()
    return {"message": "Student record deleted successfully"}


@app.get("/student/me")
def get_my_profile(user: dict = Depends(get_current_user)):
    if user.get("role") != "student":
        raise HTTPException(status_code=403, detail="Student access only")
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, student_code, full_name, email, department, gpa, photo_url, username, created_at FROM students WHERE id = ?",
        (user["id"],),
    )
    student = cursor.fetchone()
    conn.close()
    if not student:
        raise HTTPException(status_code=404, detail="Student profile not found")
    return dict(student)


@app.post("/student/update-photo")
def update_student_photo(payload: UpdatePhotoRequest, user: dict = Depends(get_current_user)):
    if user.get("role") != "student":
        raise HTTPException(status_code=403, detail="Student access only")
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE students SET photo_url = ? WHERE id = ?", (payload.photo_url, user["id"]))
    conn.commit()
    conn.close()
    return {"message": "Profile photo updated successfully"}


@app.post("/student/change-password")
def change_student_password(payload: ChangePasswordRequest, user: dict = Depends(get_current_user)):
    if user.get("role") != "student":
        raise HTTPException(status_code=403, detail="Student access only")

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT password_hash FROM students WHERE id = ?", (user["id"],))
    row = cursor.fetchone()
    if not row or row["password_hash"] != hash_password(payload.old_password):
        conn.close()
        raise HTTPException(status_code=400, detail="Current password is incorrect")

    cursor.execute(
        "UPDATE students SET password_hash = ? WHERE id = ?",
        (hash_password(payload.new_password), user["id"]),
    )
    conn.commit()
    conn.close()
    return {"message": "Password updated successfully"}
