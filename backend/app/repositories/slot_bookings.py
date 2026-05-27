"""Helpers to list and book appointment slots with capacity rules.

Doctor/admin slot booking logic.

Per-slot booking logic to list/reserve slots following this order:

MAIN at requested slot
→ WAITLIST at next available slot on the same day, if accepted
→ OVERRIDE at requested slot, if explicitly allowed
→ REJECT
"""

from __future__ import annotations

from datetime import date, datetime, time, timedelta
from typing import Literal

from .availability import get_availability_for_doctor_date, _supabase_request
from ..services.scheduling import generate_available_slots

BookingType = Literal["MAIN", "WAITLIST", "OVERRIDE"]

ACTIVE_STATUSES = ("pending", "confirmed")

DEFAULT_WAITLIST_CAPACITY_PER_DAY = 3


def _normalize_dt(value: datetime) -> str:
    """Format datetime consistently for Supabase comparisons/inserts."""
    return value.isoformat()


def _validate_requested_slot(
    doctor_id: str,
    day: date,
    start_time: time,
) -> tuple[datetime | None, dict | None, int | None]:
    availability = get_availability_for_doctor_date(doctor_id, day)
    requested_slot = datetime.combine(day, start_time)

    allowed_slots = set(generate_available_slots(availability))

    if requested_slot not in allowed_slots:
        return (
            None,
            {"error": "Requested time is not an available generated slot for this doctor/date."},
            400,
        )

    return requested_slot, None, None


def _get_doctor_clinic_id(doctor_id: str) -> str | None:
    status, data, err = _supabase_request(
        "GET",
        "/rest/v1/doctors",
        query={
            "id": f"eq.{doctor_id}",
            "select": "clinic_id",
            "limit": "1",
        },
    )

    if err or status != 200 or not data:
        return None

    return data[0].get("clinic_id")


def _get_main_capacity(doctor_id: str, day: date) -> int:
    availability = get_availability_for_doctor_date(doctor_id, day)
    return availability.max_appointments_per_slot


def _count_appointments_by_type(
    doctor_id: str,
    appointment_datetime: datetime,
) -> dict[str, int]:
    status, data, err = _supabase_request(
        "GET",
        "/rest/v1/appointments",
        query={
            "doctor_id": f"eq.{doctor_id}",
            "appointment_datetime": f"eq.{_normalize_dt(appointment_datetime)}",
            "status": f"in.({','.join(ACTIVE_STATUSES)})",
            "select": "appointment_type",
        },
    )

    counts = {
        "MAIN": 0,
        "WAITLIST": 0,
        "OVERRIDE": 0,
    }

    if err or status != 200:
        return counts

    for row in data or []:
        appointment_type = (row.get("appointment_type") or "MAIN").upper()
        if appointment_type in counts:
            counts[appointment_type] += 1

    return counts


def _regular_slot_usage(counts: dict[str, int]) -> int:
    """Appointments that consume normal slot capacity."""
    return counts["MAIN"] + counts["WAITLIST"]


def _slot_has_regular_capacity(
    doctor_id: str,
    slot_start: datetime,
    main_capacity: int,
) -> bool:
    counts = _count_appointments_by_type(doctor_id, slot_start)
    return _regular_slot_usage(counts) < main_capacity


def _count_waitlist_for_day(doctor_id: str, day: date) -> int:
    day_start = datetime.combine(day, time.min)
    day_end = day_start + timedelta(days=1)

    status, data, err = _supabase_request(
        "GET",
        "/rest/v1/appointments",
        query={
            "doctor_id": f"eq.{doctor_id}",
            "appointment_type": "eq.WAITLIST",
            "status": f"in.({','.join(ACTIVE_STATUSES)})",
            "select": "id,appointment_datetime",
        },
    )

    if err or status != 200:
        return 0

    count = 0
    for row in data or []:
        raw_dt = row.get("appointment_datetime")
        if not raw_dt:
            continue

        try:
            appt_dt = datetime.fromisoformat(raw_dt.replace("Z", "+00:00")).replace(tzinfo=None)
        except ValueError:
            continue

        if day_start <= appt_dt < day_end:
            count += 1

    return count


