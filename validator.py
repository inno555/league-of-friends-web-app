import hashlib
import secrets
import re
from datetime import datetime, timedelta

from database import (
    create_user,
    get_user_by_username,
    update_password,
    get_connection,
)


# =========================================================
# DEFAULT ADMIN
# =========================================================

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "Admin@123"


# =========================================================
# PASSWORD HASHING
# =========================================================

def hash_password(password):
    """
    Securely hash a password using PBKDF2-HMAC-SHA256.
    """

    salt = secrets.token_hex(16)

    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        100_000,
    ).hex()

    return f"{salt}${password_hash}"


def verify_password(password, stored_password):
    """
    Verify a password against its stored hash.
    """

    try:

        salt, stored_hash = stored_password.split("$")

        password_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            100_000,
        ).hex()

        return secrets.compare_digest(
            password_hash,
            stored_hash,
        )

    except (ValueError, AttributeError):

        return False


# =========================================================
# EMAIL VALIDATION
# =========================================================

def validate_email(email):

    pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"

    return re.match(
        pattern,
        email,
    ) is not None


# =========================================================
# REGISTRATION VALIDATION
# =========================================================

def validate_registration(
    full_name,
    username,
    email,
    password,
    confirm_password,
):

    if not full_name.strip():

        return False, "Full name is required."

    if not username.strip():

        return False, "Username is required."

    if not email.strip():

        return False, "Email address is required."

    if not validate_email(email):

        return False, "Enter a valid email address."

    if len(password) < 6:

        return (
            False,
            "Password must be at least 6 characters.",
        )

    if password != confirm_password:

        return False, "Passwords do not match."

    return True, ""


# =========================================================
# REGISTER USER
# =========================================================

def register_user(
    full_name,
    username,
    email,
    password,
    confirm_password,
):

    valid, message = validate_registration(
        full_name,
        username,
        email,
        password,
        confirm_password,
    )

    if not valid:

        return False, message

    password_hash = hash_password(password)

    return create_user(
        username=username.strip(),
        full_name=full_name.strip(),
        email=email.strip().lower(),
        password_hash=password_hash,
        role="member",
        status="pending",
    )


# =========================================================
# LOGIN
# =========================================================

def login_user(username, password):

    if not username or not password:

        return (
            None,
            "Username and password are required.",
        )

    user = get_user_by_username(
        username.strip()
    )

    if not user:

        return (
            None,
            "Invalid username or password.",
        )

    stored_password = user["password_hash"]

    if not verify_password(
        password,
        stored_password,
    ):

        return (
            None,
            "Invalid username or password.",
        )

    # -----------------------------------------------------
    # ACCOUNT STATUS
    # -----------------------------------------------------

    status = user["status"]

    if status == "pending":

        return (
            None,
            "Your registration is awaiting administrator approval.",
        )

    if status == "rejected":

        return (
            None,
            "Your registration was rejected by the administrator.",
        )

    if status == "suspended":

        return (
            None,
            "Your account has been suspended. "
            "Please contact the club administrator.",
        )

    if status != "active":

        return (
            None,
            "Your account is not active.",
        )

    # -----------------------------------------------------
    # SUCCESS
    # -----------------------------------------------------

    return {
        "id": user["id"],
        "username": user["username"],
        "full_name": user["full_name"],
        "email": user["email"],
        "phone": user["phone"] or "",
        "address": user["address"] or "",
        "emergency_contact": (
            user["emergency_contact"] or ""
        ),
        "role": user["role"],
        "status": user["status"],
    }, ""


# =========================================================
# ADMIN PASSWORD RESET
# =========================================================

def reset_user_password(
    user_id,
    new_password,
    confirm_password,
):

    if len(new_password) < 6:

        return (
            False,
            "Password must be at least 6 characters.",
        )

    if new_password != confirm_password:

        return (
            False,
            "Passwords do not match.",
        )

    update_password(
        user_id,
        hash_password(new_password),
    )

    return (
        True,
        "Password reset successfully.",
    )


# =========================================================
# PASSWORD RECOVERY TABLE
# =========================================================

