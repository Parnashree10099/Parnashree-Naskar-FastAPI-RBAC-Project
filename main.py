from fastapi import FastAPI, UploadFile, File, Form, Request, Response, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.requests import Request
from pydantic import BaseModel
from dotenv import load_dotenv
import smtplib
import sqlite3
import re
import random
import string
import os
import time
import hmac
import hashlib
import base64

load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY", "my-fastapi-secret-key")
def create_session_token(email):
    expiry = int(time.time()) + 3600

    data = f"{email}|{expiry}"

    signature = hmac.new(
        SECRET_KEY.encode(),
        data.encode(),
        hashlib.sha256
    ).hexdigest()

    token = base64.urlsafe_b64encode(
        data.encode()
    ).decode()

    return token + "." + signature

EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

app = FastAPI()
reset_otps = {}
def send_otp_email(receiver_email, otp):

    subject = "Your OTP Verification Code"

    body = f"""
Your OTP is: {otp}

Please use this OTP to complete the verification.
"""

    message = f"Subject: {subject}\n\n{body}"

    with smtplib.SMTP("smtp.gmail.com", 587) as server:

        server.starttls()

        server.login(
            EMAIL_ADDRESS,
            EMAIL_PASSWORD
        )

        server.sendmail(
            EMAIL_ADDRESS,
            receiver_email,
            message
        )
def send_credentials_email(receiver_email, temporary_password):

    subject = "Your Login Credentials"

    body = f"""
Your account has been created by the Admin.

Email: {receiver_email}
Temporary Password: {temporary_password}

Please use these credentials to log in.

You will be asked to verify your email with an OTP and
change your temporary password during your first login.
"""

    message = f"Subject: {subject}\n\n{body}"

    with smtplib.SMTP("smtp.gmail.com", 587) as server:

        server.starttls()

        server.login(
            EMAIL_ADDRESS,
            EMAIL_PASSWORD
        )

        server.sendmail(
            EMAIL_ADDRESS,
            receiver_email,
            message
        )

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
def show_register_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="register.html"
    )




class UserRegistration(BaseModel):
    full_name: str
    email: str
    phone: str
    dob: str
    password: str
    role: str
    subject: str = ""
    standard: str = ""


