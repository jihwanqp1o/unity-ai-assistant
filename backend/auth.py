"""
backend/auth.py
----------------
회원가입/로그인/로그아웃 + React 프론트엔드용 로그인 세션(JWT, httpOnly 쿠키) 인증 의존성.
"""
from __future__ import annotations

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from backend.db import get_db
from backend.models import User
from backend.schemas import LoginRequest, SignupRequest, UserOut
from backend.security import create_session_token, decode_session_token, hash_password, verify_password

router = APIRouter(prefix="/api/auth", tags=["auth"])

COOKIE_NAME = "session_token"


def get_current_user(
    session_token: str | None = Cookie(default=None, alias=COOKIE_NAME),
    db: Session = Depends(get_db),
) -> User:
    user_id = decode_session_token(session_token) if session_token else None
    if user_id is None:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")
    return user


def _set_session_cookie(response: Response, user_id: int) -> None:
    token = create_session_token(user_id)
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        samesite="lax",
        max_age=60 * 60 * 24 * 30,
    )


@router.post("/signup", response_model=UserOut)
def signup(body: SignupRequest, response: Response, db: Session = Depends(get_db)) -> User:
    if db.query(User).filter(User.email == body.email).first():
        raise HTTPException(status_code=409, detail="이미 가입된 이메일입니다.")
    user = User(email=body.email, password_hash=hash_password(body.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    _set_session_cookie(response, user.id)
    return user


@router.post("/login", response_model=UserOut)
def login(body: LoginRequest, response: Response, db: Session = Depends(get_db)) -> User:
    user = db.query(User).filter(User.email == body.email).first()
    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="이메일 또는 비밀번호가 올바르지 않습니다.")
    _set_session_cookie(response, user.id)
    return user


@router.post("/logout")
def logout(response: Response) -> dict:
    response.delete_cookie(COOKIE_NAME)
    return {"ok": True}


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)) -> User:
    return user
