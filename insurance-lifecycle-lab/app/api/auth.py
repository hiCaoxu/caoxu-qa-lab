from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..auth import create_access_token, get_current_user, hash_password, verify_password
from ..database import get_db
from ..errors import AppError
from ..models import User
from ..schemas import LoginRequest, RegisterRequest, TokenResponse, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserOut, status_code=201)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    if db.query(User).filter(User.username == payload.username).first():
        raise AppError(409, "USERNAME_EXISTS", "Username is already registered")
    if len(payload.password) < 6:
        raise AppError(422, "WEAK_PASSWORD", "Password must be at least 6 characters")
    if len(payload.id_no) < 6:
        raise AppError(422, "INVALID_ID_NO", "ID number is too short")
    if len(payload.phone) < 7:
        raise AppError(422, "INVALID_PHONE", "Phone number is too short")

    user = User(
        username=payload.username,
        password_hash=hash_password(payload.password),
        role="USER",
        full_name=payload.full_name,
        phone=payload.phone,
        id_no=payload.id_no,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == payload.username).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise AppError(401, "INVALID_CREDENTIALS", "Invalid username or password")

    token = create_access_token(
        {"sub": user.username, "uid": user.id, "role": user.role}
    )
    return TokenResponse(access_token=token, token_type="Bearer")


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user
