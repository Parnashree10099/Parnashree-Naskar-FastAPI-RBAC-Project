import sqlite3

connection = sqlite3.connect("users.db")

cursor = connection.cursor()

# Create users table
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    full_name TEXT NOT NULL,

    email TEXT UNIQUE NOT NULL,

    phone TEXT NOT NULL,

    dob TEXT NOT NULL,

    password TEXT NOT NULL,

    is_verified INTEGER DEFAULT 0,

    otp TEXT,

    role TEXT NOT NULL DEFAULT 'Student',

    subject TEXT,

    standard TEXT,

    teacher_id INTEGER,

must_change_password INTEGER DEFAULT 0,

login_otp TEXT
)
""")

# Check which columns already exist
cursor.execute("PRAGMA table_info(users)")
columns = [column[1] for column in cursor.fetchall()]

# Add new columns if they don't already exist
if "role" not in columns:
    cursor.execute(
        "ALTER TABLE users ADD COLUMN role TEXT NOT NULL DEFAULT 'Student'"
    )

if "subject" not in columns:
    cursor.execute(
        "ALTER TABLE users ADD COLUMN subject TEXT"
    )

if "standard" not in columns:
    cursor.execute(
        "ALTER TABLE users ADD COLUMN standard TEXT"
    )

if "teacher_id" not in columns:
    cursor.execute(
        "ALTER TABLE users ADD COLUMN teacher_id INTEGER"
    )
if "must_change_password" not in columns:
    cursor.execute(
        "ALTER TABLE users ADD COLUMN must_change_password INTEGER DEFAULT 0"
    )

if "login_otp" not in columns:
    cursor.execute(
        "ALTER TABLE users ADD COLUMN login_otp TEXT"
    )
connection.commit()
connection.close()

print("Database setup completed successfully!")