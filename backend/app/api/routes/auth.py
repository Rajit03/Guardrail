from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import create_access_token
from app.schemas.user import UserRegister, UserLogin, UserOut, Token, MessageResponse
from app.services import auth_service
from app.api.dependencies import get_current_user
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new Guardrail user"
)
def register(
    user_in: UserRegister,
    db: Session = Depends(get_db)
):
    """Register a new user account with hashed password."""
    existing_user = auth_service.get_user_by_email(db, email=user_in.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email address already exists."
        )
    
    auth_service.create_user(db, user_in=user_in)
    return {"message": "User registered successfully"}


@router.post(
    "/login",
    response_model=Token,
    summary="Log in user and obtain JWT access token"
)
def login(
    credentials: UserLogin,
    db: Session = Depends(get_db)
):
    """Authenticate user with email and password, returning JWT bearer token."""
    user = auth_service.authenticate_user(
        db,
        email=credentials.email,
        password=credentials.password
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect email or password."
        )
    
    access_token = create_access_token(subject=user.id)
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


@router.get(
    "/me",
    response_model=UserOut,
    summary="Get details of current authenticated user"
)
def get_me(
    current_user: User = Depends(get_current_user)
):
    """Return profile information of currently authenticated user."""
    return current_user
