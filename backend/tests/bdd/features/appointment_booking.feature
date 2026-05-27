# backend/tests/bdd/features/appointment_booking.feature

Feature: Appointment Booking
  As a patient
  I want to book, cancel, and be protected from double-booking
  So that I can manage my medical appointments reliably

  Background:
    Given the system has a registered provider "Dr. Schutz" with specialty "cardiology"
    And the provider has an available slot on "2026-04-10" at "10:00" for 30 minutes

  Scenario: Patient successfully books an available appointment
    Given the patient "Ivan Morales" has a registered account
    When the patient selects the slot and submits the booking
    Then the appointment is saved with status "Requested"
    And the slot on "2026-04-10" at "10:00" is marked as unavailable
    And the patient receives a booking confirmation

  Scenario: Patient attempts to book an already-taken slot
    Given the patient "Ivan Morales" has already booked the slot
    And a second patient "Maximus Aurelius" has a registered account
    When "Maximus Aurelius" attempts to book the same slot
    Then the system rejects the request with status 409
    And no appointment is created for "Maximus Aurelius"
    And the slot remains reserved by "Ivan Morales"

  Scenario: Doctor cancels a scheduled appointment
    Given the patient "Ivan Morales" has a confirmed appointment on "2026-04-10" at "10:00"
    When "Dr. Schutz" cancels the appointment with reason "Doctor unavailable"
    Then the appointment status is updated to "Cancelled"
    And the slot on "2026-04-10" at "10:00" is marked as available

  Scenario: Booking requiring insurance stays pending
    Given the patient "Ivan Morales" has a registered account
    And insurance authorization is required for the requested consultation
    And insurance authorization has not been received
    When the patient selects the slot and submits the booking
    Then the appointment is saved with status "PendingApproval"
    And the slot on "2026-04-10" at "10:00" is marked as unavailable

  Scenario: Pending appointment is confirmed after insurance authorization
    Given the patient "Ivan Morales" has a pending-approval appointment on "2026-04-10" at "10:00"
    And insurance authorization has been received
    When staff confirms the pending appointment
    Then the appointment status is updated to "Confirmed"
    And the slot remains reserved for "Ivan Morales"

  Scenario: Patient cannot reschedule below clinic cutoff
    Given the patient "Ivan Morales" has a confirmed appointment at "14:00"
    And the current time is "13:55"
    And clinic reschedule cutoff is 10 minutes before appointment
    When "Ivan Morales" requests reschedule to "16:00"
    Then the system rejects the request with status 422
    And the appointment status is updated to "Confirmed"

  Scenario: Waitlisted patient gets released slot
    Given the patient "Ivan Morales" is on the waitlist for the provider slot
    And the slot on "2026-04-10" at "10:00" is released by cancellation
    When the system runs waitlist reassignment
    Then the appointment is saved with status "Confirmed"
    And the slot remains reserved for "Ivan Morales"
