from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_auditor
from app.models.audit import User
from app.schemas.auth import (
    ForgotPasswordRequest,
    LoginRequest,
    LogoutRequest,
    MessageResponse,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserOut,
)
from app.services.auth_service import (
    AUDITOR_PORTAL_ROLES,
    authenticate_user,
    issue_tokens,
    register_user,
    revoke_refresh_token,
    verify_refresh_token,
)

router = APIRouter(prefix="/auth", tags=["Auth"])


def _ensure_auditor_role(user: User) -> None:
    if user.role not in AUDITOR_PORTAL_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Registration is available for auditor accounts only.",
        )


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(body: RegisterRequest, db: Session = Depends(get_db)):
    try:
        user = register_user(
            db,
            email=body.email.strip().lower(),
            password=body.password,
            full_name=body.full_name.strip(),
            company_name=body.company_name.strip() if body.company_name else None,
            phone=body.phone.strip() if body.phone else None,
            role="auditor",
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    _ensure_auditor_role(user)
    return issue_tokens(db, user)


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    user = authenticate_user(db, body.email.strip().lower(), body.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    _ensure_auditor_role(user)
    return issue_tokens(db, user)


@router.post("/refresh", response_model=TokenResponse)
def refresh(body: RefreshRequest, db: Session = Depends(get_db)):
    user = verify_refresh_token(db, body.refresh_token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")
    _ensure_auditor_role(user)
    revoke_refresh_token(db, body.refresh_token)
    return issue_tokens(db, user)


@router.post("/logout", response_model=MessageResponse)
def logout(body: LogoutRequest, db: Session = Depends(get_db)):
    revoke_refresh_token(db, body.refresh_token)
    return MessageResponse(message="Logged out successfully.")


@router.post("/forgot-password", response_model=MessageResponse)
def forgot_password(body: ForgotPasswordRequest, db: Session = Depends(get_db)):
    del db
    del body
    return MessageResponse(
        message=(
            "If an account exists for that email, password reset instructions will be sent. "
            "Password reset via email is not yet configured — contact your administrator."
        )
    )


@router.get("/me", response_model=UserOut)
def me(current_user: Annotated[User, Depends(get_current_auditor)]):
    return current_user
