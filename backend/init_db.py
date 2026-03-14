import os
import sqlite3

db_path = os.path.join(os.path.dirname(__file__), "database.db")
print("Creating database at:", db_path)

if os.path.exists(db_path):
    os.remove(db_path)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()
# Create the appointments table
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
# Insert sample data for testing
cursor.execute("""
INSERT INTO appointments (user_id, appointment_date, appointment_time, clinic_id, doctor_id, status)
VALUES (1, '2026-03-15', '09:00', 2, 5, 'completed')
""")

cursor.execute("""
INSERT INTO appointments (user_id, appointment_date, appointment_time, clinic_id, doctor_id, status)
VALUES (1, '2026-03-20', '10:00', 2, 5, 'scheduled')
""")

cursor.execute("""
INSERT INTO appointments (user_id, appointment_date, appointment_time, clinic_id, doctor_id, status)
VALUES (1, '2026-03-22', '14:00', 3, 7, 'scheduled')
""")

cursor.execute("""
INSERT INTO appointments (user_id, appointment_date, appointment_time, clinic_id, doctor_id, status)
VALUES (1, '2026-03-25', '13:00', 2, 6, 'scheduled')
""")

cursor.execute("""
INSERT INTO appointments (user_id, appointment_date, appointment_time, clinic_id, doctor_id, status)
VALUES (1, '2026-03-28', '15:30', 1, 4, 'cancelled')
""")

cursor.execute("""
INSERT INTO appointments (user_id, appointment_date, appointment_time, clinic_id, doctor_id, status)
VALUES (1, '2026-03-15', '09:00', 2, 5, 'completed')
""")
cursor.execute("""
INSERT INTO appointments (user_id, appointment_date, appointment_time, clinic_id, doctor_id, status)
VALUES (1, '2026-03-20', '10:00', 2, 5, 'scheduled')
""")
cursor.execute("""
INSERT INTO appointments (user_id, appointment_date, appointment_time, clinic_id, doctor_id, status)
VALUES (2, '2026-03-21', '11:00', 1, 3, 'scheduled')
""")
cursor.execute("""
INSERT INTO appointments (user_id, appointment_date, appointment_time, clinic_id, doctor_id, status)
VALUES (2, '2026-03-18', '16:00', 1, 4, 'cancelled')
""")
cursor.execute("""
INSERT INTO appointments (user_id, appointment_date, appointment_time, clinic_id, doctor_id, status)
VALUES (3, '2026-03-22', '14:00', 3, 7, 'scheduled')
""")
cursor.execute("""
INSERT INTO appointments (user_id, appointment_date, appointment_time, clinic_id, doctor_id, status)
VALUES (3, '2026-03-25', '13:00', 2, 6, 'scheduled')
""")
conn.commit()
conn.close()

print("Done.")