@app.post("/register")
def register_user(user: UserRegistration):

    # Validate role
    if user.role not in ["Teacher", "Student"]:
        return {
            "success": False,
            "message": "Please select a valid role!"
        }

    # Validate Teacher details
    if user.role == "Teacher" and not user.subject.strip():
        return {
            "success": False,
            "message": "Subject is required for Teachers!"
        }

    # Validate Student details
    if user.role == "Student" and not user.standard.strip():
        return {
            "success": False,
            "message": "Standard is required for Students!"
        }

    # Password validation
    password = user.password

    if len(password) < 10:
        return {
            "success": False,
            "message": "Password must contain at least 10 characters!"
        }

    if not re.search(r"[A-Za-z]", password):
        return {
            "success": False,
            "message": "Password must contain at least one alphabet!"
        }

    if not re.search(r"[0-9]", password):
        return {
            "success": False,
            "message": "Password must contain at least one number!"
        }

    if not re.search(r"[^A-Za-z0-9]", password):
        return {
            "success": False,
            "message": "Password must contain at least one special character!"
        }

    # Generate OTP
    otp = str(random.randint(100000, 999999))

    connection = sqlite3.connect("users.db")
    cursor = connection.cursor()

    try:

        cursor.execute("""
            INSERT INTO users (
                full_name,
                email,
                phone,
                dob,
                password,
                otp,
                role,
                subject,
                standard
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user.full_name,
            user.email,
            user.phone,
            user.dob,
            user.password,
            otp,
            user.role,
            user.subject if user.role == "Teacher" else None,
            user.standard if user.role == "Student" else None
        ))

        connection.commit()

        # Send OTP email
        send_otp_email(user.email, otp)

        return {
            "success": True,
            "message": "Registration successful! OTP has been sent to your email."
        }

    except sqlite3.IntegrityError:

        return {
            "success": False,
            "message": "This email is already registered!"
        }

    finally:

        connection.close()


class EmailVerification(BaseModel):
    email: str
    otp: str


@app.post("/verify-email")
def verify_email(data: EmailVerification):

    connection = sqlite3.connect("users.db")
    cursor = connection.cursor()

    cursor.execute(
        "SELECT otp FROM users WHERE email = ?",
        (data.email,)
    )

    user = cursor.fetchone()

    if user is None:
        connection.close()

        return {
            "message": "User not found!"
        }

    stored_otp = user[0]

    if stored_otp != data.otp:
        connection.close()

        return {
            "message": "Invalid OTP!"
        }

    cursor.execute(
        "UPDATE users SET is_verified = 1 WHERE email = ?",
        (data.email,)
    )

    connection.commit()
    connection.close()

    return {
        "message": "Email verified successfully!"
    }
@app.get("/verify", response_class=HTMLResponse)
def show_verify_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="verify.html"
    )



class UserLogin(BaseModel):
    email: str
    password: str

def generate_login_otp():
    return str(random.randint(100000, 999999))


@app.post("/login")
def login_user(user: UserLogin):

    connection = sqlite3.connect("users.db")
    cursor = connection.cursor()

    cursor.execute(
        """
       SELECT email, password, is_verified, must_change_password
FROM users
WHERE email = ?
        """,
        (user.email,)
    )

    database_user = cursor.fetchone()

    connection.close()

    if database_user is None:
        return {
            "message": "User not found!"
        }

    stored_email = database_user[0]
    stored_password = database_user[1]
    is_verified = database_user[2]
    must_change_password = database_user[3]

    if stored_password != user.password:
        return {
            "message": "Incorrect password!"
        }

    if is_verified == 0:
        return {
            "message": "Email is not verified. Please verify your email first.",
            "redirect": "/verify"
        }
    if must_change_password == 1:

        login_otp = generate_login_otp()

        connection = sqlite3.connect("users.db")
        cursor = connection.cursor()

        cursor.execute("""
            UPDATE users
            SET login_otp = ?
            WHERE email = ?
        """, (login_otp, stored_email))

        connection.commit()
        connection.close()

        send_otp_email(stored_email, login_otp)

        return {
            "message": "First login detected. OTP sent to your email.",
            "redirect": "/first-login"
        }

    session_token = create_session_token(stored_email)

    response = Response(
        content='{"message":"Login successful!","redirect":"/dashboard"}',
        media_type="application/json"
    )

    response.set_cookie(
        key="session_token",
        value=session_token,
        httponly=True,
        samesite="lax"
    )

    return response
class FirstLoginData(BaseModel):
    email: str
    otp: str
    new_password: str


@app.post("/first-login")
def complete_first_login(data: FirstLoginData):

    connection = sqlite3.connect("users.db")
    cursor = connection.cursor()

    cursor.execute("""
        SELECT login_otp, must_change_password
        FROM users
        WHERE email = ?
    """, (data.email,))

    user = cursor.fetchone()

    if user is None:
        connection.close()
        return {
            "success": False,
            "message": "User not found!"
        }

    stored_otp = user[0]
    must_change_password = user[1]

    if must_change_password != 1:
        connection.close()
        return {
            "success": False,
            "message": "First login is already completed!"
        }

    if stored_otp != data.otp:
        connection.close()
        return {
            "success": False,
            "message": "Invalid OTP!"
        }
    password = data.new_password

    if len(password) < 10:
        connection.close()
        return {
            "success": False,
            "message": "Password must contain at least 10 characters!"
        }

    if not re.search(r"[A-Za-z]", password):
        connection.close()
        return {
            "success": False,
            "message": "Password must contain at least one alphabet!"
        }

    if not re.search(r"[0-9]", password):
        connection.close()
        return {
            "success": False,
            "message": "Password must contain at least one number!"
        }

    if not re.search(r"[^A-Za-z0-9]", password):
        connection.close()
        return {
            "success": False,
            "message": "Password must contain at least one special character!"
        }

    cursor.execute("""
        UPDATE users
        SET password = ?,
            must_change_password = 0,
            login_otp = NULL
        WHERE email = ?
    """, (data.new_password, data.email))

    connection.commit()
    connection.close()

    return {
        "success": True,
        "message": "Password changed successfully! You can now login."
    }

def get_current_user(request: Request):

    token = request.cookies.get("session_token")

    if not token:
        raise HTTPException(
            status_code=401,
            detail="Please login first!"
        )
    try:
        encoded_data, signature = token.split(".")

        data = base64.urlsafe_b64decode(
            encoded_data.encode()
        ).decode()

        expected_signature = hmac.new(
            SECRET_KEY.encode(),
            data.encode(),
            hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(
            signature,
            expected_signature
        ):
            raise HTTPException(
                status_code=401,
                detail="Invalid session!"
            )

        email, expiry = data.split("|")

        if int(expiry) < int(time.time()):
            raise HTTPException(
                status_code=401,
                detail="Session expired!"
            )

        return email

    except (ValueError, TypeError):
        raise HTTPException(
            status_code=401,
            detail="Invalid session!"
        )

@app.get("/profile")
def get_profile(request: Request):

    email = get_current_user(request)

    connection = sqlite3.connect("users.db")
    cursor = connection.cursor()

    cursor.execute("""
        SELECT id, full_name, email, phone, dob, role
        FROM users
        WHERE email = ?
    """, (email,))

    user = cursor.fetchone()

    connection.close()

    if user is None:
        raise HTTPException(
            status_code=404,
            detail="User not found!"
        )

    return {
        "id": user[0],
        "full_name": user[1],
        "email": user[2],
        "phone": user[3],
        "dob": user[4],
        "role": user[5]
    }
@app.get("/first-login")
def first_login_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="first_login.html"
    )
@app.get("/dashboard", response_class=HTMLResponse)
def show_dashboard_page(request: Request):

    email = get_current_user(request)

    connection = sqlite3.connect("users.db")
    cursor = connection.cursor()

    cursor.execute("""
        SELECT must_change_password
        FROM users
        WHERE email = ?
    """, (email,))

    user = cursor.fetchone()

    connection.close()

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="User not found!"
        )

    if user[0] == 1:
        return RedirectResponse(
            url="/first-login",
            status_code=303
        )

    return templates.TemplateResponse(
        request=request,
        name="dashboard.html"
    )

@app.get("/login", response_class=HTMLResponse)
def show_login_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="login.html"
    )


class ProfileUpdate(BaseModel):
    email: str
    full_name: str
    phone: str
    dob: str


@app.put("/update-profile")
def update_profile(
    request: Request,
    data: ProfileUpdate
):

    # Get the email of the logged-in user from secure session
    email = get_current_user(request)

    connection = sqlite3.connect("users.db")
    cursor = connection.cursor()

    # Check the logged-in user's role
    cursor.execute("""
        SELECT role
        FROM users
        WHERE email = ?
    """, (email,))

    current_user = cursor.fetchone()

    if current_user is None:
        connection.close()
        raise HTTPException(
            status_code=401,
            detail="User not found!"
        )

    # Students are not allowed to update their profile
    if current_user[0] == "Student":
        connection.close()
        raise HTTPException(
            status_code=403,
            detail="Students cannot update their profile!"
        )

    cursor.execute("""
        UPDATE users
        SET full_name = ?, phone = ?, dob = ?
        WHERE email = ?
    """, (
        data.full_name,
        data.phone,
        data.dob,
        email
    ))
    cursor = connection.cursor()

    cursor.execute("""
        UPDATE users
        SET full_name = ?, phone = ?, dob = ?
        WHERE email = ?
    """, (
        data.full_name,
        data.phone,
        data.dob,
        email
    ))

    connection.commit()

    updated_rows = cursor.rowcount

    connection.close()

    if updated_rows == 0:
        return {
            "success": False,
            "message": "User not found!"
        }

    return {
        "success": True,
        "message": "Profile updated successfully!"
    }

@app.post("/upload-profile-picture")
async def upload_profile_picture(
    request: Request,
    file: UploadFile = File(...)
):

    # Get the logged-in user's email from the secure session
    email = get_current_user(request)

    file_extension = file.filename.split(".")[-1]

    file_name = (
        email.replace("@", "_").replace(".", "_")
        + "."
        + file_extension
    )

    file_path = os.path.join(
        "static",
        "uploads",
        file_name
    )

    file_content = await file.read()

    with open(file_path, "wb") as image_file:
        image_file.write(file_content)

    return {
        "success": True,
        "message": "Profile picture uploaded successfully!",
        "image_url": "/static/uploads/" + file_name
    }


@app.delete("/delete-profile-picture")
def delete_profile_picture(request: Request):

    # Get the logged-in user's email from the secure session
    email = get_current_user(request)

    upload_folder = os.path.join("static", "uploads")

    possible_extensions = ["jpg", "jpeg", "png", "webp"]

    deleted = False

    for extension in possible_extensions:

        file_name = (
            email.replace("@", "_").replace(".", "_")
            + "."
            + extension
        )

        file_path = os.path.join(
            upload_folder,
            file_name
        )

        if os.path.exists(file_path):
            os.remove(file_path)
            deleted = True

    if deleted:
        return {
            "success": True,
            "message": "Profile picture deleted successfully!"
        }

    return {
        "success": False,
        "message": "Profile picture not found!"
    }


class PasswordChange(BaseModel):
    email: str
    current_password: str
    new_password: str


@app.put("/change-password")
def change_password(data: PasswordChange):

    connection = sqlite3.connect("users.db")
    cursor = connection.cursor()

    cursor.execute(
        "SELECT password FROM users WHERE email = ?",
        (data.email,)
    )

    user = cursor.fetchone()

    if user is None:
        connection.close()

        return {
            "success": False,
            "message": "User not found!"
        }

    stored_password = user[0]

    if stored_password != data.current_password:
        connection.close()

        return {
            "success": False,
            "message": "Current password is incorrect!"
        }

    new_password = data.new_password

    if len(new_password) < 10:
        connection.close()

        return {
            "success": False,
            "message": "Password must contain at least 10 characters!"
        }

    if not re.search(r"[A-Za-z]", new_password):
        connection.close()

        return {
            "success": False,
            "message": "Password must contain at least one alphabet!"
        }

    if not re.search(r"[0-9]", new_password):
        connection.close()

        return {
            "success": False,
            "message": "Password must contain at least one number!"
        }

    if not re.search(r"[^A-Za-z0-9]", new_password):
        connection.close()

        return {
            "success": False,
            "message": "Password must contain at least one special character!"
        }

    cursor.execute(
        "UPDATE users SET password = ? WHERE email = ?",
        (new_password, data.email)
    )

    connection.commit()
    connection.close()

    return {
        "success": True,
        "message": "Password changed successfully!"
    }
@app.get("/change-password", response_class=HTMLResponse)
def show_change_password_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="change_password.html"
    )

class ForgotPassword(BaseModel):
    email: str

@app.get("/forgot-password", response_class=HTMLResponse)
def show_forgot_password_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="forgot_password.html"
    )
@app.post("/forgot-password")
def forgot_password(data: ForgotPassword):

    connection = sqlite3.connect("users.db")
    cursor = connection.cursor()

    cursor.execute(
        "SELECT email FROM users WHERE email = ?",
        (data.email,)
    )

    user = cursor.fetchone()

    connection.close()

    if user is None:
        return {
            "success": False,
            "message": "Email not found!"
        }

    otp = random.randint(100000, 999999)

    reset_otps[data.email] = otp
    send_otp_email(data.email, otp)

    return {
        "success": True,
        "message": "OTP generated successfully!"
    }

class ResetPassword(BaseModel):
    email: str
    otp: int
    new_password: str


@app.put("/reset-password")
def reset_password(data: ResetPassword):

    if data.email not in reset_otps:
        return {
            "success": False,
            "message": "Please request an OTP first!"
        }

    stored_otp = reset_otps[data.email]

    if stored_otp != data.otp:
        return {
            "success": False,
            "message": "Invalid OTP!"
        }

    new_password = data.new_password

    if len(new_password) < 10:
        return {
            "success": False,
            "message": "Password must contain at least 10 characters!"
        }

    if not re.search(r"[A-Za-z]", new_password):
        return {
            "success": False,
            "message": "Password must contain at least one alphabet!"
        }

    if not re.search(r"[0-9]", new_password):
        return {
            "success": False,
            "message": "Password must contain at least one number!"
        }

    if not re.search(r"[^A-Za-z0-9]", new_password):
        return {
            "success": False,
            "message": "Password must contain at least one special character!"
        }

    connection = sqlite3.connect("users.db")
    cursor = connection.cursor()

    cursor.execute(
        "UPDATE users SET password = ? WHERE email = ?",
        (new_password, data.email)
    )

    connection.commit()
    connection.close()

    del reset_otps[data.email]

    return {
        "success": True,
        "message": "Password reset successfully!"
    }

@app.get("/reset-password", response_class=HTMLResponse)
def show_reset_password_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="reset_password.html"
    )

@app.get("/logout")
def logout():

    response = RedirectResponse(
        url="/login",
        status_code=303
    )

    response.delete_cookie("session_token")

    return response

@app.delete("/delete-user/{email}")
def delete_user(email: str):

    connection = sqlite3.connect("users.db")
    cursor = connection.cursor()

    cursor.execute(
        "DELETE FROM users WHERE email = ?",
        (email,)
    )

    connection.commit()
    connection.close()

    return {
        "message": "User deleted successfully!"
    }

@app.get("/admin/users")
def get_all_users(request: Request):

    email = get_current_user(request)

    connection = sqlite3.connect("users.db")
    cursor = connection.cursor()

    # Check that the logged-in user is an Admin
    cursor.execute("""
        SELECT role
        FROM users
        WHERE email = ?
    """, (email,))

    current_user = cursor.fetchone()

    if current_user is None:
        connection.close()
        raise HTTPException(
            status_code=401,
            detail="User not found!"
        )

    if current_user[0] != "Admin":
        connection.close()
        raise HTTPException(
            status_code=403,
            detail="Admin access required!"
        )

    cursor.execute("""
        SELECT id, full_name, email, phone, role, subject, standard, teacher_id
        FROM users
        WHERE role IN ('Teacher', 'Student')
    """)

    users = cursor.fetchall()

    connection.close()

    return {
        "success": True,
        "users": [
            {
                "id": user[0],
                "full_name": user[1],
                "email": user[2],
                "phone": user[3],
                "role": user[4],
                "subject": user[5],
                "standard": user[6],
                "teacher_id": user[7]
            }
            for user in users
        ]
    }
class AdminCreateUser(BaseModel):
    full_name: str
    email: str
    phone: str
    dob: str
    role: str
    subject: str = ""
    standard: str = ""


@app.post("/admin/create-user")
def admin_create_user(request: Request, user: AdminCreateUser):

    email = get_current_user(request)

    connection = sqlite3.connect("users.db")
    cursor = connection.cursor()

    cursor.execute("""
        SELECT role
        FROM users
        WHERE email = ?
    """, (email,))

    current_user = cursor.fetchone()

    if current_user is None:
        connection.close()
        raise HTTPException(
            status_code=401,
            detail="User not found!"
        )

    if current_user[0] != "Admin":
        connection.close()
        raise HTTPException(
            status_code=403,
            detail="Admin access required!"
        )

    connection.close()
    temporary_password = (
    "Temp@"
    + "".join(
        random.choices(
            string.ascii_letters + string.digits,
            k=8
        )
    )
)

    if user.role not in ["Teacher", "Student"]:
        return {
            "success": False,
            "message": "Please select a valid role!"
        }

    if user.role == "Teacher" and not user.subject.strip():
        return {
            "success": False,
            "message": "Subject is required for Teachers!"
        }

    if user.role == "Student" and not user.standard.strip():
        return {
            "success": False,
            "message": "Standard is required for Students!"
        }


    connection = sqlite3.connect("users.db")
    cursor = connection.cursor()

    try:

        cursor.execute("""
            INSERT INTO users (
                full_name,
                email,
                phone,
                dob,
                password,
                is_verified,
                role,
                subject,
                standard,
                must_change_password
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user.full_name,
            user.email,
            user.phone,
            user.dob,
            temporary_password,
            1,
            user.role,
            user.subject if user.role == "Teacher" else None,
            user.standard if user.role == "Student" else None,
            1
        ))

        connection.commit()

        send_credentials_email(
            user.email,
            temporary_password
        )

        return {
            "success": True,
            "message": "User created successfully!",
            "temporary_password": temporary_password
        }

    except sqlite3.IntegrityError:

        return {
            "success": False,
            "message": "This email is already registered!"
        }

    finally:

        connection.close()
