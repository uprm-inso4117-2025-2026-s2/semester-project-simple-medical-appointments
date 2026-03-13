import os
import sqlite3

db_path = os.path.join(os.path.dirname(__file__), "database.db")
print("Creating database at:", db_path)

if os.path.exists(db_path):
    os.remove(db_path)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE appointments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    appointment_date TEXT NOT NULL,
    appointment_time TEXT NOT NULL,
    clinic_id INTEGER,
    doctor_id INTEGER,
    status TEXT
)
""")

cursor.execute("""
INSERT INTO appointments (user_id, appointment_date, appointment_time, clinic_id, doctor_id, status)
VALUES (1, '2026-03-20', '10:00', 2, 5, 'scheduled')
""")

conn.commit()
conn.close()

print("Done.")