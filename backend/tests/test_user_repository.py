from app.db.session import SessionLocal
from app.models.user import User
from app.repositories.user_repository import UserRepository
from sqlalchemy import delete


def test_user_repository():

    db = SessionLocal()

    try:
        repository = UserRepository(db)

        test_email = "repository_test@example.com"

        existing_user = repository.get_by_email(test_email)

        if existing_user:
            db.execute(delete(User).where(User.email == test_email))
            db.commit()

        user = User(
            name="Repository Test",
            email=test_email,
            hashed_password="test_hash",
            role="employee",
        )

        created_user = repository.create(user)

        assert created_user.id is not None
        assert created_user.email == test_email

        found_user = repository.get_by_email(test_email)

        assert found_user is not None
        assert found_user.email == test_email

        found_by_id = repository.get_by_id(created_user.id)

        assert found_by_id is not None
        assert found_by_id.id == created_user.id

    finally:
        db.execute(delete(User).where(User.email == test_email))
        db.commit()
        db.close()
