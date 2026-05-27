# backend/tests/bdd/steps/test_appointment_booking.py
import pytest
from pytest_bdd import given, when, then, scenarios, parsers

scenarios('../features/appointment_booking.feature')

# ── Shared State ──────────────────────────────────────────────────────────────

@pytest.fixture
def booking_context():
    """Holds mutable test state shared across steps."""
    return {
        'provider': None,
        'slot': None,
        'appointments': {},  # patient_name -> appointment_id
        'last_response_status': None,
        'slot_status': 'Available',
        'insurance_required': False,
        'insurance_received': False,
        'current_time': None,
        'reschedule_cutoff_minutes': None,
        'waitlist': [],
    }

# ── Background Steps ──────────────────────────────────────────────────────────

@given(parsers.parse('the system has a registered provider "{name}" with specialty "{specialty}"'))
def provider_registered(booking_context, name, specialty):
    booking_context['provider'] = {'name': name, 'specialty': specialty, 'id': 'prov_001'}

@given(parsers.parse('the provider has an available slot on "{slot_date}" at "{slot_time}" for 30 minutes'))
def slot_available(booking_context, slot_date, slot_time):
    booking_context['slot'] = {
        'date': slot_date,
        'time': slot_time,
        'status': 'Available',
        'duration_minutes': 30,
    }
    booking_context['slot_status'] = 'Available'

# ── Scenario 1: Successful Booking ───────────────────────────────────────────

@given(parsers.parse('the patient "{patient_name}" has a registered account'))
def patient_registered(booking_context, patient_name):
    booking_context['current_patient'] = patient_name

@when('the patient selects the slot and submits the booking')
def patient_submits_booking(booking_context):
    if booking_context['slot_status'] == 'Available':
        booking_context['slot_status'] = 'Held'
        patient = booking_context['current_patient']
        status = 'Requested'
        if booking_context['insurance_required'] and not booking_context['insurance_received']:
            status = 'PendingApproval'
        booking_context['appointments'][patient] = {
            'status': status,
            'slot': booking_context['slot'],
        }
        booking_context['last_response_status'] = 201
    else:
        booking_context['last_response_status'] = 409

@then(parsers.parse('the appointment is saved with status "{expected_status}"'))
def appointment_has_status(booking_context, expected_status):
    patient = booking_context['current_patient']
    appt = booking_context['appointments'].get(patient)
    assert appt is not None, f"No appointment found for {patient}"
    assert appt['status'] == expected_status

@then(parsers.parse('the slot on "{slot_date}" at "{slot_time}" is marked as unavailable'))
def slot_is_unavailable(booking_context, slot_date, slot_time):
    assert booking_context['slot_status'] != 'Available'

@then('the patient receives a booking confirmation')
def patient_receives_confirmation(booking_context):
    assert booking_context['last_response_status'] == 201

# ── Scenario 2: Double Booking Prevention ────────────────────────────────────

@given(parsers.parse('the patient "{patient_name}" has already booked the slot'))
def first_patient_booked(booking_context, patient_name):
    booking_context['slot_status'] = 'Reserved'
    booking_context['appointments'][patient_name] = {
        'status': 'Confirmed',
        'slot': booking_context['slot'],
    }

@given(parsers.parse('a second patient "{patient_name}" has a registered account'))
def second_patient_registered(booking_context, patient_name):
    booking_context['current_patient'] = patient_name

@when(parsers.parse('"{patient_name}" attempts to book the same slot'))
def second_patient_attempts_booking(booking_context, patient_name):
    booking_context['current_patient'] = patient_name
    if booking_context['slot_status'] != 'Available':
        booking_context['last_response_status'] = 409
    else:
        booking_context['last_response_status'] = 201

@then(parsers.parse('the system rejects the request with status {status_code:d}'))
def request_rejected(booking_context, status_code):
    assert booking_context['last_response_status'] == status_code

@then(parsers.parse('no appointment is created for "{patient_name}"'))
def no_appointment_created(booking_context, patient_name):
    assert patient_name not in booking_context['appointments']

@then(parsers.parse('the slot remains reserved by "{patient_name}"'))
def slot_still_reserved(booking_context, patient_name):
    assert booking_context['appointments'][patient_name]['status'] == 'Confirmed'

# ── Scenario 3: Doctor Cancels ────────────────────────────────────────────────

@given(parsers.parse('the patient "{patient_name}" has a confirmed appointment on "{slot_date}" at "{slot_time}"'))
def patient_has_confirmed_appointment(booking_context, patient_name, slot_date, slot_time):
    booking_context['slot_status'] = 'Reserved'
    booking_context['appointments'][patient_name] = {
        'status': 'Confirmed',
        'slot': {'date': slot_date, 'time': slot_time},
    }
    booking_context['current_patient'] = patient_name

