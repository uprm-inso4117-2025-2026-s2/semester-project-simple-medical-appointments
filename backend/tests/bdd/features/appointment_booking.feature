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
