from flask import jsonify, g
from app.config import get_db_connection
from app.middleware.auth_middleware import requires_auth
from .main import main_bp


@main_bp.route('/appointment-history/<int:user_id>', methods=['GET'])
@requires_auth
def get_appointment_history(user_id):
    # Users can only access their own history; admins are handled at the
    # admin endpoints layer.
    if g.user_id != str(user_id):
        return jsonify({'error': 'Forbidden: you can only view your own appointment history.'}), 403

    conn = get_db_connection()
    appointments = conn.execute(
        '''
        SELECT id, user_id, appointment_date, appointment_time, clinic_id, doctor_id, status
        FROM appointments
        WHERE user_id = ?
        ORDER BY appointment_date ASC, appointment_time ASC
        ''',
        (user_id,)
    ).fetchall()
    conn.close()

    # Converts sqlite row objects into plain dictionaries.
    results = []
    for appt in appointments:
        results.append({
            'id': appt['id'],
            'user_id': appt['user_id'],
            'appointment_date': appt['appointment_date'],
            'appointment_time': appt['appointment_time'],
            'clinic_id': appt['clinic_id'],
            'doctor_id': appt['doctor_id'],
            'status': appt['status'],
        })

    return jsonify(results)

