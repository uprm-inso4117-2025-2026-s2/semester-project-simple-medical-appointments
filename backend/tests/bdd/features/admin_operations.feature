# Lecture: Behavior Driven Development (Schütz-Schmuck, UPRM)
# BDD stage: Formulation; acceptance criteria from discovery expressed as
#   executable Given/When/Then scenarios readable without code knowledge.
# Triad perspectives: customer (happy paths) + test (boundary/guard cases)

Feature: Admin User Management Operations
  As a clinic admin
  I need to manage user accounts
  So that access control stays accurate

  Background:
    Given I am authenticated as an admin

  Scenario: List users - admin retrieves paginated user list
    When I request the list of all users
    Then the response status is 200
    And the response body contains a "users" array
    And each user entry has "user_id", "email", "role", and "status" fields

  Scenario: Role assignment - admin assigns doctor role to existing user
    When I assign the "doctor" role to user "target-user-001"
    Then the response status is 200
    And the response body confirms role was updated to "doctor"

  Scenario: Role assignment - assigning a non-existent role returns error
    When I assign the "superuser" role to user "target-user-001"
    Then the response status is 400
    And the response body contains an error about invalid role

  Scenario: Deactivation - admin deactivates a user account
    When I deactivate user "target-user-001"
    Then the response status is 200
    And the response body confirms the user was deactivated

  Scenario: Deactivation - banned user appears inactive in list
    # Verifies that banned_until in the future causes status="inactive".
    # Status is derived at query time, not stored as a boolean in the DB.
    When I request the list of users including a banned user
    Then the response status is 200
    And the response includes a user with status "inactive"

  Scenario: Deactivation - admin cannot deactivate own account
    # Route-level guard: user_id == g.user_id returns 400 before Supabase call.
    When I deactivate my own account
    Then the response status is 400
