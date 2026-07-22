"""
backend/devices.py
--------------------
로컬 캡처 에이전트 페어링 (device-code 플로우, `gh auth login`과 동일한 패턴).

1) 에이전트가 POST /pair/start 호출 → device_code 발급.
2) 사용자가 브라우저에서 로그인 후 그 코드를 승인(POST /pair/{code}/claim).
3) 에이전트는 GET /pair/{code}를 폴링하다가 status=claimed가 되면 토큰을 받아 로컬에 저장.

MVP 범위 결정: device_code에 만료 시간을 두지 않았다 (짧은 세션 동안만 쓰인다고 가정).
운영 환경으로 확장 시 생성 시각 기준 TTL과 재사용 방지를 추가해야 한다.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from backend.auth import get_current_user
from backend.db import get_db
from config import FRONTEND_BASE_URL
from backend.models import Device, User
from backend.schemas import DevicePollOut, DeviceStartOut
from backend.security import generate_device_code, generate_device_token, hash_device_token

router = APIRouter(prefix="/api/devices", tags=["devices"])


def get_current_device(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> Device:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="에이전트 인증 토큰이 필요합니다.")
    token = authorization.removeprefix("Bearer ").strip()
    device = (
        db.query(Device)
        .filter(Device.token_hash == hash_device_token(token), Device.status == "claimed")
        .first()
    )
    if device is None:
        raise HTTPException(status_code=401, detail="유효하지 않은 기기 토큰입니다.")
    return device


@router.post("/pair/start", response_model=DeviceStartOut)
def start_pairing(db: Session = Depends(get_db)) -> DeviceStartOut:
    code = generate_device_code()
    device = Device(device_code=code, status="pending")
    db.add(device)
    db.commit()
    return DeviceStartOut(device_code=code, pair_url=f"{FRONTEND_BASE_URL}/pair?code={code}")


@router.get("/pair/{code}", response_model=DevicePollOut)
def poll_pairing(code: str, db: Session = Depends(get_db)) -> DevicePollOut:
    device = db.query(Device).filter(Device.device_code == code).first()
    if device is None:
        raise HTTPException(status_code=404, detail="존재하지 않는 페어링 코드입니다.")
    if device.status != "claimed":
        return DevicePollOut(status="pending")
    return DevicePollOut(status="claimed", token=device.pending_token)


@router.post("/pair/{code}/claim")
def claim_pairing(code: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    device = db.query(Device).filter(Device.device_code == code).first()
    if device is None:
        raise HTTPException(status_code=404, detail="존재하지 않는 페어링 코드입니다.")
    if device.status == "claimed":
        raise HTTPException(status_code=409, detail="이미 승인된 코드입니다.")

    raw_token = generate_device_token()
    device.user_id = user.id
    device.token_hash = hash_device_token(raw_token)
    device.pending_token = raw_token
    device.status = "claimed"
    db.commit()
    return {"ok": True}
