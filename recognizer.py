import cv2
import numpy as np
from keras.models import load_model
from datetime import datetime
import os
import sqlite3


face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')


model = load_model('models/antispoof_model.h5')


def mark_attendance(student_id):
    conn = sqlite3.connect('database/attendance.db')
    cursor = conn.cursor()
    now = datetime.now()
    timestamp = now.strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute('INSERT INTO attendance (user_id, timestamp, status) VALUES (?, ?, ?)', (student_id, timestamp, "Present"))
    conn.commit()
    conn.close()


def verify_face(face_roi):
    try:
        face = cv2.resize(face_roi, (96, 96))
        face = face.astype("float32") / 255.0
        face = np.expand_dims(face, axis=(0, -1))  # (1, 96, 96, 1)
        face_sequence = np.repeat(face[np.newaxis, ...], 10, axis=1)  # (1, 10, 96, 96, 1)

        pred = model.predict(face_sequence)
        class_idx = np.argmax(pred, axis=1)[0]
        return class_idx == 1  # 1 = real
    except Exception as e:
        print("Verification error:", e)
        return False


def recognize_face(face_roi):
    return "student001"


def start_recognition():
    cap = cv2.VideoCapture(0)

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)

        for (x, y, w, h) in faces:
            face_roi = gray[y:y+h, x:x+w]

            if verify_face(face_roi):
                student_id = recognize_face(face_roi)
                mark_attendance(student_id)
                cv2.putText(frame, f"Real Face - {student_id}", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            else:
                cv2.putText(frame, "Spoof Detected", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

            cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)

        cv2.imshow('Face Recognition', frame)
        if cv2.waitKey(1) == 27:
            break

    cap.release()
    cv2.destroyAllWindows()



def fetch_all_students():
    conn = sqlite3.connect('database/attendance.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT id, username AS name, email, username AS roll FROM users")
    students = cursor.fetchall()
    conn.close()
    return [dict(row) for row in students]

def get_attendance_by_user(user_id):
    conn = sqlite3.connect('database/attendance.db')
    cursor = conn.cursor()
    cursor.execute("SELECT timestamp, status FROM attendance WHERE user_id = ? ORDER BY timestamp DESC", (user_id,))
    records = cursor.fetchall()
    conn.close()
    return records



if __name__ == "__main__":
    start_recognition()