class AdminUpdateUser(BaseModel):
    full_name: str
    phone: str
    dob: str
    role: str
    subject: str = ""
    standard: str = ""


@app.put("/admin/update-user/{user_id}")
def admin_update_user(
    request: Request,
    user_id: int,
    user: AdminUpdateUser
):

    email = get_current_user(request)

    connection = sqlite3.connect("users.db")
    cursor = connection.cursor()

    cursor.execute("""
        SELECT role
        FROM users
        WHERE email = ?
    """, (email,))

    current_user = cursor.fetchone()

    if current_user is None:
        connection.close()
        raise HTTPException(
            status_code=401,
            detail="User not found!"
        )

    if current_user[0] != "Admin":
        connection.close()
        raise HTTPException(
            status_code=403,
            detail="Admin access required!"
        )
    

    connection.close()


    if user.role not in ["Teacher", "Student"]:
        return {
            "success": False,
            "message": "Please select a valid role!"
        }

    if user.role == "Teacher" and not user.subject.strip():
        return {
            "success": False,
            "message": "Subject is required for Teachers!"
        }

    if user.role == "Student" and not user.standard.strip():
        return {
            "success": False,
            "message": "Standard is required for Students!"
        }

    connection = sqlite3.connect("users.db")
    cursor = connection.cursor()

    try:

        cursor.execute("""
            UPDATE users
            SET
                full_name = ?,
                phone = ?,
                dob = ?,
                role = ?,
                subject = ?,
                standard = ?
            WHERE id = ?
        """, (
            user.full_name,
            user.phone,
            user.dob,
            user.role,
            user.subject if user.role == "Teacher" else None,
            user.standard if user.role == "Student" else None,
            user_id
        ))

        if cursor.rowcount == 0:
            return {
                "success": False,
                "message": "User not found!"
            }

        connection.commit()

        return {
            "success": True,
            "message": "User updated successfully!"
        }

    finally:

        connection.close()
