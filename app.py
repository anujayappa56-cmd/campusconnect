from flask import Flask, render_template, request, redirect, session, Response
import sqlite3
import csv
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'secret123'

# ---------------- HOME ----------------
@app.route('/')
def home():
    return render_template('home.html')

# ---------------- ABOUT ----------------
@app.route('/about')
def about():
    return render_template('about.html')


# ---------------- SIGNUP ----------------
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    message = ""
    subjects = ["PHP", "AI", "Data Mining", "Fundamentals Of Data Science", "WCMS"]

    if request.method == 'POST':
        student_id = request.form.get('student_id')
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']
        subject = request.form.get('subject')

        conn = sqlite3.connect('college.db')
        cursor = conn.cursor()

        if role == 'hod':
            cursor.execute("SELECT * FROM users WHERE role='hod'")
            if cursor.fetchone():
                message = "HOD already exists!"
            else:
                cursor.execute("INSERT INTO users VALUES (?, ?, ?, ?, ?)", (None, username, password, role, None))
                conn.commit()
                session['user'] = username
                session['role'] = role
                conn.close()
                return redirect('/dashboard')

        elif role == 'lecturer':
            if not subject:
                message = "Select subject!"
            else:
                cursor.execute("SELECT * FROM users WHERE subject=?", (subject,))
                if cursor.fetchone():
                    message = "Subject already assigned!"
                else:
                    cursor.execute("INSERT INTO users VALUES (?, ?, ?, ?, ?)", (None, username, password, role, subject))
                    conn.commit()
                    session['user'] = username
                    session['role'] = role
                    conn.close()
                    return redirect('/dashboard')

        elif role == 'student':
            if not student_id:
                message = "Student ID required!"
            else:
                cursor.execute("SELECT * FROM users WHERE student_id=?", (student_id,))
                if cursor.fetchone():
                    message = "Student already exists!"
                else:
                    cursor.execute("INSERT INTO users VALUES (?, ?, ?, ?, ?)", (student_id, username, password, role, None))

                    for sub in subjects:
                        cursor.execute(
                            "INSERT OR IGNORE INTO attendance (student_id, username, subject) VALUES (?, ?, ?)",
                            (student_id, username, sub)
                        )

                    conn.commit()
                    session['user'] = username
                    session['role'] = role
                    conn.close()
                    return redirect('/dashboard')

        conn.close()

    return render_template('signup.html', message=message, subjects=subjects)


# ---------------- LOGIN ----------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    message = ""

    if request.method == 'POST':
        student_id = request.form.get('student_id')
        username = request.form.get('username')
        password = request.form['password']

        conn = sqlite3.connect('college.db')
        cursor = conn.cursor()

        if student_id:
            cursor.execute("SELECT * FROM users WHERE student_id=?", (student_id,))
        else:
            cursor.execute("SELECT * FROM users WHERE username=?", (username,))

        user = cursor.fetchone()
        conn.close()

        if user and user[2] == password:
            session['user'] = user[1]
            session['role'] = user[3]
            return redirect('/dashboard')
        else:
            message = "Invalid credentials!"

    return render_template('login.html', message=message)