def create_recovery_table():

    conn = get_connection()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS password_recovery (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            token TEXT UNIQUE NOT NULL,
            expires_at TEXT NOT NULL,
            used INTEGER DEFAULT 0,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id)
                REFERENCES users(id)
        )
    """)

    conn.commit()
    conn.close()


# Make sure the table exists whenever validator.py is loaded.
create_recovery_table()


# =========================================================
# REQUEST PASSWORD RECOVERY
# =========================================================

def request_password_recovery(email):
    """
    Create a secure one-time recovery token.

    In the current development version the token is returned
    to Streamlit so it can be displayed for testing.

    In production, send this token through email instead.
    """

    if not email:

        return (
            False,
            "Email address is required.",
            None,
        )

    email = email.strip().lower()

    conn = get_connection()

    user = conn.execute("""
        SELECT *
        FROM users
        WHERE LOWER(email) = ?
        LIMIT 1
    """, (
        email,
    )).fetchone()

    if not user:

        conn.close()

        # Do not reveal whether an email exists.
        return (
            True,
            "If the email exists, recovery instructions "
            "have been generated.",
            None,
        )

    # -----------------------------------------------------
    # Remove old unused tokens for this user
    # -----------------------------------------------------

    conn.execute("""
        UPDATE password_recovery
        SET used = 1
        WHERE user_id = ?
        AND used = 0
    """, (
        user["id"],
    ))

    # -----------------------------------------------------
    # Generate secure token
    # -----------------------------------------------------

    token = secrets.token_urlsafe(32)

    expires_at = (
        datetime.now() + timedelta(minutes=30)
    ).strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    created_at = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    conn.execute("""
        INSERT INTO password_recovery (
            user_id,
            token,
            expires_at,
            used,
            created_at
        )
        VALUES (?, ?, ?, 0, ?)
    """, (
        user["id"],
        token,
        expires_at,
        created_at,
    ))

    conn.commit()
    conn.close()

    return (
        True,
        "Recovery request created.",
        token,
    )


# =========================================================
# RESET PASSWORD WITH RECOVERY TOKEN
# =========================================================

def reset_password_with_token(
    token,
    new_password,
    confirm_password,
):

    if not token:

        return (
            False,
            "Recovery token is required.",
        )

    if len(new_password) < 6:

        return (
            False,
            "Password must be at least 6 characters.",
        )

    if new_password != confirm_password:

        return (
            False,
            "Passwords do not match.",
        )

    conn = get_connection()

    recovery = conn.execute("""
        SELECT *
        FROM password_recovery
        WHERE token = ?
        AND used = 0
        LIMIT 1
    """, (
        token.strip(),
    )).fetchone()

    if not recovery:

        conn.close()

        return (
            False,
            "Invalid or already-used recovery token.",
        )

    # -----------------------------------------------------
    # Check expiration
    # -----------------------------------------------------

    try:

        expires_at = datetime.strptime(
            recovery["expires_at"],
            "%Y-%m-%d %H:%M:%S",
        )

    except ValueError:

        conn.close()

        return (
            False,
            "Invalid recovery token.",
        )

    if datetime.now() > expires_at:

        conn.execute("""
            UPDATE password_recovery
            SET used = 1
            WHERE id = ?
        """, (
            recovery["id"],
        ))

        conn.commit()
        conn.close()

        return (
            False,
            "This recovery token has expired.",
        )

    # -----------------------------------------------------
    # Update password
    # -----------------------------------------------------

    password_hash = hash_password(
        new_password
    )

    conn.execute("""
        UPDATE users
        SET password_hash = ?
        WHERE id = ?
    """, (
        password_hash,
        recovery["user_id"],
    ))

    # -----------------------------------------------------
    # Mark token as used
    # -----------------------------------------------------

    conn.execute("""
        UPDATE password_recovery
        SET used = 1
        WHERE id = ?
    """, (
        recovery["id"],
    ))

    conn.commit()
    conn.close()

    return (
        True,
        "Your password has been changed successfully.",
    )