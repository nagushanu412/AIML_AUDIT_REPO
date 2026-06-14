from __future__ import annotations

import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.audit import RefreshToken, User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
settings = get_settings()

AUDITOR_PORTAL_ROLES = frozenset({"auditor", "partner", "manager", "admin"})


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    if not hashed or not hashed.startswith("$2"):
        return False
    return pwd_context.verify(plain, hashed)


def _token_response(user: User, access_token: str, refresh_token: str) -> dict:
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": settings.jwt_expire_minutes * 60,
        "user_id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role,
    }


def create_access_token(user_id: uuid.UUID) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {"sub": str(user_id), "exp": expire, "type": "access"}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> uuid.UUID:
    try:
        payload = jwt.decode(
            token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
        )
        if payload.get("type") != "access":
            raise ValueError("Invalid token type")
        return uuid.UUID(payload["sub"])
    except (JWTError, ValueError, KeyError) as exc:
        raise ValueError("Invalid token") from exc


def _hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def create_refresh_token(db: Session, user_id: uuid.UUID) -> str:
    plain = secrets.token_urlsafe(48)
    token_hash = _hash_refresh_token(plain)
    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.jwt_refresh_expire_days)
    db.add(
        RefreshToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
        )
    )
    db.commit()
    return plain


def verify_refresh_token(db: Session, plain_token: str) -> User | None:
    token_hash = _hash_refresh_token(plain_token)
    now = datetime.now(timezone.utc)
    record = (
        db.query(RefreshToken)
        .filter(
            RefreshToken.token_hash == token_hash,
            RefreshToken.revoked_at.is_(None),
            RefreshToken.expires_at > now,
        )
        .first()
    )
    if not record:
        return None
    user = (
        db.query(User)
        .filter(User.id == record.user_id, User.is_active.is_(True))
        .first()
    )
    return user


def revoke_refresh_token(db: Session, plain_token: str) -> bool:
    token_hash = _hash_refresh_token(plain_token)
    record = (
        db.query(RefreshToken)
        .filter(
            RefreshToken.token_hash == token_hash,
            RefreshToken.revoked_at.is_(None),
        )
        .first()
    )
    if not record:
        return False
    record.revoked_at = datetime.now(timezone.utc)
    db.commit()
    return True


def revoke_all_refresh_tokens(db: Session, user_id: uuid.UUID) -> None:
    now = datetime.now(timezone.utc)
    db.query(RefreshToken).filter(
        RefreshToken.user_id == user_id,
        RefreshToken.revoked_at.is_(None),
    ).update({"revoked_at": now})
    db.commit()


def issue_tokens(db: Session, user: User) -> dict:
    access = create_access_token(user.id)
    refresh = create_refresh_token(db, user.id)
    return _token_response(user, access, refresh)


def authenticate_user(db: Session, email: str, password: str) -> User | None:
    user = db.query(User).filter(User.email == email).first()
    if not user or not user.is_active:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


def register_user(
    db: Session,
    *,
    email: str,
    password: str,
    full_name: str,
    company_name: str | None = None,
    phone: str | None = None,
    role: str = "auditor",
) -> User:
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        raise ValueError("An account with this email already exists.")

    user = User(
        email=email,
        password_hash=hash_password(password),
        full_name=full_name,
        company_name=company_name,
        phone=phone,
        role=role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def ensure_demo_user(db: Session) -> User:
    user = db.query(User).filter(User.email == settings.demo_user_email).first()
    if user:
        if user.password_hash == "pending" or not user.password_hash.startswith("$2"):
            user.password_hash = hash_password(settings.demo_user_password)
            user.full_name = user.full_name or "Nagarajan"
            db.commit()
            db.refresh(user)
        return user
    user = User(
        email=settings.demo_user_email,
        password_hash=hash_password(settings.demo_user_password),
        full_name="Nagarajan",
        role="auditor",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# Backward-compatible alias used by deps
decode_token = decode_access_token