@app.delete("/admin/delete-user/{user_id}")
def admin_delete_user(request: Request, user_id: int):

    email = get_current_user(request)

    connection = sqlite3.connect("users.db")
    cursor = connection.cursor()

    cursor.execute("""
        SELECT role
        FROM users
        WHERE email = ?
    """, (email,))

    current_user = cursor.fetchone()

    if current_user is None:
        connection.close()
        raise HTTPException(
            status_code=401,
            detail="User not found!"
        )

    if current_user[0] != "Admin":
        connection.close()
        raise HTTPException(
            status_code=403,
            detail="Admin access required!"
        )

    cursor.execute("""
        DELETE FROM users
        WHERE id = ? AND role IN ('Teacher', 'Student')
    """, (user_id,))

    if cursor.rowcount == 0:
        connection.close()
        return {
            "success": False,
            "message": "User not found!"
        }

    connection.commit()
    connection.close()

    return {
        "success": True,
        "message": "User deleted successfully!"
    }
class AssignTeacher(BaseModel):
    teacher_id: int


@app.put("/admin/assign-teacher/{student_id}")
def assign_teacher(
    request: Request,
    student_id: int,
    data: AssignTeacher
):

    # Get the logged-in user
    email = get_current_user(request)

    connection = sqlite3.connect("users.db")
    cursor = connection.cursor()

    # Check the logged-in user's role
    cursor.execute("""
        SELECT role
        FROM users
        WHERE email = ?
    """, (email,))

    current_user = cursor.fetchone()

    if current_user is None:
        connection.close()
        raise HTTPException(
            status_code=401,
            detail="User not found!"
        )

    # Only Admin can assign teachers
    if current_user[0] != "Admin":
        connection.close()
        raise HTTPException(
            status_code=403,
            detail="Admin access required!"
        )

    # Check whether selected user is a Teacher
    cursor.execute("""
        SELECT id
        FROM users
        WHERE id = ? AND role = 'Teacher'
    """, (data.teacher_id,))

    teacher = cursor.fetchone()

    if teacher is None:
        connection.close()
        return {
            "success": False,
            "message": "Selected user is not a Teacher!"
        }

    # Check whether selected user is a Student
    cursor.execute("""
        SELECT id
        FROM users
        WHERE id = ? AND role = 'Student'
    """, (student_id,))

    student = cursor.fetchone()

    if student is None:
        connection.close()
        return {
            "success": False,
            "message": "Student not found!"
        }

    # Assign / reassign the Teacher
    cursor.execute("""
        UPDATE users
        SET teacher_id = ?
        WHERE id = ? AND role = 'Student'
    """, (data.teacher_id, student_id))

    connection.commit()
    connection.close()

    return {
        "success": True,
        "message": "Teacher assigned successfully!"
    }

