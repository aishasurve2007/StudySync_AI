"""
Auth dependency: turn a bearer token into a User row.

We use `HTTPBearer` (not OAuth2PasswordBearer): clients obtain a token from
/auth/register or /auth/login and send it as `Authorization: Bearer <token>`.
In Swagger this gives a single "paste your token" box under Authorize.

`auto_error=False` lets us raise a consistent 401 ourselves for missing,
malformed, or invalid tokens (HTTPBearer's default would raise 403 on a
missing header, which we don't want).
"""
import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.user import User

bearer_scheme = HTTPBearer(auto_error=False)

_credentials_error = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if creds is None or not creds.credentials:
        raise _credentials_error

    user_id = decode_access_token(creds.credentials)
    if user_id is None:
        raise _credentials_error
    try:
        uid = uuid.UUID(user_id)
    except ValueError:
        raise _credentials_error

    user = db.get(User, uid)
    if user is None:
        raise _credentials_error
    return user
