from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector
from werkzeug.security import check_password_hash
from dotenv import load_dotenv
import os
load_dotenv()
app = Flask(__name__)
app.secret_key = "student-task-attendance-secret-key"
def get_database_connection():
    connection = mysql.connector.connect(
        host="localhost",
        user="root",
        password=os.getenv("Manasa_0207"),
        database="student_system"
    )
    return connection
@app.route("/")
def home():
    return redirect(url_for("login"))
@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        connection = get_database_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            "SELECT * FROM users WHERE email = %s",
            (email,)
        )

        user = cursor.fetchone()

        cursor.close()
        connection.close()

        # Check login details
        if user and check_password_hash(user["password"], password):

            session["user_id"] = user["id"]
            session["name"] = user["name"]
            session["email"] = user["email"]
            session["role"] = user["role"]

            return redirect(url_for("dashboard"))

        else:
            flash("Invalid email or password")

    return render_template("login.html")

@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect(url_for("login"))

    connection = get_database_connection()
    cursor = connection.cursor(dictionary=True)

    # STUDENT DASHBOARD
    if session["role"] == "student":

        # Total tasks
        cursor.execute("""
            SELECT COUNT(*) AS total_tasks
            FROM tasks
            JOIN students
                ON tasks.student_id = students.id
            WHERE students.user_id = %s
        """, (session["user_id"],))

        total_tasks = cursor.fetchone()["total_tasks"]

        # Completed tasks
        cursor.execute("""
            SELECT COUNT(*) AS completed_tasks
            FROM tasks
            JOIN students
                ON tasks.student_id = students.id
            WHERE students.user_id = %s
            AND tasks.status = 'Completed'
        """, (session["user_id"],))

        completed_tasks = cursor.fetchone()["completed_tasks"]

        # Pending tasks
        pending_tasks = total_tasks - completed_tasks

        # Attendance
        cursor.execute("""
            SELECT attendance.status
            FROM attendance
            JOIN students
                ON attendance.student_id = students.id
            WHERE students.user_id = %s
        """, (session["user_id"],))

        attendance_records = cursor.fetchall()

        total_attendance = len(attendance_records)
        present_count = 0

        for record in attendance_records:
            if record["status"] == "Present":
                present_count += 1

        if total_attendance > 0:
            attendance_percentage = (
                present_count / total_attendance
            ) * 100
        else:
            attendance_percentage = 0

        cursor.close()
        connection.close()

        return render_template(
            "student_dashboard.html",
            name=session["name"],
            total_tasks=total_tasks,
            completed_tasks=completed_tasks,
            pending_tasks=pending_tasks,
            attendance_percentage=attendance_percentage
        )

    # TEACHER DASHBOARD
    elif session["role"] == "teacher":

        # Total students
        cursor.execute("""
            SELECT COUNT(*) AS total_students
            FROM students
        """)

        total_students = cursor.fetchone()["total_students"]

        # Total tasks
        cursor.execute("""
            SELECT COUNT(*) AS total_tasks
            FROM tasks
        """)

        total_tasks = cursor.fetchone()["total_tasks"]

        # Total attendance records
        cursor.execute("""
            SELECT COUNT(*) AS total_attendance
            FROM attendance
        """)

        total_attendance = cursor.fetchone()["total_attendance"]

        cursor.close()
        connection.close()

        return render_template(
            "teacher_dashboard.html",
            name=session["name"],
            total_students=total_students,
            total_tasks=total_tasks,
            total_attendance=total_attendance
        )

    return redirect(url_for("login"))
@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("login"))
@app.route("/manage_students")
def manage_students():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session["role"] != "teacher":
        return redirect(url_for("dashboard"))

    connection = get_database_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute("""
        SELECT students.id,
               students.roll_number,
               users.name,
               users.email,
               students.course,
               students.year,
               students.section
        FROM students
        JOIN users ON students.user_id = users.id
    """)

    students = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        "manage_students.html",
        students=students
    )