def _find_next_available_slot_same_day(
    doctor_id: str,
    day: date,
    requested_slot: datetime,
) -> datetime | None:
    availability = get_availability_for_doctor_date(doctor_id, day)
    generated_slots = generate_available_slots(availability)
    main_capacity = availability.max_appointments_per_slot

    for slot_start in generated_slots:
        if slot_start <= requested_slot:
            continue

        if _slot_has_regular_capacity(doctor_id, slot_start, main_capacity):
            return slot_start

    return None


def _insert_appointment(
    *,
    patient_id: str,
    doctor_id: str,
    clinic_id: str,
    appointment_datetime: datetime,
    appointment_type: BookingType,
    notes: str | None = None,
) -> tuple[dict | None, tuple[dict, int] | None]:
    payload = {
        "patient_id": patient_id,
        "doctor_id": doctor_id,
        "clinic_id": clinic_id,
        "appointment_datetime": _normalize_dt(appointment_datetime),
        "status": "confirmed",
        "appointment_type": appointment_type,
        "notes": notes,
    }

    status, data, err = _supabase_request(
        "POST",
        "/rest/v1/appointments",
        query={"select": "*"},
        json_body=payload,
    )

    if err:
        return None, ({"error": "Failed to create appointment", "details": err}, 500)

    if status not in (200, 201) or not data:
        return None, (
            {
                "error": "Failed to create appointment",
                "details": data,
            },
            500,
        )

    return data[0], None


