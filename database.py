import sqlite3
from datetime import datetime

DB_NAME = "rockville_club.db"


def get_connection():
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# =========================================================
# DATABASE INITIALIZATION
# =========================================================

def init_database():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            full_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT DEFAULT '',
            address TEXT DEFAULT '',
            emergency_contact TEXT DEFAULT '',
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'member',
            status TEXT NOT NULL DEFAULT 'pending',
            created_at TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS financial_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            category TEXT NOT NULL,
            amount REAL NOT NULL,
            description TEXT DEFAULT '',
            record_date TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender_id INTEGER NOT NULL,
            receiver_id INTEGER NOT NULL,
            message TEXT NOT NULL,
            is_read INTEGER DEFAULT 0,
            created_at TEXT NOT NULL,
            FOREIGN KEY(sender_id) REFERENCES users(id),
            FOREIGN KEY(receiver_id) REFERENCES users(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS admin_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            subject TEXT NOT NULL,
            message TEXT NOT NULL,
            status TEXT DEFAULT 'open',
            admin_response TEXT DEFAULT '',
            created_at TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS login_issues (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT NOT NULL,
            issue TEXT NOT NULL,
            status TEXT DEFAULT 'open',
            admin_response TEXT DEFAULT '',
            created_at TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS announcements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            author_id INTEGER NOT NULL,
            published INTEGER DEFAULT 1,
            created_at TEXT NOT NULL,
            FOREIGN KEY(author_id) REFERENCES users(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS password_recovery (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            token_hash TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            used INTEGER DEFAULT 0,
            created_at TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)

    # -----------------------------------------------------
    # Migration for older users table
    # -----------------------------------------------------

    cursor.execute("PRAGMA table_info(users)")

    columns = {
        row["name"]
        for row in cursor.fetchall()
    }

    extra_columns = {
        "phone": "TEXT DEFAULT ''",
        "address": "TEXT DEFAULT ''",
        "emergency_contact": "TEXT DEFAULT ''",
        "role": "TEXT DEFAULT 'member'",
        "status": "TEXT DEFAULT 'pending'",
        "created_at": "TEXT DEFAULT ''"
    }

    for column, definition in extra_columns.items():

        if column not in columns:

            cursor.execute(
                f"ALTER TABLE users ADD COLUMN {column} {definition}"
            )

    cursor.execute("""
        UPDATE users
        SET role = 'member'
        WHERE role IS NULL OR role = ''
    """)

    cursor.execute("""
        UPDATE users
        SET status = 'active'
        WHERE status IS NULL OR status = ''
    """)

    conn.commit()
    conn.close()


# =========================================================
# USERS
# =========================================================

def create_user(
    username,
    full_name,
    email,
    password_hash,
    role="member",
    status="pending"
):

    conn = get_connection()

    try:

        conn.execute("""
            INSERT INTO users (
                username,
                full_name,
                email,
                password_hash,
                role,
                status,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            username,
            full_name,
            email,
            password_hash,
            role,
            status,
            now()
        ))

        conn.commit()

        return True, "Account created successfully."

    except sqlite3.IntegrityError as error:

        text = str(error).lower()

        if "username" in text:
            return False, "Username already exists."

        if "email" in text:
            return False, "Email already exists."

        return False, "Unable to create account."

    finally:
        conn.close()


def get_user_by_username(username):

    conn = get_connection()

    user = conn.execute("""
        SELECT *
        FROM users
        WHERE LOWER(username) = LOWER(?)
    """, (username.strip(),)).fetchone()

    conn.close()

    return user


def get_user_by_email(email):

    conn = get_connection()

    user = conn.execute("""
        SELECT *
        FROM users
        WHERE LOWER(email) = LOWER(?)
    """, (email.strip(),)).fetchone()

    conn.close()

    return user


def get_user_by_id(user_id):

    conn = get_connection()

    user = conn.execute("""
        SELECT *
        FROM users
        WHERE id = ?
    """, (user_id,)).fetchone()

    conn.close()

    return user


def get_all_users():

    conn = get_connection()

    users = conn.execute("""
        SELECT *
        FROM users
        ORDER BY full_name ASC
    """).fetchall()

    conn.close()

    return users


def get_active_members():

    conn = get_connection()

    users = conn.execute("""
        SELECT *
        FROM users
        WHERE role = 'member'
        AND status = 'active'
        ORDER BY full_name ASC
    """).fetchall()

    conn.close()

    return users


def get_pending_users():

    conn = get_connection()

    users = conn.execute("""
        SELECT *
        FROM users
        WHERE status = 'pending'
        ORDER BY created_at DESC
    """).fetchall()

    conn.close()

    return users


def update_user_profile(
    user_id,
    full_name,
    email,
    phone,
    address,
    emergency_contact
):

    conn = get_connection()

    try:

        conn.execute("""
            UPDATE users
            SET
                full_name = ?,
                email = ?,
                phone = ?,
                address = ?,
                emergency_contact = ?
            WHERE id = ?
        """, (
            full_name,
            email,
            phone,
            address,
            emergency_contact,
            user_id
        ))

        conn.commit()

        return True, "Profile updated successfully."

    except sqlite3.IntegrityError:

        return False, "That email address is already in use."

    finally:
        conn.close()


def update_user_status(user_id, status):

    conn = get_connection()

    conn.execute("""
        UPDATE users
        SET status = ?
        WHERE id = ?
    """, (status, user_id))

    conn.commit()
    conn.close()


def update_password(user_id, password_hash):

    conn = get_connection()

    conn.execute("""
        UPDATE users
        SET password_hash = ?
        WHERE id = ?
    """, (password_hash, user_id))

    conn.commit()
    conn.close()


def delete_user(user_id):

    conn = get_connection()

    conn.execute(
        "DELETE FROM financial_records WHERE user_id = ?",
        (user_id,)
    )

    conn.execute(
        "DELETE FROM messages WHERE sender_id = ? OR receiver_id = ?",
        (user_id, user_id)
    )

    conn.execute(
        "DELETE FROM admin_messages WHERE user_id = ?",
        (user_id,)
    )

    conn.execute(
        "DELETE FROM login_issues WHERE user_id = ?",
        (user_id,)
    )

    conn.execute(
        "DELETE FROM password_recovery WHERE user_id = ?",
        (user_id,)
    )

    conn.execute(
        "DELETE FROM users WHERE id = ?",
        (user_id,)
    )

    conn.commit()
    conn.close()


def admin_exists():

    conn = get_connection()

    result = conn.execute("""
        SELECT id
        FROM users
        WHERE role = 'admin'
        LIMIT 1
    """).fetchone()

    conn.close()

    return result is not None


# =========================================================
# FINANCIAL RECORDS
# =========================================================

FINANCIAL_CATEGORIES = [
    "Savings",
    "Registration Fee",
    "Monthly Dues",
    "Fines",
    "Levy",
    "Donation",
    "Other"
]


def add_financial_record(
    user_id,
    category,
    amount,
    description,
    record_date
):

    conn = get_connection()

    conn.execute("""
        INSERT INTO financial_records (
            user_id,
            category,
            amount,
            description,
            record_date,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        user_id,
        category,
        amount,
        description,
        record_date,
        now()
    ))

    conn.commit()
    conn.close()


def get_user_financial_records(user_id, year):

    conn = get_connection()

    records = conn.execute("""
        SELECT *
        FROM financial_records
        WHERE user_id = ?
        AND strftime('%Y', record_date) = ?
        ORDER BY record_date DESC
    """, (
        user_id,
        str(year)
    )).fetchall()

    conn.close()

    return records


def get_all_financial_records():

    conn = get_connection()

    records = conn.execute("""
        SELECT
            financial_records.*,
            users.full_name,
            users.username
        FROM financial_records
        JOIN users
        ON financial_records.user_id = users.id
        ORDER BY record_date DESC
    """).fetchall()

    conn.close()

    return records


def update_financial_record(
    record_id,
    category,
    amount,
    description,
    record_date
):

    conn = get_connection()

    conn.execute("""
        UPDATE financial_records
        SET
            category = ?,
            amount = ?,
            description = ?,
            record_date = ?
        WHERE id = ?
    """, (
        category,
        amount,
        description,
        record_date,
        record_id
    ))

    conn.commit()
    conn.close()


def delete_financial_record(record_id):

    conn = get_connection()

    conn.execute("""
        DELETE FROM financial_records
        WHERE id = ?
    """, (record_id,))

    conn.commit()
    conn.close()


def get_member_financial_summary(user_id, year):

    conn = get_connection()

    rows = conn.execute("""
        SELECT
            category,
            COALESCE(SUM(amount), 0) AS total
        FROM financial_records
        WHERE user_id = ?
        AND strftime('%Y', record_date) = ?
        GROUP BY category
    """, (
        user_id,
        str(year)
    )).fetchall()

    conn.close()

    summary = {
        category: 0.0
        for category in FINANCIAL_CATEGORIES
    }

    for row in rows:
        summary[row["category"]] = row["total"]

    return summary


# =========================================================
# MEMBER / ADMIN MESSAGES
# =========================================================

def send_message(sender_id, receiver_id, message):

    conn = get_connection()

    conn.execute("""
        INSERT INTO messages (
            sender_id,
            receiver_id,
            message,
            is_read,
            created_at
        )
        VALUES (?, ?, ?, 0, ?)
    """, (
        sender_id,
        receiver_id,
        message,
        now()
    ))

    conn.commit()
    conn.close()


def get_user_messages(user_id):

    conn = get_connection()

    messages = conn.execute("""
        SELECT
            messages.*,
            sender.full_name AS sender_name,
            receiver.full_name AS receiver_name
        FROM messages
        JOIN users sender
            ON messages.sender_id = sender.id
        JOIN users receiver
            ON messages.receiver_id = receiver.id
        WHERE messages.sender_id = ?
        OR messages.receiver_id = ?
        ORDER BY messages.created_at ASC
    """, (
        user_id,
        user_id
    )).fetchall()

    conn.close()

    return messages


def get_conversation(user_id, other_user_id):

    conn = get_connection()

    messages = conn.execute("""
        SELECT
            messages.*,
            sender.full_name AS sender_name,
            receiver.full_name AS receiver_name
        FROM messages
        JOIN users sender
            ON messages.sender_id = sender.id
        JOIN users receiver
            ON messages.receiver_id = receiver.id
        WHERE
            (
                messages.sender_id = ?
                AND messages.receiver_id = ?
            )
            OR
            (
                messages.sender_id = ?
                AND messages.receiver_id = ?
            )
        ORDER BY messages.created_at ASC
    """, (
        user_id,
        other_user_id,
        other_user_id,
        user_id
    )).fetchall()

    conn.close()

    return messages


def mark_conversation_read(user_id, other_user_id):

    conn = get_connection()

    conn.execute("""
        UPDATE messages
        SET is_read = 1
        WHERE sender_id = ?
        AND receiver_id = ?
    """, (
        other_user_id,
        user_id
    ))

    conn.commit()
    conn.close()


def get_unread_count(user_id):

    conn = get_connection()

    result = conn.execute("""
        SELECT COUNT(*) AS total
        FROM messages
        WHERE receiver_id = ?
        AND is_read = 0
    """, (user_id,)).fetchone()

    conn.close()

    return result["total"]


def get_message_contacts(user_id):

    conn = get_connection()

    rows = conn.execute("""
        SELECT DISTINCT
            CASE
                WHEN sender_id = ?
                THEN receiver_id
                ELSE sender_id
            END AS contact_id
        FROM messages
        WHERE sender_id = ?
        OR receiver_id = ?
    """, (
        user_id,
        user_id,
        user_id
    )).fetchall()

    conn.close()

    contacts = []

    for row in rows:

        user = get_user_by_id(row["contact_id"])

        if user:
            contacts.append(user)

    return contacts


# =========================================================
# CONTACT ADMIN
# =========================================================

def create_admin_message(user_id, subject, message):

    conn = get_connection()

    conn.execute("""
        INSERT INTO admin_messages (
            user_id,
            subject,
            message,
            status,
            created_at
        )
        VALUES (?, ?, ?, 'open', ?)
    """, (
        user_id,
        subject,
        message,
        now()
    ))

    conn.commit()
    conn.close()


def get_admin_messages():

    conn = get_connection()

    messages = conn.execute("""
        SELECT
            admin_messages.*,
            users.full_name,
            users.username
        FROM admin_messages
        JOIN users
        ON admin_messages.user_id = users.id
        ORDER BY admin_messages.created_at DESC
    """).fetchall()

    conn.close()

    return messages


def resolve_admin_message(message_id, response):

    conn = get_connection()

    conn.execute("""
        UPDATE admin_messages
        SET
            status = 'resolved',
            admin_response = ?
        WHERE id = ?
    """, (
        message_id,
        response
    ))

    conn.commit()
    conn.close()


# =========================================================
# LOGIN ISSUES
# =========================================================

def create_login_issue(user_id, username, issue):

    conn = get_connection()

    conn.execute("""
        INSERT INTO login_issues (
            user_id,
            username,
            issue,
            status,
            created_at
        )
        VALUES (?, ?, ?, 'open', ?)
    """, (
        user_id,
        username,
        issue,
        now()
    ))

    conn.commit()
    conn.close()


def get_login_issues():

    conn = get_connection()

    issues = conn.execute("""
        SELECT
            login_issues.*,
            users.full_name
        FROM login_issues
        LEFT JOIN users
        ON login_issues.user_id = users.id
        ORDER BY login_issues.created_at DESC
    """).fetchall()

    conn.close()

    return issues


def resolve_login_issue(issue_id, response):

    conn = get_connection()

    conn.execute("""
        UPDATE login_issues
        SET
            status = 'resolved',
            admin_response = ?
        WHERE id = ?
    """, (
        issue_id,
        response
    ))

    conn.commit()
    conn.close()


# =========================================================
# ANNOUNCEMENTS
# =========================================================

def create_announcement(title, content, author_id):

    conn = get_connection()

    conn.execute("""
        INSERT INTO announcements (
            title,
            content,
            author_id,
            published,
            created_at
        )
        VALUES (?, ?, ?, 1, ?)
    """, (
        title,
        content,
        author_id,
        now()
    ))

    conn.commit()
    conn.close()


def get_announcements():

    conn = get_connection()

    rows = conn.execute("""
        SELECT
            announcements.*,
            users.full_name AS author_name
        FROM announcements
        JOIN users
        ON announcements.author_id = users.id
        WHERE published = 1
        ORDER BY created_at DESC
    """).fetchall()

    conn.close()

    return rows


def get_all_announcements():

    conn = get_connection()

    rows = conn.execute("""
        SELECT
            announcements.*,
            users.full_name AS author_name
        FROM announcements
        JOIN users
        ON announcements.author_id = users.id
        ORDER BY created_at DESC
    """).fetchall()

    conn.close()

    return rows


def update_announcement(
    announcement_id,
    title,
    content,
    published
):

    conn = get_connection()

    conn.execute("""
        UPDATE announcements
        SET
            title = ?,
            content = ?,
            published = ?
        WHERE id = ?
    """, (
        title,
        content,
        published,
        announcement_id
    ))

    conn.commit()
    conn.close()


def delete_announcement(announcement_id):

    conn = get_connection()

    conn.execute("""
        DELETE FROM announcements
        WHERE id = ?
    """, (announcement_id,))

    conn.commit()
    conn.close()


# =========================================================
# PASSWORD RECOVERY
# =========================================================

def create_recovery_request(
    user_id,
    token_hash,
    expires_at
):

    conn = get_connection()

    conn.execute("""
        INSERT INTO password_recovery (
            user_id,
            token_hash,
            expires_at,
            used,
            created_at
        )
        VALUES (?, ?, ?, 0, ?)
    """, (
        user_id,
        token_hash,
        expires_at,
        now()
    ))

    conn.commit()
    conn.close()


def get_valid_recovery_request(token_hash):

    conn = get_connection()

    request = conn.execute("""
        SELECT *
        FROM password_recovery
        WHERE token_hash = ?
        AND used = 0
        AND expires_at > ?
        ORDER BY created_at DESC
        LIMIT 1
    """, (
        token_hash,
        now()
    )).fetchone()

    conn.close()

    return request


def mark_recovery_used(request_id):

    conn = get_connection()

    conn.execute("""
        UPDATE password_recovery
        SET used = 1
        WHERE id = ?
    """, (request_id,))

    conn.commit()
    conn.close()