# ---------------- FORGOT PASSWORD ----------------
@app.route('/forgot', methods=['GET', 'POST'])
def forgot():
    message = ""

    if request.method == 'POST':
        role = request.form.get('role')
        username = request.form.get('username')
        new_password = request.form.get('new_password')

        conn = sqlite3.connect('college.db')
        cursor = conn.cursor()

        if role == 'student':
            student_id = request.form.get('student_id')
            cursor.execute("SELECT * FROM users WHERE student_id=? AND username=?", (student_id, username))
            if cursor.fetchone():
                cursor.execute("UPDATE users SET password=? WHERE student_id=?", (new_password, student_id))
                conn.commit()
                message = "Password updated successfully!"
            else:
                message = "Invalid Student details!"

        elif role == 'lecturer':
            subject = request.form.get('subject')
            cursor.execute("SELECT * FROM users WHERE subject=? AND username=?", (subject, username))
            if cursor.fetchone():
                cursor.execute("UPDATE users SET password=? WHERE subject=?", (new_password, subject))
                conn.commit()
                message = "Password updated successfully!"
            else:
                message = "Invalid Lecturer details!"

        elif role == 'hod':
            cursor.execute("SELECT * FROM users WHERE role='hod' AND username=?", (username,))
            if cursor.fetchone():
                cursor.execute("UPDATE users SET password=? WHERE username=?", (new_password, username))
                conn.commit()
                message = "Password updated successfully!"
            else:
                message = "Invalid HOD details!"

        conn.close()

    return render_template('forgot.html', message=message)


# ---------------- EXAM RESULTS ----------------
@app.route('/exam_results', methods=['GET', 'POST'])
def exam_results():

    if 'user' not in session:
        return redirect('/login')

    role = session.get('role')

    conn = sqlite3.connect('college.db')
    cursor = conn.cursor()

    # ================= STUDENT =================
    if role == 'student':

        cursor.execute("SELECT student_id FROM users WHERE username=?", (session['user'],))
        student_id = cursor.fetchone()[0]

        cursor.execute("""
            SELECT subject, marks_obtained, total_marks
            FROM results
            WHERE student_id=?
        """, (student_id,))

        records = cursor.fetchall()
        conn.close()

        return render_template('exam_results.html', records=records)

    # ================= LECTURER =================
    elif role == 'lecturer':

        cursor.execute("SELECT subject FROM users WHERE username=?", (session['user'],))
        subject = cursor.fetchone()[0]

        cursor.execute("SELECT student_id, username FROM users WHERE role='student'")
        students = cursor.fetchall()

        # SAVE MARKS
        if request.method == 'POST':
            for student in students:
                student_id = student[0]

                marks = request.form.get(f'marks_{student_id}')
                total = request.form.get(f'total_{student_id}')

                if marks and total:
                    cursor.execute("""
                        INSERT OR REPLACE INTO results (student_id, subject, marks_obtained, total_marks)
                        VALUES (?, ?, ?, ?)
                    """, (student_id, subject, marks, total))

            conn.commit()

        # FETCH UPDATED DATA
        cursor.execute("""
            SELECT student_id, subject, marks_obtained, total_marks
            FROM results
            WHERE subject=?
        """, (subject,))

        records = cursor.fetchall()
        conn.close()

        return render_template(
            'lecturer_results.html',
            students=students,
            subject=subject,
            records=records
        )

    else:
        conn.close()
        return "Unauthorized"



