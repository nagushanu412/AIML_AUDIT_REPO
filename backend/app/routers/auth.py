from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_auditor
from app.models.audit import User
from app.schemas.auth import (
    AcceptInviteRequest,
    AcceptInviteResponse,
    ForgotPasswordRequest,
    InvitePreviewResponse,
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
from app.services.invite_service import accept_invite, preview_invite
from app.services.member_service import MemberService

router = APIRouter(prefix="/auth", tags=["Auth"])
_member_service = MemberService()


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
            create_organization=True,
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
    _member_service.activate_invited_memberships(db, user)
    return issue_tokens(db, user)


@router.post("/refresh", response_model=TokenResponse)
def refresh(body: RefreshRequest, db: Session = Depends(get_db)):
    user = verify_refresh_token(db, body.refresh_token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")
    _ensure_auditor_role(user)
    revoke_refresh_token(db, body.refresh_token)
    _member_service.activate_invited_memberships(db, user)
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


@router.get("/invite/preview", response_model=InvitePreviewResponse)
def invite_preview(token: str, db: Session = Depends(get_db)):
    try:
        preview = preview_invite(db, token)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return InvitePreviewResponse(
        email=preview.email,
        full_name=preview.full_name,
        organization_name=preview.organization_name,
        role=preview.role,
        role_label=preview.role_label,
        requires_password=preview.requires_password,
    )


@router.post("/invite/accept", response_model=AcceptInviteResponse)
def invite_accept(body: AcceptInviteRequest, db: Session = Depends(get_db)):
    try:
        tokens, message = accept_invite(db, body.token, body.password)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if tokens:
        return AcceptInviteResponse(
            message=message,
            requires_login=False,
            access_token=tokens["access_token"],
            refresh_token=tokens["refresh_token"],
            token_type=tokens["token_type"],
            expires_in=tokens["expires_in"],
            user_id=tokens["user_id"],
            email=tokens["email"],
            full_name=tokens["full_name"],
            role=tokens["role"],
            organization_id=tokens.get("organization_id"),
            member_role=tokens.get("member_role"),
        )

    return AcceptInviteResponse(message=message, requires_login=True)


@router.get("/me", response_model=UserOut)
def me(current_user: Annotated[User, Depends(get_current_auditor)]):
    return current_user
