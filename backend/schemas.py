"""backend/schemas.py — API 요청/응답 Pydantic 모델."""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    email: str


class DeviceStartOut(BaseModel):
    device_code: str
    pair_url: str


class DevicePollOut(BaseModel):
    status: str  # pending | claimed
    token: Optional[str] = None


class SessionCreateOut(BaseModel):
    id: str
    session_url: str


class ScreenshotIn(BaseModel):
    screenshot_b64: str


class SessionOut(BaseModel):
    id: str
    screenshot_b64: Optional[str] = None
    question: Optional[str] = None
    code_paste: Optional[str] = None
    answer: Optional[str] = None
    status: str

    model_config = ConfigDict(from_attributes=True)


class AskRequest(BaseModel):
    question: str = Field(min_length=1)
    code_paste: Optional[str] = None


class AskResponse(BaseModel):
    answer: str
    mock: bool
