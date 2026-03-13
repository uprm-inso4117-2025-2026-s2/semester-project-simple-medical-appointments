from flask import jsonify
from app.config import get_db_connection
from .main import main_bp
@main_bp.route('/appointment-history/<int:user_id>', methods=['GET'])
def get_appointment_history(user_id):
    conn= get_db_connection()
    appointments = conn.execute(
        '''
        SELECT appointment_date, appointment_time, clinic_id, doctor_id, status
        FROM appointments
        WHERE user_id = ?
        ORDER BY appointment_date ASC, appointment_time ASC
        ''',
        (user_id,)
    ).fetchall()
    conn.close()
    results = []
    for appt in appointments:
        results.append({
            'appointment_date': appt['appointment_date'],
            'appointment_time': appt['appointment_time'],
            'clinic_id': appt['clinic_id'],
            'doctor_id': appt['doctor_id'],
            'status': appt['status']
        })
    return jsonify(results)

