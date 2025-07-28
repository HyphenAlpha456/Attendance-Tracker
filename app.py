from flask import Flask, render_template, request, redirect, url_for, session, flash
import os
import sqlite3
from datetime import datetime
from werkzeug.utils import secure_filename
from recognizer import verify_face, fetch_all_students, get_attendance_by_user
from utils import init_db, register_user, authenticate_user, log_attendance, fetch_attendance


app = Flask(__name__)
app.secret_key = 'your_super_secret_key'


UPLOAD_FOLDER = os.path.join('static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


init_db()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS



@app.route('/')
def home():
    return render_template('home.html')

@app.route('/admin')
def admin():
    return redirect(url_for('dashboard'))

@app.route('/student')
def student_portal():
    return render_template('student_home.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        student_id = request.form.get('student_id')
        name = request.form.get('name')
        image = request.files.get('face_image')

        if not student_id or not name or not image:
            flash('All fields are required', 'danger')
            return redirect(url_for('register'))

        if image.filename == '':
            flash('No selected file', 'danger')
            return redirect(url_for('register'))

        if not allowed_file(image.filename):
            flash('Only JPG, JPEG, and PNG images are allowed', 'danger')
            return redirect(url_for('register'))

        try:
            conn = sqlite3.connect('database/attendance.db')
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE username = ?", (student_id,))
            existing = cursor.fetchone()
            conn.close()
        except Exception as e:
            flash(f"Database error: {str(e)}", 'danger')
            return redirect(url_for('register'))

        if existing:
            flash('You are already registered!', 'warning')
            return redirect(url_for('student_portal'))

        filename = secure_filename(student_id + '.jpg')
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        try:
            image.save(filepath)
        except Exception as e:
            flash(f"File upload failed: {str(e)}", 'danger')
            return redirect(url_for('register'))

        try:
            register_user(student_id, name, filepath)
        except Exception as e:
            flash(f"Registration failed: {str(e)}", 'danger')
            return redirect(url_for('register'))

        flash('Student registered successfully!', 'success')
        return redirect(url_for('student_portal'))

    return render_template('register.html')

@app.route('/give_attendance', methods=['GET', 'POST'])
def give_attendance():
    if request.method == 'POST':
        student_id = request.form.get('roll')
        name = request.form.get('name')

        if not student_id or not name:
            return render_template('attendance.html', error='Roll number and name are required.')

        filepath = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(student_id + '.jpg'))

        if not os.path.exists(filepath):
            return render_template('attendance.html', error='No registration found for this roll number.')

        try:
            if verify_face(filepath, student_id):
                log_attendance(student_id)
                return render_template('attendance.html', success='Attendance marked successfully!')
            else:
                return render_template('attendance.html', error='Face verification failed! Face not matched or spoof detected.')
        except Exception as e:
            return render_template('attendance.html', error=f"Verification failed: {str(e)}")

    return render_template('attendance.html')

@app.route('/dashboard', methods=['GET'])
def dashboard():
    try:
        students = fetch_all_students()
        attendance_data = []
        total_present = 0

        for student in students:
            user_id = student["id"]
            name = student["name"]
            email = student["email"]
            roll = student["roll"]

            attendance_records = get_attendance_by_user(user_id)
            total_days = len(attendance_records)
            present_days = sum(1 for record in attendance_records if record[1] == "Present")
            attendance_percent = round((present_days / total_days) * 100, 2) if total_days > 0 else 0

            attendance_data.append({
                "name": name,
                "email": email,
                "roll": roll,
                "total_days": total_days,
                "present_days": present_days,
                "attendance_percent": attendance_percent
            })

            today_str = datetime.now().strftime("%Y-%m-%d")
            if today_str in [r[0][:10] for r in attendance_records]:
                total_present += 1

        avg_attendance = round(sum(s["attendance_percent"] for s in attendance_data) / len(attendance_data), 2) if attendance_data else 0

        return render_template("dashboard.html",
                               records=attendance_data,
                               total_students=len(attendance_data),
                               today_attendance=total_present,
                               average_attendance=avg_attendance)
    except Exception as e:
        flash(f"Dashboard loading error: {str(e)}", 'danger')
        return redirect(url_for('home'))



if __name__ == '__main__':
    app.run(debug=True)

