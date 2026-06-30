from typing import Annotated
import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.audit import User
from app.services.auth_service import (
    AUDITOR_PORTAL_ROLES,
    decode_access_token,
    decode_access_token_payload,
)
from app.services.member_constants import role_has_permission
from app.services.member_service import MemberService
from app.services.tenant_context import TenantContext, TenantContextService

security = HTTPBearer(auto_error=False)
_member_service = MemberService()
_tenant_service = TenantContextService()


def get_current_user(
    db: Annotated[Session, Depends(get_db)],
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
) -> User:
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    try:
        user_id = decode_access_token(credentials.credentials)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail="Invalid token") from exc
    user = db.query(User).filter(User.id == user_id, User.is_active.is_(True)).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or inactive user")
    return user


def get_current_auditor(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    if current_user.role not in AUDITOR_PORTAL_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Auditor portal access required for this account.",
        )
    return current_user


def get_tenant_context(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_auditor)],
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
) -> TenantContext:
    token_org_id: uuid.UUID | None = None
    token_org_role: str | None = None

    if credentials:
        try:
            payload = decode_access_token_payload(credentials.credentials)
            if payload.get("org_id"):
                token_org_id = uuid.UUID(str(payload["org_id"]))
            token_org_role = payload.get("org_role")
        except (ValueError, TypeError):
            pass

    try:
        return _tenant_service.validate_token_org_claims(
            db,
            current_user,
            token_org_id=token_org_id,
            token_org_role=str(token_org_role) if token_org_role else None,
        )
    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc


def require_org_permission(permission: str):
    """RBAC dependency factory — checks org-scoped permission for the current user."""

    def _dependency(
        db: Annotated[Session, Depends(get_db)],
        current_user: Annotated[User, Depends(get_current_auditor)],
    ) -> User:
        org_id = _member_service.resolve_user_organization_id(db, current_user)
        if not org_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No organization linked to this account yet.",
            )
        membership = _member_service.get_caller_membership(db, current_user, org_id)
        if not role_has_permission(membership.role, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission for this action.",
            )
        return current_user

    return _dependency
