from unittest.mock import patch


#These tests validate the /api/auth/register endpoint wich indirectly test the register() and getSession() functions

# We are testing the full registration flow logic, including:
# - Successful user registration (201 response)
# - Handling of missing JSON body (400 response)
# - Validation of required fields (400 response)
# - Validation of allowed user roles (400 response)
# - Handling of database synchronization failures (500 response)
#
# The goal is to ensure the endpoint behaves correctly under both valid and invalid inputs,
# and returns appropriate HTTP status codes and error messages.
#
#
# External dependencies (Supabase sync) are mocked using unittest.mock.patch
# to isolate the route logic and avoid real database calls during testing.

#For testing go to backend directory in terminal: cd backend
#Run the test file with or equivalent: python3.13 -m pytest tests/test_routes_auth.py -v



#<------------------- SUCCESS ------------------->
def test_register_success(client):
    payload = {
        "user_id": "123",
        "first_name": "John",
        "last_name": "Doe",
        "username": "johndoe",
        "role": "patient",
    }

    with patch("app.routes.auth.sync_user_after_registration") as mock_sync:
        mock_sync.return_value = {}

        response = client.post("/api/auth/register", json=payload)

        assert response.status_code == 201
        assert response.get_json() == {
            "message": "User registered successfully."
        }


#<------------------- MISSING JSON ------------------->
def test_register_missing_json(client):
    response = client.post("/api/auth/register")

    assert response.status_code == 400
    assert response.get_json() == {
        "error": "Request body must be JSON."
    }



#<------------------- ISSING REQUIRED FIELDS ------------------->
def test_register_missing_required_fields(client):
    payload = {
        "user_id": "123",
        "role": "patient",
    }

    response = client.post("/api/auth/register", json=payload)

    assert response.status_code == 400

    data = response.get_json()

    assert "Missing required fields" in data["error"]



#<------------------- INVALID ROLE ------------------->
def test_register_invalid_role(client):
    payload = {
        "user_id": "123",
        "first_name": "John",
        "last_name": "Doe",
        "username": "johndoe",
        "role": "superhero",
    }

    response = client.post("/api/auth/register", json=payload)

    assert response.status_code == 400

    data = response.get_json()

    assert "Invalid role" in data["error"]



#<------------------- DB SYNC FAILURE ------------------->
def test_register_db_sync_failure(client):
    payload = {
        "user_id": "123",
        "first_name": "John",
        "last_name": "Doe",
        "username": "johndoe",
        "role": "patient",
    }

    with patch("app.routes.auth.sync_user_after_registration") as mock_sync:
        mock_sync.return_value = {
            "error": "Database insert failed",
            "step": "profiles",
        }

        response = client.post("/api/auth/register", json=payload)

        assert response.status_code == 500

        data = response.get_json()

        assert data["failed_at"] == "profiles"
        assert "DB sync failed" in data["error"]