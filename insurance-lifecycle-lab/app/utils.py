import calendar
import hashlib
import hmac
import os
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP

import jwt
from fastapi import Depends, Header
from sqlalchemy import func
from sqlalchemy.orm import Session

from .config import ACCESS_TOKEN_EXPIRE_MINUTES, JWT_ALGORITHM, JWT_SECRET
from .database import get_db
from .errors import AppError
from .models import AuditLog, User


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    iterations = 120000
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return f"pbkdf2_sha256${iterations}${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        algorithm, iterations, salt_hex, digest_hex = stored.split("$")
        if algorithm != "pbkdf2_sha256":
            return False
        digest = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), bytes.fromhex(salt_hex), int(iterations)
        )
        return hmac.compare_digest(digest.hex(), digest_hex)
    except Exception:
        return False


def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    payload = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    payload.update({"exp": expire})
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def get_current_user(
    authorization: str = Header(default=""), db: Session = Depends(get_db)
) -> User:
    if not authorization.startswith("Bearer "):
        raise AppError(401, "UNAUTHENTICATED", "Bearer token is required")
    token = authorization.split(" ", 1)[1].strip()
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("uid")
    except jwt.PyJWTError:
        raise AppError(401, "INVALID_TOKEN", "Token is invalid or expired")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise AppError(401, "INVALID_TOKEN", "Token subject no longer exists")
    return user


def get_current_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != "ADMIN":
        raise AppError(403, "FORBIDDEN", "Admin role is required")
    return user


def generate_no(prefix: str, db: Session, model, field: str = "id") -> str:
    count = db.query(func.count(model.id)).scalar() or 0
    return f"{prefix}{datetime.utcnow():%Y%m%d}{count + 1:06d}"


def add_audit(
    db: Session,
    entity_type: str,
    entity_id: int,
    action: str,
    from_status=None,
    to_status=None,
    operator: str = "SYSTEM",
    detail: dict = None,
) -> AuditLog:
    log = AuditLog(
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        from_status=from_status,
        to_status=to_status,
        operator=operator,
        detail=detail or {},
    )
    db.add(log)
    return log


def _days_in_month(year: int, month: int) -> int:
    return calendar.monthrange(year, month)[1]


def add_months(value: date, months: int) -> date:
    index = value.month - 1 + months
    year = value.year + index // 12
    month = index % 12 + 1
    day = min(value.day, _days_in_month(year, month))
    return date(year, month, day)


def months_between(start: date, end: date) -> int:
    return (end.year - start.year) * 12 + (end.month - start.month) - (
        1 if end.day < start.day else 0
    )


def money(value) -> Decimal:
    return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
