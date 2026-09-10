import logging
import os
import jwt
import firebase_admin.auth
from fastapi import Depends, Request, HTTPException
from backend.domain.schemas.users import User
from backend.security.firebase_admin_init import verify_firebase_id_token

logger = logging.getLogger(__name__)

# "jwt" (default) verifies a real bearer token. "simulate" is a dev-only
# fallback that trusts an X-User-Id header outright — opt in explicitly via
# env var, never the silent default, so a misconfigured deployment fails
# closed (missing/invalid token) rather than open.
AUTH_MODE = os.environ.get("AUTH_MODE", "jwt")
JWT_SECRET = os.environ.get("JWT_SECRET", "dev-only-insecure-secret-change-me")
JWT_ALGORITHM = os.environ.get("JWT_ALGORITHM", "HS256")

# The fixed demo account (see scripts/seed_synthetic_data.py) is a shared,
# read-only showcase — anyone can sign in as it via dev-login to see a
# populated app instead of an empty one, but nothing should ever be able to
# write to it, or the next visitor sees whatever the last one left behind.
DEMO_USER_ID = os.environ.get("DEMO_USER_ID", "demo")


def get_current_user(request: Request) -> User:
    """Authenticated-user dependency. This is the only place `user_id` is
    established from a request — every route trusts it, never a body/query
    argument the caller supplies (Batch 5 AUTH-001/AUTH-007)."""
    if AUTH_MODE == "simulate":
        return _simulate_user(request)
    return _verify_jwt_user(request)


def _simulate_user(request: Request) -> User:
    user_id = request.headers.get("X-User-Id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthenticated")
    return User(user_id=user_id, auth_subject=user_id, email=f"{user_id}@example.com")


def _verify_jwt_user(request: Request) -> User:
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")

    token = auth_header[len("Bearer "):]

    # Real accounts authenticate via Firebase (email + password) — this
    # library-signed ID token is not forgeable without Firebase's private
    # key, unlike our own dev-login JWT below, so verifying it is what
    # actually proves "this really is that person" rather than just
    # trusting whatever user_id a request claims.
    try:
        decoded = verify_firebase_id_token(token)
        return User(
            user_id=decoded["uid"],
            auth_subject=decoded["uid"],
            email=decoded.get("email"),
            display_name=decoded.get("name"),
        )
    except (firebase_admin.auth.InvalidIdTokenError, firebase_admin.auth.ExpiredIdTokenError,
            firebase_admin.auth.RevokedIdTokenError, ValueError) as e:
        # Falling through to the legacy JWT path below is normal for an
        # actually-legacy token, but if this token was in fact a real
        # Firebase ID token, the fallback's own error (e.g. a PyJWT
        # algorithm-mismatch complaint) is misleading on its own -- log the
        # real reason Firebase Admin rejected it so a misconfiguration
        # (wrong project ID, credentials issue, etc.) is diagnosable from
        # logs instead of requiring this exact investigation again.
        logger.info("Firebase ID token verification failed, falling back to legacy JWT: %s", e)

    # Fall back to our own signed JWT. Minting one still requires
    # JWT_SECRET, which only the server holds — the actual "log in as
    # anyone" hole this closed was /auth/dev-login handing one out over an
    # unauthenticated HTTP call for whatever user_id was requested; that
    # route now only ever mints one for the fixed demo account. Test
    # fixtures also mint these directly (see tests/conftest.py's
    # auth_headers) to simulate arbitrary users without needing a real
    # Firebase token per test.
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {e}")

    subject = payload.get("sub")
    if not subject:
        raise HTTPException(status_code=401, detail="Token missing 'sub' claim")

    return User(
        user_id=subject,
        auth_subject=subject,
        email=payload.get("email"),
        display_name=payload.get("name"),
    )


def require_mutation_allowed(user: User = Depends(get_current_user)) -> User:
    """Use this instead of get_current_user on any route that creates,
    updates, or deletes data. Every read-only route keeps get_current_user
    directly — the demo account can still browse fine, it just can't
    change anything."""
    if user.user_id == DEMO_USER_ID:
        raise HTTPException(
            status_code=403,
            detail="This is a read-only demo account. Sign in with your own account to try it yourself.",
        )
    return user
