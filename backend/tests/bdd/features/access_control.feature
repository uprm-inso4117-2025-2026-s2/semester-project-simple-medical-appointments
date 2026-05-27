# Lecture: Behavior Driven Development (Schütz-Schmuck, UPRM)
# BDD stage: Formulation; test-centric triad perspective: edge cases and
#   boundary conditions (non-admin attempting privileged operations).
# These scenarios exposed the missing admin_bp registration (gap, now fixed).

Feature: Admin Route Access Control
  As the system
  I need to restrict admin operations to admin users only
  So that non-privileged users cannot perform administrative actions

  Scenario: Non-admin user cannot list users
    Given I am authenticated as a patient
    When I request the list of all users
    Then the response status is 403

  Scenario: Non-admin user cannot assign roles
    Given I am authenticated as a patient
    When I assign the "doctor" role to user "target-user-001"
    Then the response status is 403

  Scenario: Non-admin user cannot deactivate users
    Given I am authenticated as a patient
    When I deactivate user "target-user-001"
    Then the response status is 403