@app.get("/teacher/students")
def get_teacher_students(request: Request):

    email = get_current_user(request)

    connection = sqlite3.connect("users.db")
    cursor = connection.cursor()

    # Check that the logged-in user is a Teacher
    cursor.execute("""
        SELECT id, role
        FROM users
        WHERE email = ?
    """, (email,))

    current_user = cursor.fetchone()

    if current_user is None:
        connection.close()
        raise HTTPException(
            status_code=401,
            detail="User not found!"
        )

    if current_user[1] != "Teacher":
        connection.close()
        raise HTTPException(
            status_code=403,
            detail="Teacher access required!"
        )

    teacher_id = current_user[0]

    cursor.execute("""
        SELECT id, full_name, email, phone, dob, role, subject, standard
        FROM users
        WHERE teacher_id = ? AND role = 'Student'
    """, (teacher_id,))

    students = cursor.fetchall()

    connection.close()

    return {
        "success": True,
        "students": [
            {
                "id": student[0],
                "full_name": student[1],
                "email": student[2],
                "phone": student[3],
                "dob": student[4],
                "role": student[5],
                "subject": student[6],
                "standard": student[7]
            }
            for student in students
        ]
    }
@app.get("/student/teacher")
def get_student_teacher(request: Request):

    email = get_current_user(request)

    connection = sqlite3.connect("users.db")
    cursor = connection.cursor()

    cursor.execute("""
        SELECT id, role
        FROM users
        WHERE email = ?
    """, (email,))

    current_user = cursor.fetchone()

    if current_user is None:
        connection.close()
        raise HTTPException(
            status_code=401,
            detail="User not found!"
        )

    if current_user[1] != "Student":
        connection.close()
        raise HTTPException(
            status_code=403,
            detail="Student access required!"
        )

    student_id = current_user[0]

    cursor.execute("""
        SELECT
            teacher.id,
            teacher.full_name,
            teacher.email,
            teacher.subject
        FROM users AS student
        JOIN users AS teacher
            ON student.teacher_id = teacher.id
        WHERE student.id = ?
          AND student.role = 'Student'
          AND teacher.role = 'Teacher'
    """, (student_id,))

    teacher = cursor.fetchone()

    connection.close()

    if teacher is None:
        return {
            "success": False,
            "message": "No Teacher assigned yet!"
        }

    return {
        "success": True,
        "teacher": {
            "id": teacher[0],
            "full_name": teacher[1],
            "email": teacher[2],
            "subject": teacher[3]
        }
    }