# ---------------- CHECK DATABASE ----------------
@app.route('/check_db')
def check_db():
    conn = sqlite3.connect('college.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM attendance")
    data = cursor.fetchall()
    conn.close()
    return str(data)


# ---------------- DASHBOARD ----------------
@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect('/login')

    role = session.get('role')

    conn = sqlite3.connect('college.db')
    cursor = conn.cursor()
    cursor.execute("SELECT message FROM announcements ORDER BY id DESC LIMIT 1")
    announcement = cursor.fetchone()
    conn.close()

    if role == 'hod':
        return render_template('dashboard_hod.html', announcement=announcement)
    elif role == 'lecturer':
        return render_template('dashboard_lecturer.html', announcement=announcement)
    else:
        return render_template('dashboard_student.html', announcement=announcement)


# ---------------- DELETE ACCOUNT ----------------
@app.route('/delete_account')
def delete_account():
    if 'user' not in session:
        return redirect('/login')

    conn = sqlite3.connect('college.db')
    cursor = conn.cursor()

    username = session['user']
    role = session['role']

    cursor.execute("SELECT student_id FROM users WHERE username=?", (username,))
    result = cursor.fetchone()
    student_id = result[0] if result else None

    # Delete user
    cursor.execute("DELETE FROM users WHERE username=?", (username,))

    # If student → delete all related data
    if role == 'student' and student_id:
        cursor.execute("DELETE FROM attendance WHERE student_id=?", (student_id,))
        cursor.execute("DELETE FROM voters WHERE student_id=?", (student_id,))
        cursor.execute("DELETE FROM votes WHERE student_id=?", (student_id,))
        cursor.execute("DELETE FROM results WHERE student_id=?", (student_id,))

    conn.commit()
    conn.close()

    session.clear()
    return redirect('/')

# ---------------- HOD ANNOUNCEMENT ----------------
@app.route('/hod_announcement', methods=['POST'])
def hod_announcement():
    if 'user' not in session or session.get('role') != 'hod':
        return redirect('/login')

    title = request.form['title']
    message = request.form['message']
    file = request.files.get('file')
    filename = None

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        if not os.path.exists(app.config['UPLOAD_FOLDER']):
            os.makedirs(app.config['UPLOAD_FOLDER'])
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = sqlite3.connect('college.db')
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO announcements (title, message, file, created_at)
        VALUES (?, ?, ?, ?)
    """, (title, message, filename, created_at))
    conn.commit()
    conn.close()
    return redirect('/announcements')

# ---------------- ANNOUNCEMENTS ----------------
@app.route('/announcements')
def announcements():
    if 'user' not in session:
        return redirect('/login')
    role = session.get('role')
    conn = sqlite3.connect('college.db')
    cursor = conn.cursor()
    cursor.execute("SELECT title, message, file, created_at FROM announcements ORDER BY id DESC")
    all_announcements = cursor.fetchall()
    conn.close()
    return render_template('announcement.html', announcements=all_announcements, role=role)


# ---------------- ATTENDANCE ----------------
@app.route('/attendance')
def attendance_page():

    if 'user' not in session:
        return redirect('/login')

    role = session.get('role')

    # ================= STUDENT =================
    if role == 'student':

        conn = sqlite3.connect('college.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT student_id FROM users WHERE username=?", (session['user'],))
        student_id = cursor.fetchone()[0]

        cursor.execute("""
            SELECT subject,
                   COALESCE(classes_held, 0) AS classes_held,
                   COALESCE(classes_attended, 0) AS classes_attended
            FROM attendance
            WHERE student_id=?
        """, (student_id,))

        rows = cursor.fetchall()
        conn.close()

        records = []
        for row in rows:
            held = row['classes_held']
            attended = row['classes_attended']
            absent = held - attended
            percentage = round((attended / held) * 100, 2) if held > 0 else 0

            records.append({
                "subject": row['subject'],
                "held": held,
                "attended": attended,
                "absent": absent,
                "percentage": percentage
            })

        return render_template('student_attendance.html', records=records)

    # ================= LECTURER =================
    elif role == 'lecturer':

        conn = sqlite3.connect('college.db')
        cursor = conn.cursor()

        cursor.execute("SELECT subject FROM users WHERE username=?", (session['user'],))
        subject = cursor.fetchone()[0]

        cursor.execute("SELECT student_id, username FROM users WHERE role='student'")
        students = cursor.fetchall()

        conn.close()

        return render_template(
            'lecturer_attendance.html',
            students=students,
            subject=subject
        )

    # ================= OTHER =================
    else:
        return "Unauthorized Access"

# ---------------- SUBMIT ATTENDANCE ----------------
@app.route('/submit_attendance', methods=['POST'])
def submit_attendance():

    if 'user' not in session or session.get('role') != 'lecturer':
        return redirect('/login')

    conn = sqlite3.connect('college.db')
    cursor = conn.cursor()

    # Get lecturer subject
    cursor.execute("SELECT subject FROM users WHERE username=?", (session['user'],))
    subject = cursor.fetchone()[0]

    # Get all students
    cursor.execute("SELECT student_id FROM users WHERE role='student'")
    students = cursor.fetchall()

    for student in students:
        student_id = student[0]

        status = request.form.get(f'att_{student_id}')

        # Ensure record exists
        cursor.execute("""
            INSERT OR IGNORE INTO attendance (student_id, subject, classes_held, classes_attended)
            VALUES (?, ?, 0, 0)
        """, (student_id, subject))

        # Increase classes held
        cursor.execute("""
            UPDATE attendance
            SET classes_held = classes_held + 1
            WHERE student_id=? AND subject=?
        """, (student_id, subject))

        # If present → increase attended
        if status == 'present':
            cursor.execute("""
                UPDATE attendance
                SET classes_attended = classes_attended + 1
                WHERE student_id=? AND subject=?
            """, (student_id, subject))

    conn.commit()
    conn.close()

    return redirect('/attendance')


# ---------------- ATTENDANCE DATA (NEWLY ADDED) ----------------
@app.route('/attendance_data')
def attendance_data():
    if 'user' not in session or session.get('role') != 'student':
        return []

    conn = sqlite3.connect('college.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT student_id FROM users WHERE username=?", (session['user'],))
    student_id = cursor.fetchone()[0]

    cursor.execute("""
        SELECT subject,
               COALESCE(classes_held, 0) AS classes_held,
               COALESCE(classes_attended, 0) AS classes_attended
        FROM attendance
        WHERE student_id=?
    """, (student_id,))

    rows = cursor.fetchall()
    conn.close()

    data = []

    for row in rows:
        held = row['classes_held']
        attended = row['classes_attended']

        data.append({
            "subject": row['subject'],
            "held": held,
            "attended": attended
        })

    from flask import jsonify   # 👈 ADD THIS LINE
    return jsonify(data)        # 👈 CHANGE THIS LINE


# ---------------- HOD VIEW ATTENDANCE ----------------
@app.route('/hod_attendance', methods=['GET', 'POST'])
def hod_attendance():
    if 'user' not in session or session.get('role') != 'hod':
        return redirect('/login')

    search_id = request.form.get('student_id')
    filter_low = request.form.get('low_attendance')

    conn = sqlite3.connect('college.db')
    cursor = conn.cursor()

    query = "SELECT student_id, subject, classes_held, classes_attended FROM attendance"
    params = []

    if search_id:
        query += " WHERE student_id=?"
        params.append(search_id)

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    records = []
    for row in rows:
        student_id, subject, held, attended = row
        absent = held - attended
        percentage = round((attended / held) * 100, 2) if held > 0 else 0

        if filter_low and percentage >= 70:
            continue

        records.append({
            "student_id": student_id,
            "subject": subject,
            "held": held,
            "attended": attended,
            "absent": absent,
            "percentage": percentage
        })

    return render_template('hod_attendance.html', records=records)


# ---------------- ADD CANDIDATES ----------------
@app.route('/add_candidates')
def add_candidates():
    if 'user' not in session or session.get('role') != 'hod':
        return "Access Denied"

    conn = sqlite3.connect('college.db')
    cursor = conn.cursor()

    cursor.execute("SELECT student_id, username FROM users WHERE role='student'")
    students = cursor.fetchall()

    cursor.execute("SELECT student_id, candidate_name, votes FROM votes")
    candidates = cursor.fetchall()

    cursor.execute("SELECT COUNT(*) FROM users WHERE role='student'")
    total_students = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM voters")
    voted_students = cursor.fetchone()[0]

    conn.close()

    return render_template(
        'add_candidates.html',
        students=students,
        candidates=candidates,
        total_students=total_students,
        voted_students=voted_students
    )


# ---------------- ADD CANDIDATES POST ----------------
@app.route('/hod_add_candidates', methods=['POST'])
def hod_add_candidates():
    if 'user' not in session or session.get('role') != 'hod':
        return "Access Denied"

    selected_ids = request.form.getlist('student_ids')

    conn = sqlite3.connect('college.db')
    cursor = conn.cursor()

    for sid in selected_ids:
        cursor.execute("SELECT username FROM users WHERE student_id=?", (sid,))
        name = cursor.fetchone()[0]

        cursor.execute("SELECT * FROM votes WHERE student_id=?", (sid,))
        if not cursor.fetchone():
            cursor.execute(
                "INSERT INTO votes (student_id, candidate_name, votes) VALUES (?, ?, 0)",
                (sid, name)
            )

    conn.commit()
    conn.close()
    return redirect('/add_candidates')


# ---------------- VOTE ----------------
@app.route('/vote')
def vote():
    if 'user' not in session or session.get('role') != 'student':
        return redirect('/login')

    conn = sqlite3.connect('college.db')
    cursor = conn.cursor()

    cursor.execute("SELECT student_id FROM users WHERE username=?", (session['user'],))
    student_id = cursor.fetchone()[0]

    cursor.execute("SELECT * FROM announcements WHERE message LIKE '%Winner%'")
    if cursor.fetchone():
        conn.close()
        return "Voting Closed. Results already announced."

    cursor.execute("SELECT * FROM voters WHERE student_id=?", (student_id,))
    voted = cursor.fetchone()

    cursor.execute("SELECT student_id, candidate_name FROM votes")
    candidates = cursor.fetchall()

    conn.close()

    return render_template('student_vote.html', candidates=candidates, voted=voted)


# ---------------- CAST VOTE ----------------
@app.route('/cast_vote/<candidate_id>')
def cast_vote(candidate_id):
    if 'user' not in session or session.get('role') != 'student':
        return redirect('/login')

    conn = sqlite3.connect('college.db')
    cursor = conn.cursor()

    cursor.execute("SELECT student_id FROM users WHERE username=?", (session['user'],))
    student_id = cursor.fetchone()[0]

    cursor.execute("SELECT * FROM voters WHERE student_id=?", (student_id,))
    if cursor.fetchone():
        conn.close()
        return redirect('/vote')

    cursor.execute("UPDATE votes SET votes = votes + 1 WHERE student_id=?", (candidate_id,))
    cursor.execute("INSERT INTO voters (student_id) VALUES (?)", (student_id,))

    conn.commit()
    conn.close()

    return redirect('/vote')


# ---------------- ANNOUNCE RESULTS ----------------
@app.route('/announce_results')
def announce_results():
    if 'user' not in session or session.get('role') != 'hod':
        return redirect('/login')

    conn = sqlite3.connect('college.db')
    cursor = conn.cursor()

    cursor.execute("SELECT candidate_name, votes FROM votes ORDER BY votes DESC")
    results = cursor.fetchall()

    if not results:
        conn.close()
        return redirect('/add_candidates')

    winner = results[0]

    message = "🏆 Election Results:\n\n"
    for r in results:
        message += f"{r[0]} - {r[1]} votes\n"

    message += f"\n🎉 Winner: {winner[0]}"

    cursor.execute("INSERT INTO announcements (message) VALUES (?)", (message,))
    conn.commit()
    conn.close()

    return redirect('/announcements')


# ---------------- RESET ELECTION ----------------
@app.route('/reset_election')
def reset_election():
    if 'user' not in session or session.get('role') != 'hod':
        return redirect('/login')

    conn = sqlite3.connect('college.db')
    cursor = conn.cursor()

    cursor.execute("DELETE FROM votes")
    cursor.execute("DELETE FROM voters")
    cursor.execute("DELETE FROM announcements WHERE message LIKE '%Election Results%'")

    conn.commit()
    conn.close()

    return redirect('/add_candidates')


# ---------------- LOGOUT ----------------
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')


# ---------------- RUN ----------------
if __name__ == '__main__':
    print("🚀 Server running...")
    app.run(host="0.0.0.0", port=10000)