@when(parsers.parse('"{actor}" cancels the appointment with reason "{reason}"'))
def actor_cancels_appointment(booking_context, actor, reason):
    patient = booking_context['current_patient']
    booking_context['appointments'][patient]['status'] = 'Cancelled'
    booking_context['appointments'][patient]['cancel_reason'] = reason
    booking_context['slot_status'] = 'Available'

@then(parsers.parse('the appointment status is updated to "{expected_status}"'))
def appointment_status_updated(booking_context, expected_status):
    patient = booking_context['current_patient']
    assert booking_context['appointments'][patient]['status'] == expected_status

@then(parsers.parse('the slot on "{slot_date}" at "{slot_time}" is marked as available'))
def slot_is_available_again(booking_context, slot_date, slot_time):
    assert booking_context['slot_status'] == 'Available'


# —— Scenario 4/5: Insurance-dependent confirmation —————————————————————

@given('insurance authorization is required for the requested consultation')
def insurance_required(booking_context):
    booking_context['insurance_required'] = True


@given('insurance authorization has not been received')
def insurance_not_received(booking_context):
    booking_context['insurance_received'] = False


@given('insurance authorization has been received')
def insurance_received(booking_context):
    booking_context['insurance_received'] = True


@given(parsers.parse('the patient "{patient_name}" has a pending-approval appointment on "{slot_date}" at "{slot_time}"'))
def patient_has_pending_approval_appointment(booking_context, patient_name, slot_date, slot_time):
    booking_context['current_patient'] = patient_name
    booking_context['slot_status'] = 'Held'
    booking_context['appointments'][patient_name] = {
        'status': 'PendingApproval',
        'slot': {'date': slot_date, 'time': slot_time},
    }


@when('staff confirms the pending appointment')
def staff_confirms_pending_appointment(booking_context):
    patient = booking_context['current_patient']
    appt = booking_context['appointments'][patient]
    if appt['status'] == 'PendingApproval' and booking_context['insurance_received']:
        appt['status'] = 'Confirmed'
        booking_context['slot_status'] = 'Reserved'
        booking_context['last_response_status'] = 200
    else:
        booking_context['last_response_status'] = 422


# —— Scenario 6: Reschedule cutoff boundary —————————————————————————————

@given(parsers.parse('the patient "{patient_name}" has a confirmed appointment at "{appt_time}"'))
def patient_has_confirmed_at_time(booking_context, patient_name, appt_time):
    booking_context['current_patient'] = patient_name
    booking_context['appointments'][patient_name] = {
        'status': 'Confirmed',
        'slot': {'time': appt_time},
    }
    booking_context['slot_status'] = 'Reserved'


@given(parsers.parse('the current time is "{current_time}"'))
def current_time_set(booking_context, current_time):
    booking_context['current_time'] = current_time


@given(parsers.parse('clinic reschedule cutoff is {minutes:d} minutes before appointment'))
def reschedule_cutoff_set(booking_context, minutes):
    booking_context['reschedule_cutoff_minutes'] = minutes


def _hhmm_to_minutes(text):
    h, m = text.split(':')
    return int(h) * 60 + int(m)


@when(parsers.parse('"{patient_name}" requests reschedule to "{new_time}"'))
def patient_requests_reschedule(booking_context, patient_name, new_time):
    booking_context['current_patient'] = patient_name
    appt = booking_context['appointments'][patient_name]
    appt_minutes = _hhmm_to_minutes(appt['slot']['time'])
    now_minutes = _hhmm_to_minutes(booking_context['current_time'])
    remaining = appt_minutes - now_minutes
    cutoff = booking_context['reschedule_cutoff_minutes']

    if cutoff is not None and remaining < cutoff:
        booking_context['last_response_status'] = 422
    else:
        appt['slot']['time'] = new_time
        booking_context['last_response_status'] = 200


# —— Scenario 7: Waitlist reassignment ————————————————————————————————

@given(parsers.parse('the patient "{patient_name}" is on the waitlist for the provider slot'))
def patient_on_waitlist(booking_context, patient_name):
    booking_context['waitlist'].append(patient_name)


@given(parsers.parse('the slot on "{slot_date}" at "{slot_time}" is released by cancellation'))
def slot_released_by_cancellation(booking_context, slot_date, slot_time):
    booking_context['slot'] = {'date': slot_date, 'time': slot_time}
    booking_context['slot_status'] = 'Available'


@when('the system runs waitlist reassignment')
def run_waitlist_reassignment(booking_context):
    if booking_context['slot_status'] == 'Available' and booking_context['waitlist']:
        patient = booking_context['waitlist'].pop(0)
        booking_context['appointments'][patient] = {
            'status': 'Confirmed',
            'slot': booking_context['slot'],
        }
        booking_context['current_patient'] = patient
        booking_context['slot_status'] = 'Reserved'
        booking_context['last_response_status'] = 200
    else:
        booking_context['last_response_status'] = 404