@app.route("/add_student", methods=["GET", "POST"])
def add_student():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session["role"] != "teacher":
        return redirect(url_for("dashboard"))

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        roll_number = request.form["roll_number"]
        course = request.form["course"]
        year = request.form["year"]
        section = request.form["section"]

        connection = get_database_connection()
        cursor = connection.cursor(dictionary=True)

        from werkzeug.security import generate_password_hash

        # Check duplicate email
        cursor.execute(
            "SELECT id FROM users WHERE email = %s",
            (email,)
        )

        existing_email = cursor.fetchone()

        if existing_email:
            cursor.close()
            connection.close()

            flash("Email already exists. Please use a different email.")

            return redirect(url_for("add_student"))

        # Check duplicate roll number
        cursor.execute(
            "SELECT id FROM students WHERE roll_number = %s",
            (roll_number,)
        )

        existing_roll = cursor.fetchone()

        if existing_roll:
            cursor.close()
            connection.close()

            flash("Roll number already exists. Please use a different roll number.")

            return redirect(url_for("add_student"))
                    # Check whether roll number already exists
        cursor.execute(
            "SELECT id FROM students WHERE roll_number = %s",
            (roll_number,)
        )

        existing_roll = cursor.fetchone()

        if existing_roll:
            cursor.close()
            connection.close()

            flash("Roll number already exists. Please use a different roll number.")
            return redirect(url_for("add_student"))

        # Create encrypted password
        hashed_password = generate_password_hash(password)

        # Add student to users table
        cursor.execute("""
            INSERT INTO users
            (name, email, password, role)
            VALUES (%s, %s, %s, 'student')
        """, (
            name,
            email,
            hashed_password
        ))

        user_id = cursor.lastrowid

        # Add student details to students table
        cursor.execute("""
            INSERT INTO students
            (user_id, roll_number, course, year, section)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            user_id,
            roll_number,
            course,
            year,
            section
        ))

        connection.commit()

        cursor.close()
        connection.close()

        flash("Student added successfully!")

        return redirect(url_for("manage_students"))
       

    return render_template("add_student.html")

@app.route("/manage_tasks")
def manage_tasks():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session["role"] != "teacher":
        return redirect(url_for("dashboard"))

    connection = get_database_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute("""
        SELECT tasks.id,
               tasks.task_name,
               tasks.description,
               tasks.assigned_date,
               tasks.due_date,
               tasks.status,
               users.name AS student_name,
               students.roll_number
        FROM tasks
        JOIN students
            ON tasks.student_id = students.id
        JOIN users
            ON students.user_id = users.id
        ORDER BY tasks.due_date
    """)

    tasks = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        "manage_tasks.html",
        tasks=tasks
    )
@app.route("/add_task", methods=["GET", "POST"])
def add_task():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session["role"] != "teacher":
        return redirect(url_for("dashboard"))

    connection = get_database_connection()
    cursor = connection.cursor(dictionary=True)

    # Get all students
    cursor.execute("""
        SELECT students.id,
               students.roll_number,
               users.name
        FROM students
        JOIN users
            ON students.user_id = users.id
        ORDER BY users.name
    """)

    students = cursor.fetchall()

    if request.method == "POST":

        student_id = request.form["student_id"]
        task_name = request.form["task_name"]
        description = request.form["description"]
        assigned_date = request.form["assigned_date"]
        due_date = request.form["due_date"]
                # Check whether due date is before assigned date
        if due_date < assigned_date:
            cursor.close()
            connection.close()

            flash("Due date cannot be before the assigned date.")
            return redirect(url_for("add_task"))

        # Check dates
        if due_date < assigned_date:

            cursor.close()
            connection.close()

            flash("Due date cannot be earlier than the assigned date.")

            return redirect(url_for("add_task"))

        # Add task
        cursor.execute("""
            INSERT INTO tasks
            (student_id, task_name, description,
             assigned_date, due_date, status)
            VALUES (%s, %s, %s, %s, %s, 'Pending')
        """, (
            student_id,
            task_name,
            description,
            assigned_date,
            due_date
        ))

        connection.commit()

        cursor.close()
        connection.close()

        flash("Task assigned successfully!")

        return redirect(url_for("manage_tasks"))

    cursor.close()
    connection.close()

    return render_template(
        "add_task.html",
        students=students
    )
# ================================
# STUDENT - MY TASKS
# ================================

@app.route("/my_tasks")
def my_tasks():

    # Check whether the user is logged in
    if "user_id" not in session:
        return redirect(url_for("login"))

    # Only students can access My Tasks
    if session["role"] != "student":
        return redirect(url_for("dashboard"))

    # Connect to database
    connection = get_database_connection()
    cursor = connection.cursor(dictionary=True)

    # Get tasks belonging to the logged-in student
    cursor.execute("""
        SELECT tasks.id,
               tasks.task_name,
               tasks.description,
               tasks.assigned_date,
               tasks.due_date,
               tasks.status
        FROM tasks
        JOIN students
            ON tasks.student_id = students.id
        WHERE students.user_id = %s
        ORDER BY tasks.due_date
    """, (session["user_id"],))

    tasks = cursor.fetchall()

    # Close database connection
    cursor.close()
    connection.close()

    # Send tasks to HTML page
    return render_template(
        "my_tasks.html",
        tasks=tasks
    )


# ================================
# STUDENT - UPDATE TASK STATUS
# ================================

@app.route("/update_task_status/<int:task_id>", methods=["POST"])
def update_task_status(task_id):

    # Check whether the user is logged in
    if "user_id" not in session:
        return redirect(url_for("login"))

    # Only students can update task status
    if session["role"] != "student":
        return redirect(url_for("dashboard"))

    # Connect to database
    connection = get_database_connection()
    cursor = connection.cursor(dictionary=True)

    # Check whether this task belongs to the logged-in student
    cursor.execute("""
        SELECT tasks.id
        FROM tasks
        JOIN students
            ON tasks.student_id = students.id
        WHERE tasks.id = %s
        AND students.user_id = %s
    """, (task_id, session["user_id"]))

    task = cursor.fetchone()

    # If the task belongs to this student,
    # change its status to Completed
    if task:

        cursor.execute("""
            UPDATE tasks
            SET status = 'Completed'
            WHERE id = %s
        """, (task_id,))

        connection.commit()

    # Close database connection
    cursor.close()
    connection.close()

    # Return to My Tasks page
    return redirect(url_for("my_tasks"))

@app.route("/mark_attendance", methods=["GET", "POST"])
def mark_attendance():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session["role"] != "teacher":
        return redirect(url_for("dashboard"))

    connection = get_database_connection()
    cursor = connection.cursor(dictionary=True)

    # Get all students
    cursor.execute("""
        SELECT students.id,
               students.roll_number,
               users.name
        FROM students
        JOIN users
            ON students.user_id = users.id
        ORDER BY users.name
    """)

    students = cursor.fetchall()

    if request.method == "POST":

        student_id = request.form["student_id"]
        attendance_date = request.form["attendance_date"]
        status = request.form["status"]
                # Check for duplicate attendance
        cursor.execute("""
            SELECT id
            FROM attendance
            WHERE student_id = %s
            AND attendance_date = %s
        """, (student_id, attendance_date))

        existing_attendance = cursor.fetchone()

        if existing_attendance:

            cursor.close()
            connection.close()

            flash("Attendance has already been marked for this student on this date.")

            return redirect(url_for("mark_attendance"))

        cursor.execute("""
            INSERT INTO attendance
            (student_id, attendance_date, status)
            VALUES (%s, %s, %s)
        """, (
            student_id,
            attendance_date,
            status
        ))

        connection.commit()
        flash("Attendance marked successfully!")

        cursor.close()
        connection.close()

        return redirect(url_for("view_attendance"))

    cursor.close()
    connection.close()

    return render_template(
        "mark_attendance.html",
        students=students
    )
@app.route("/view_attendance")
def view_attendance():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session["role"] != "teacher":
        return redirect(url_for("dashboard"))

    connection = get_database_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute("""
        SELECT attendance.id,
               users.name AS student_name,
               students.roll_number,
               attendance.attendance_date,
               attendance.status
        FROM attendance
        JOIN students
            ON attendance.student_id = students.id
        JOIN users
            ON students.user_id = users.id
        ORDER BY attendance.attendance_date DESC
    """)

    attendance = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        "view_attendance.html",
        attendance=attendance
    )
@app.route("/my_attendance")
def my_attendance():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session["role"] != "student":
        return redirect(url_for("dashboard"))

    connection = get_database_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute("""
        SELECT attendance.attendance_date,
               attendance.status
        FROM attendance
        JOIN students
            ON attendance.student_id = students.id
        WHERE students.user_id = %s
        ORDER BY attendance.attendance_date DESC
    """, (session["user_id"],))

    attendance = cursor.fetchall()

    # Calculate attendance summary
    total_classes = len(attendance)

    present_count = 0
    absent_count = 0

    for record in attendance:

        if record["status"] == "Present":
            present_count += 1

        elif record["status"] == "Absent":
            absent_count += 1

    if total_classes > 0:
        attendance_percentage = (present_count / total_classes) * 100
    else:
        attendance_percentage = 0

    cursor.close()
    connection.close()

    return render_template(
        "my_attendance.html",
        attendance=attendance,
        total_classes=total_classes,
        present_count=present_count,
        absent_count=absent_count,
        attendance_percentage=attendance_percentage
    )
if __name__ == "__main__":
    app.run(debug=True)