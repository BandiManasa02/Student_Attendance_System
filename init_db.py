import mysql.connector
from werkzeug.security import generate_password_hash
MYSQL_PASSWORD = "Manasa_0207"
connection = mysql.connector.connect(
    host="localhost",
    user="root",
    password=MYSQL_PASSWORD
)
cursor = connection.cursor()
cursor.execute("CREATE DATABASE IF NOT EXISTS student_system")
cursor.execute("USE student_system")
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL
)
""")
student_password = generate_password_hash("student123")
cursor.execute("""
INSERT IGNORE INTO users (name, email, password, role)
VALUES (%s, %s, %s, %s)
""", (
    "Sample Student",
    "student@gmail.com",
    student_password,
    "student"
))
teacher_password = generate_password_hash("teacher123")
cursor.execute("""
INSERT IGNORE INTO users (name, email, password, role)
VALUES (%s, %s, %s, %s)
""", (
    "Sample Teacher",
    "teacher@gmail.com",
    teacher_password,
    "teacher"
))
connection.commit()
print("Database created successfully!")
print("Users table created successfully!")
print("Test user created successfully!")
cursor.execute("""
CREATE TABLE IF NOT EXISTS students (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    roll_number VARCHAR(50) UNIQUE NOT NULL,
    course VARCHAR(100),
    year INT,
    section VARCHAR(20),
    FOREIGN KEY (user_id) REFERENCES users(id)
)
""")
print("Students table created successfully!")
print("Students table created successfully!")

cursor.execute("""
CREATE TABLE IF NOT EXISTS tasks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT,
    task_name VARCHAR(200) NOT NULL,
    description TEXT,
    assigned_date DATE,
    due_date DATE,
    status VARCHAR(30) DEFAULT 'Pending',
    FOREIGN KEY (student_id) REFERENCES students(id)
)
""")
print("Tasks table created successfully!")
cursor.execute("""
CREATE TABLE IF NOT EXISTS attendance (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    attendance_date DATE NOT NULL,
    status VARCHAR(20) NOT NULL,
    FOREIGN KEY (student_id) REFERENCES students(id)
)
""")

print("Attendance table created successfully!")
cursor.close()
connection.close()