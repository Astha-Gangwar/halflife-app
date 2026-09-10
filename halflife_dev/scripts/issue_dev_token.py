"""Issue a JWT for local manual testing against AUTH_MODE=jwt (the default).

Usage:
    python scripts/issue_dev_token.py user-123
"""
import sys
import os
from datetime import datetime, timedelta
from backend.utils.clock import utcnow

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import jwt
from backend.security.authentication import JWT_SECRET, JWT_ALGORITHM

if __name__ == "__main__":
    user_id = sys.argv[1] if len(sys.argv) > 1 else "dev-user"
    payload = {
        "sub": user_id,
        "email": f"{user_id}@example.com",
        "exp": utcnow() + timedelta(hours=24),
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    print(token)
