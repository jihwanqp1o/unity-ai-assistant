"""backend/schemas.py — API 요청/응답 Pydantic 모델."""
from __future__ import annotations

from datetime import datetime
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
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AskRequest(BaseModel):
    question: str = Field(min_length=1)
    code_paste: Optional[str] = None


class AskResponse(BaseModel):
    answer: str
    mock: bool


class QuickCaptureIn(BaseModel):
    """에이전트가 캡처 직후 네이티브 입력창에서 받은 질문을 스크린샷과 함께 한 번에 보낼 때 사용."""

    screenshot_b64: str
    question: str = Field(min_length=1)
    code_paste: Optional[str] = None


class QuickCaptureOut(BaseModel):
    id: str
    session_url: str
    answer: str
    mock: bool