def book_admin_appointment(
    *,
    patient_id: str,
    doctor_id: str,
    appointment_date: date,
    appointment_time: time,
    notes: str | None = None,
    accept_waitlist: bool = False,
    allow_override: bool = False,
) -> tuple[dict | None, tuple[dict, int] | None]:
    """Book appointment for doctor/admin workflow.

    Flow:
    1. Book MAIN at requested slot if normal capacity exists.
    2. If requested slot is full and accept_waitlist is true, assign next available
       slot on the same day as WAITLIST, subject to a daily waitlist limit.
    3. If no waitlist placement is possible and allow_override is true, book
       OVERRIDE at the requested slot.
    4. Otherwise reject.
    """
    requested_slot, error_body, error_status = _validate_requested_slot(
        doctor_id,
        appointment_date,
        appointment_time,
    )

    if error_body is not None:
        return None, (error_body, error_status or 400)

    clinic_id = _get_doctor_clinic_id(doctor_id)
    if not clinic_id:
        return None, (
            {"error": "Could not determine clinic for selected doctor."},
            400,
        )

    main_capacity = _get_main_capacity(doctor_id, appointment_date)
    requested_counts = _count_appointments_by_type(doctor_id, requested_slot)

    # 1. MAIN booking at requested slot.
    if _regular_slot_usage(requested_counts) < main_capacity:
        appointment, insert_error = _insert_appointment(
            patient_id=patient_id,
            doctor_id=doctor_id,
            clinic_id=clinic_id,
            appointment_datetime=requested_slot,
            appointment_type="MAIN",
            notes=notes,
        )

        if insert_error is not None:
            return None, insert_error

        return (
            {
                "appointment": appointment,
                "booking_type": "MAIN",
                "assigned_datetime": _normalize_dt(requested_slot),
                "requested_datetime": _normalize_dt(requested_slot),
                "message": "Appointment booked in requested slot.",
            },
            None,
        )

    # 2. WAITLIST booking into next available slot that same day.
    if accept_waitlist:
        daily_waitlist_count = _count_waitlist_for_day(doctor_id, appointment_date)

        if daily_waitlist_count >= DEFAULT_WAITLIST_CAPACITY_PER_DAY:
            waitlist_error = {
                "error": "Daily waitlist capacity has been reached.",
                "waitlist_capacity_per_day": DEFAULT_WAITLIST_CAPACITY_PER_DAY,
            }
        else:
            next_slot = _find_next_available_slot_same_day(
                doctor_id,
                appointment_date,
                requested_slot,
            )

            if next_slot is not None:
                waitlist_notes = notes or ""
                waitlist_notes = (
                    f"{waitlist_notes}\nPreferred time was "
                    f"{requested_slot.strftime('%H:%M')}; assigned to next available slot."
                ).strip()

                appointment, insert_error = _insert_appointment(
                    patient_id=patient_id,
                    doctor_id=doctor_id,
                    clinic_id=clinic_id,
                    appointment_datetime=next_slot,
                    appointment_type="WAITLIST",
                    notes=waitlist_notes,
                )

                if insert_error is not None:
                    return None, insert_error

                return (
                    {
                        "appointment": appointment,
                        "booking_type": "WAITLIST",
                        "assigned_datetime": _normalize_dt(next_slot),
                        "requested_datetime": _normalize_dt(requested_slot),
                        "message": "Requested slot was full. Patient was assigned to the next available slot on the same day.",
                    },
                    None,
                )

            waitlist_error = {
                "error": "No next available slot found for waitlist placement on this day."
            }
    else:
        waitlist_error = {
            "error": "Requested slot is full and waitlist placement was not accepted."
        }

    # 3. OVERRIDE booking at requested slot, only if explicitly allowed.
    if allow_override:
        override_notes = notes or ""
        override_notes = (
            f"{override_notes}\nOverride approved for full requested slot."
        ).strip()

        appointment, insert_error = _insert_appointment(
            patient_id=patient_id,
            doctor_id=doctor_id,
            clinic_id=clinic_id,
            appointment_datetime=requested_slot,
            appointment_type="OVERRIDE",
            notes=override_notes,
        )

        if insert_error is not None:
            return None, insert_error

        return (
            {
                "appointment": appointment,
                "booking_type": "OVERRIDE",
                "assigned_datetime": _normalize_dt(requested_slot),
                "requested_datetime": _normalize_dt(requested_slot),
                "message": "Requested slot was full. Appointment was booked through admin override.",
            },
            None,
        )

    # 4. REJECT.
    return None, (
        {
            "error": "Unable to book appointment.",
            "details": waitlist_error,
            "requested_slot_counts": requested_counts,
            "main_capacity": main_capacity,
        },
        409,
    )


def try_reserve_slot(
    doctor_id: str,
    day: date,
    start_time: time,
) -> tuple[dict, int] | None:
    """Compatibility wrapper for the older /submit route.

    This only validates requested slot availability for MAIN booking.
    New doctor/admin booking should use book_admin_appointment().
    """
    requested_slot, error_body, error_status = _validate_requested_slot(
        doctor_id,
        day,
        start_time,
    )

    if error_body is not None:
        return error_body, error_status or 400

    main_capacity = _get_main_capacity(doctor_id, day)
    counts = _count_appointments_by_type(doctor_id, requested_slot)

    if _regular_slot_usage(counts) >= main_capacity:
        return (
            {
                "error": "This time slot is full",
                "max_appointments_per_slot": main_capacity,
            },
            409,
        )

    return None


def slot_time_strings_for_doctor_day(doctor_id: str, day: date) -> list[str]:
    """Return HH:MM strings for generated slots that still have regular capacity."""
    availability = get_availability_for_doctor_date(doctor_id, day)
    main_capacity = availability.max_appointments_per_slot

    available_times = []

    for slot_start in generate_available_slots(availability):
        counts = _count_appointments_by_type(doctor_id, slot_start)

        if _regular_slot_usage(counts) < main_capacity:
            available_times.append(slot_start.strftime("%H:%M"))

    return available_times


def reset_booking_counts() -> None:
    """
    Compatibility helper for tests.

    Booking counts are no longer stored in memory; they are calculated from
    appointment records. Test data should be reset through test fixtures.
    """
    return None