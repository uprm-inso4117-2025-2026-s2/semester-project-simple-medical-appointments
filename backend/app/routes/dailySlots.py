from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
from supabase import create_client
import os

slots_bp = Blueprint('slots', __name__, url_prefix='/api/slots')

# Initialize Supabase
supabase = create_client(
    os.getenv("VITE_SUPABASE_URL"),
    os.getenv("VITE_SUPABASE_ANON_KEY")
)

def generate_slots(start_time, end_time, duration):
    slots = []

    current = start_time
    while current < end_time:
        slots.append(current.strftime("%H:%M"))
        current += timedelta(minutes=duration)

    return slots

# Endpoint 
@slots_bp.route('/', methods=['GET'])
def get_slots():
    doctor_id = request.args.get('doctor_id')
    date_str = request.args.get('date')

    if not doctor_id or not date_str:
        return jsonify({"error": "doctor_id and date required"}), 400

    date = datetime.strptime(date_str, "%Y-%m-%d")
    day_of_week = date.weekday()  # Monday = 0

    # get doctor schedule
    schedule_res = supabase.table("doctor_schedule_rule") \
        .select("*") \
        .eq("doctor_id", doctor_id) \
        .eq("day_of_week", day_of_week) \
        .execute()

    if not schedule_res.data:
        return jsonify([])

    schedule = schedule_res.data[0]

    start_time = datetime.strptime(schedule["start_time"], "%H:%M:%S")
    end_time = datetime.strptime(schedule["end_time"], "%H:%M:%S")

    # get slot duration
    doctor_res = supabase.table("doctor") \
        .select("slot_duration_minutes") \
        .eq("id", doctor_id) \
        .execute()

    duration = doctor_res.data[0]["slot_duration_minutes"]

    slots = generate_slots(start_time, end_time, duration)

    return jsonify(slots)