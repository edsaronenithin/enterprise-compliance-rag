from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.user import UserCreate, UserResponse, UserLogin, TokenResponse
from app.services.auth_service import AuthService


router = APIRouter(
    prefix="/api/v1/auth",
    tags=["Authentication"],
)


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(
    user_data: UserCreate,
    db: Session = Depends(get_db),
):
    auth_service = AuthService(db)

    return auth_service.register_user(user_data)


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
)
def login(
    login_data: UserLogin,
    db: Session = Depends(get_db),
):
    auth_service = AuthService(db)

    access_token = auth_service.login_user(login_data)

    return {
        "access_token": access_token,
        "token_type": "bearer",
    }
