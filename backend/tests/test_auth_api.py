from sqlalchemy import delete

from app.db.session import SessionLocal
from app.main import app
from app.models.user import User
from fastapi.testclient import TestClient


client = TestClient(app)

TEST_EMAIL = "api_test@example.com"
TEST_PASSWORD = "TestPassword123!"


def cleanup_test_user():
    db = SessionLocal()

    try:
        db.execute(delete(User).where(User.email == TEST_EMAIL))
        db.commit()
    finally:
        db.close()


def test_register_user():
    cleanup_test_user()

    response = client.post(
        "/api/v1/auth/register",
        json={
            "name": "API Test User",
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD,
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["name"] == "API Test User"
    assert data["email"] == TEST_EMAIL
    assert data["role"] == "employee"
    assert data["is_active"] is True

    # Password hash must never be returned
    assert "hashed_password" not in data


def test_duplicate_registration():
    cleanup_test_user()

    # First registration
    response = client.post(
        "/api/v1/auth/register",
        json={
            "name": "API Test User",
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD,
        },
    )

    assert response.status_code == 201

    # Second registration with same email
    response = client.post(
        "/api/v1/auth/register",
        json={
            "name": "Another User",
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD,
        },
    )

    assert response.status_code == 409

    assert response.json()["detail"] == "Email is already registered"


def test_login_success():
    cleanup_test_user()

    # Register user first
    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "name": "API Test User",
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD,
        },
    )

    assert register_response.status_code == 201

    # Login
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert len(data["access_token"]) > 0


def test_login_wrong_password():
    cleanup_test_user()

    client.post(
        "/api/v1/auth/register",
        json={
            "name": "API Test User",
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD,
        },
    )

    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": TEST_EMAIL,
            "password": "WrongPassword123!",
        },
    )

    assert response.status_code == 401

    assert response.json()["detail"] == "Invalid email or password"


def test_login_unknown_email():
    cleanup_test_user()

    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "does_not_exist@example.com",
            "password": TEST_PASSWORD,
        },
    )

    assert response.status_code == 401

    assert response.json()["detail"] == "Invalid email or password"


def test_users_me_without_token():
    cleanup_test_user()

    response = client.get("/api/v1/users/me")

    assert response.status_code == 401


def test_users_me_with_valid_token():
    cleanup_test_user()

    # Register
    client.post(
        "/api/v1/auth/register",
        json={
            "name": "API Test User",
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD,
        },
    )

    # Login
    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD,
        },
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    # Access protected endpoint
    response = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["email"] == TEST_EMAIL
    assert data["name"] == "API Test User"
    assert data["role"] == "employee"

    assert "hashed_password" not in data


def test_users_me_with_invalid_token():
    cleanup_test_user()

    response = client.get(
        "/api/v1/users/me",
        headers={"Authorization": "Bearer invalid.token.here"},
    )

    assert response.status_code == 401
