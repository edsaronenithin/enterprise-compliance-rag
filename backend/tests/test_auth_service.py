from sqlalchemy import delete

from app.db.session import SessionLocal
from app.models.user import User
from app.schemas.user import UserCreate
from app.services.auth_service import AuthService
from app.core.security import verify_password


def test_register_user():

    db = SessionLocal()

    test_email = "auth_test@example.com"

    try:
        # Clean up any previous test data
        db.execute(delete(User).where(User.email == test_email))
        db.commit()

        service = AuthService(db)

        user_data = UserCreate(
            name="Auth Test",
            email=test_email,
            password="TestPassword123!",
        )

        user = service.register_user(user_data)

        # User created
        assert user.id is not None

        # Basic information
        assert user.name == "Auth Test"
        assert user.email == test_email

        # Default role
        assert user.role == "employee"

        # Password should NOT be stored as plain text
        assert user.hashed_password != "TestPassword123!"

        # Password hash should actually verify
        assert verify_password(
            "TestPassword123!",
            user.hashed_password,
        )

    finally:
        db.execute(delete(User).where(User.email == test_email))
        db.commit()
        db.close()
