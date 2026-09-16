from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate, UserLogin


class AuthService:
    def __init__(self, db: Session):
        self.user_repository = UserRepository(db)

    def register_user(self, user_data: UserCreate) -> User:

        # 1. Check whether email already exists
        existing_user = self.user_repository.get_by_email(user_data.email)

        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email is already registered",
            )

        # 2. Hash the password
        hashed_password = hash_password(user_data.password)

        # 3. Create User model
        user = User(
            name=user_data.name,
            email=user_data.email,
            hashed_password=hashed_password,
            role="employee",
            is_active=True,
        )

        # 4. Save user
        return self.user_repository.create(user)

    def login_user(self, login_data: UserLogin) -> str:

        # 1. Find user by email
        user = self.user_repository.get_by_email(login_data.email)

        # 2. Prevent user enumeration
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        # 3. Verify password
        if not verify_password(
            login_data.password,
            user.hashed_password,
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        # 4. Check whether account is active
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive",
            )

        # 5. Generate JWT
        access_token = create_access_token(
            subject=str(user.id),
            role=user.role,
        )

        return access_token
