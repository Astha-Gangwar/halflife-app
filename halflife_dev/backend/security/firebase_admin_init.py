import firebase_admin
from firebase_admin import auth as firebase_auth

_app = None


def get_firebase_app():
    """Lazily initialize the Firebase Admin app, reusing the same
    Application Default Credentials already used for Firestore — no
    separate service account key or GCP setup needed, locally or on
    Cloud Run."""
    global _app
    if _app is None:
        _app = firebase_admin.initialize_app()
    return _app


def verify_firebase_id_token(token: str) -> dict:
    """Verifies a Firebase Authentication ID token (from the frontend's
    signInWithEmailAndPassword / createUserWithEmailAndPassword) and
    returns its decoded claims (uid, email, ...). Raises
    firebase_admin.auth.InvalidIdTokenError / ExpiredIdTokenError /
    ... on failure — callers translate those to an HTTP 401."""
    get_firebase_app()
    return firebase_auth.verify_id_token(token)
