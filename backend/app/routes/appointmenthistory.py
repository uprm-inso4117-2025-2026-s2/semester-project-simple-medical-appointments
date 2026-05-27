from flask import Blueprint, jsonify, current_app
import traceback

appointment_bp = Blueprint('appointments', __name__)


def _fetch_appointments(filters=None):
    sb = current_app.supabase

    # Fetch appointments
    query = sb.table('appointments').select('id,patient_id,doctor_id,clinic_id,appointment_datetime,status')
    if filters:
        for col, val in filters.items():
            query = query.eq(col, val)
    appointments = query.order('appointment_datetime', desc=False).execute().data or []

    if not appointments:
        return []

    # Collect unique doctor/clinic IDs
    doctor_ids = list({a['doctor_id'] for a in appointments if a.get('doctor_id')})
    clinic_ids = list({a['clinic_id'] for a in appointments if a.get('clinic_id')})

    # Lookup doctor names
    doctors_map = {}
    if doctor_ids:
        rows = sb.table('doctors').select('id,full_name').in_('id', doctor_ids).execute().data or []
        doctors_map = {r['id']: r['full_name'] for r in rows}

    # Looks up clinic names
    clinics_map = {}
    if clinic_ids:
        rows = sb.table('clinics').select('id,name').in_('id', clinic_ids).execute().data or []
        clinics_map = {r['id']: r['name'] for r in rows}

    # Builds enriched response
    return [
        {
            'id':                   a['id'],
            'patient_id':           a.get('patient_id'),
            'doctor_id':            a.get('doctor_id'),
            'doctor_name':          doctors_map.get(a.get('doctor_id'), 'Unknown'),
            'clinic_name':          clinics_map.get(a.get('clinic_id'), 'Unknown'),
            'status':               a.get('status'),
            'appointment_datetime': a.get('appointment_datetime'),
        }
        for a in appointments
    ]


@appointment_bp.route('/appointment-history', methods=['GET'])
def get_all_appointment_history():
    try:
        return jsonify(_fetch_appointments())
    except Exception as e:
        return jsonify({'error': str(e), 'trace': traceback.format_exc()}), 500


@appointment_bp.route('/appointment-history/<patient_id>', methods=['GET'])
def get_appointment_history(patient_id):
    try:
        return jsonify(_fetch_appointments({'patient_id': patient_id}))
    except Exception as e:
        return jsonify({'error': str(e), 'trace': traceback.format_exc()}), 500


@appointment_bp.route('/appointment-history/debug', methods=['GET'])
def debug_appointment_history():
    try:
        sb = current_app.supabase
        appt = sb.table('appointments').select('*').limit(1).execute().data or []
        result = {'appointment': appt}
        if appt:
            doctor_id = appt[0].get('doctor_id')
            clinic_id = appt[0].get('clinic_id')
            if doctor_id:
                result['doctor_lookup'] = sb.table('doctors').select('id,full_name').eq('id', doctor_id).execute().data
            if clinic_id:
                result['clinic_lookup'] = sb.table('clinics').select('id,name').eq('id', clinic_id).execute().data
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e), 'trace': traceback.format_exc()}), 500