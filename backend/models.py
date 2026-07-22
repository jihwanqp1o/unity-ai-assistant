"""
backend/models.py
------------------
SQLAlchemy ORM 모델 3개: User(계정), Device(로컬 캡처 에이전트 페어링), CaptureSession(캡처→질문 세션).
"""
from __future__ import annotations

import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import relationship

from backend.db import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    devices = relationship("Device", back_populates="user")
    sessions = relationship("CaptureSession", back_populates="user")


class Device(Base):
    """로컬 캡처 에이전트 하나당 한 행. device_code로 페어링을 시작하고,
    승인되면 user_id + token_hash가 채워져 이후 에이전트 인증에 쓰인다."""

    __tablename__ = "devices"

    id = Column(Integer, primary_key=True)
    device_code = Column(String, unique=True, nullable=False, index=True)
    status = Column(String, nullable=False, default="pending")  # pending | claimed
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    token_hash = Column(String, nullable=True, index=True)
    pending_token = Column(String, nullable=True)  # 최초 poll 응답으로 에이전트에 전달할 평문 토큰
    created_at = Column(DateTime, server_default=func.now())

    user = relationship("User", back_populates="devices")


class CaptureSession(Base):
    """핫키 캡처 1회 = 세션 1개. 에이전트가 생성+스크린샷 업로드, 웹 UI가 질문/답변을 채운다."""

    __tablename__ = "capture_sessions"

    id = Column(String, primary_key=True, default=lambda: uuid.uuid4().hex)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    screenshot_b64 = Column(Text, nullable=True)
    question = Column(Text, nullable=True)
    code_paste = Column(Text, nullable=True)
    answer = Column(Text, nullable=True)
    status = Column(String, nullable=False, default="capturing")  # capturing|ready|answered
    created_at = Column(DateTime, server_default=func.now())

    user = relationship("User", back_populates="sessions")
