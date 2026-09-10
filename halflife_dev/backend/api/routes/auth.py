"""Demo-account login endpoint.

Real accounts authenticate via Firebase (email + password) — see
backend/security/authentication.py. This endpoint is what's left of the
old "sign in as any user_id, no password" dev-login: it now only ever
mints a token for the fixed read-only DEMO_USER_ID, so it can't be used
to sign in as anyone else. Kept as a real (non-dev-only) route since the
"View Demo" button in the UI depends on it in every environment.
"""
from datetime import timedelta
from backend.utils.clock import utcnow
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import jwt

from backend.security.authentication import JWT_SECRET, JWT_ALGORITHM, DEMO_USER_ID

router = APIRouter(prefix="/auth", tags=["Auth"])

class DevLoginRequest(BaseModel):
    user_id: str
    email: str | None = None

class DevLoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str

@router.post("/dev-login", response_model=DevLoginResponse)
def dev_login(request: DevLoginRequest):
    if request.user_id != DEMO_USER_ID:
        raise HTTPException(
            status_code=403,
            detail="This endpoint only signs in as the demo account. Sign in with your own email and password instead.",
        )

    payload = {
        "sub": DEMO_USER_ID,
        "email": request.email or f"{DEMO_USER_ID}@example.com",
        "exp": utcnow() + timedelta(hours=24),
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return DevLoginResponse(access_token=token, user_id=DEMO_USER_ID)
