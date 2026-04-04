"""Retrieve doctor availability rules, working hours, and slot duration from storage.

This module fulfills the task: "retrieving availability rules from the database".
Until the scheduling schema exists in Supabase, we use stub data so the rest of
the flow (calculate intervals → prepare slots for calendar) can be tested.

When the DB is ready, replace the stub with queries to:
- availability_rules (working days, working hours, blocked times, closed days)
- appointment duration rules (e.g. per clinic or per doctor)
"""

from datetime import date, time

from ..services.scheduling import DailyAvailability, TimeRange


def get_availability_for_doctor_date(doctor_id: str, target_date: date) -> DailyAvailability:
    """Load availability rules for a doctor on a given date and return a normalized view.

    Returns working hours, blocked periods, and slot duration so that
    generate_available_slots() can compute the list of bookable times.

    TODO: Replace stub with real DB access once availability_rules (and related)
    tables exist in Supabase. Expected inputs from DB:
    - working_days (e.g. weekday 0–6)
    - working_hours (start_time, end_time)
    - blocked_periods or breaks (start_time, end_time)
    - appointment_duration_minutes (from clinic or doctor config)
    - max_appointments_per_slot (clinic / doctor capacity rule)
    """
    # Stub: assume Mon–Sat 09:00–17:00, 30-min slots, lunch 12:00–13:00.
    # Sunday (weekday 6) has no working hours — used for "no slots" scenarios.
    # In production, filter by doctor_id and target_date (and apply closed days).
    _ = doctor_id  # use when querying by doctor

    # Example: allow up to 2 concurrent appointments per slot (e.g. double-booking cap).
    max_appointments_per_slot = 2

    if target_date.weekday() == 6:
        # No working hours (e.g. closed on Sunday).
        working_hours = TimeRange(start=time(9, 0), end=time(9, 0))
        blocked_periods = []
        slot_minutes = 30
    else:
        working_hours = TimeRange(start=time(9, 0), end=time(17, 0))
        blocked_periods = [TimeRange(start=time(12, 0), end=time(13, 0))]
        slot_minutes = 30

    return DailyAvailability(
        date=target_date,
        working_hours=working_hours,
        blocked_periods=blocked_periods,
        slot_minutes=slot_minutes,
        max_appointments_per_slot=max_appointments_per_slot,
    )