class TeacherUpdateStudent(BaseModel):
    full_name: str
    phone: str
    dob: str
    standard: str


@app.put("/teacher/update-student/{student_id}")
def teacher_update_student(
    request: Request,
    student_id: int,
    student: TeacherUpdateStudent
):

    email = get_current_user(request)

    connection = sqlite3.connect("users.db")
    cursor = connection.cursor()

    # Check logged-in user
    cursor.execute("""
        SELECT id, role
        FROM users
        WHERE email = ?
    """, (email,))

    current_user = cursor.fetchone()

    if current_user is None:
        connection.close()
        raise HTTPException(
            status_code=401,
            detail="User not found!"
        )

    # Only Teachers can use this endpoint
    if current_user[1] != "Teacher":
        connection.close()
        raise HTTPException(
            status_code=403,
            detail="Teacher access required!"
        )

    teacher_id = current_user[0]

    # Make sure this student belongs to this Teacher
    cursor.execute("""
        SELECT id
        FROM users
        WHERE id = ?
          AND role = 'Student'
          AND teacher_id = ?
    """, (student_id, teacher_id))

    assigned_student = cursor.fetchone()

    if assigned_student is None:
        connection.close()
        raise HTTPException(
            status_code=403,
            detail="You can only update students assigned to you!"
        )

    # Update the student
    cursor.execute("""
        UPDATE users
        SET
            full_name = ?,
            phone = ?,
            dob = ?,
            standard = ?
        WHERE id = ?
          AND role = 'Student'
          AND teacher_id = ?
    """, (
        student.full_name,
        student.phone,
        student.dob,
        student.standard,
        student_id,
        teacher_id
    ))

    connection.commit()
    connection.close()

    return {
        "success": True,
        "message": "Student updated successfully!"
    }