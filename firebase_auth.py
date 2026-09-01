from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from firebase_admin import auth

from firebase_push import initialize_firebase
# 요청한 사람이 실제 누구인지 확인

bearer_scheme = HTTPBearer(auto_error=False)


def get_verified_firebase_claims(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> dict:
    if credentials is None:
        raise HTTPException(status_code=401, detail="Authentication required")

    if not initialize_firebase():
        raise HTTPException(status_code=503, detail="Firebase is unavailable")

    try:
        return auth.verify_id_token(credentials.credentials)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid Firebase token")
