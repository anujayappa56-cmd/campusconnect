import sqlite3

conn = sqlite3.connect('college.db')
cursor = conn.cursor()

# ---------------- USERS ----------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    student_id TEXT UNIQUE,
    username TEXT,
    password TEXT,
    role TEXT,
    subject TEXT
)
""")

# ---------------- ATTENDANCE ----------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS attendance (
    student_id TEXT,
    username TEXT,
    subject TEXT,
    classes_held INTEGER DEFAULT 0,
    classes_attended INTEGER DEFAULT 0,
    PRIMARY KEY (student_id, subject)
)
""")

# ---------------- VOTES ----------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS votes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id TEXT UNIQUE,
    candidate_name TEXT,
    votes INTEGER DEFAULT 0
)
""")

# ---------------- VOTERS ----------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS voters (
    student_id TEXT PRIMARY KEY
)
""")

# ---------------- SUBJECTS ----------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS subjects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subject_name TEXT UNIQUE
)
""")

# ---------------- ANNOUNCEMENTS (UPGRADED) ----------------
# Add title, file, created_at columns for full functionality
cursor.execute("""
CREATE TABLE IF NOT EXISTS announcements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    message TEXT,
    file TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

# ---------------- RESULTS ----------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id TEXT,
    subject TEXT,
    marks_obtained INTEGER,
    total_marks INTEGER
)
""")

# ---------------- INSERT SUBJECTS ----------------
subjects = ["PHP", "AI", "Data Mining", "Fundamentals Of Data Science", "WCMS"]

for sub in subjects:
    cursor.execute("INSERT OR IGNORE INTO subjects (subject_name) VALUES (?)", (sub,))

conn.commit()
conn.close()

print("✅ Full database setup complete with all tables and upgraded announcements!")