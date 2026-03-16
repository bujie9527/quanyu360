from __future__ import annotations

from datetime import datetime
from datetime import timedelta
from datetime import timezone

from jose import JWTError
from jose import jwt
from passlib.context import CryptContext

from app.config import settings
from app.schemas import TokenClaims
from common.app.models import Tenant
from common.app.models import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(user: User, tenant: Tenant) -> tuple[str, int]:
    issued_at = datetime.now(timezone.utc)
    expires_at = issued_at + timedelta(minutes=settings.access_token_expire_minutes)

    payload = {
        "sub": str(user.id),
        "tenant_id": str(user.tenant_id),
        "tenant_slug": tenant.slug,
        "email": user.email,
        "role": user.role.value,
        "iss": settings.jwt_issuer,
        "aud": settings.jwt_audience,
        "iat": int(issued_at.timestamp()),
        "exp": int(expires_at.timestamp()),
    }
    token = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return token, settings.access_token_expire_minutes * 60


def decode_access_token(token: str) -> TokenClaims:
    payload = jwt.decode(
        token,
        settings.jwt_secret_key,
        algorithms=[settings.jwt_algorithm],
        audience=settings.jwt_audience,
        issuer=settings.jwt_issuer,
    )
    return TokenClaims.model_validate(payload)


def try_decode_access_token(token: str) -> TokenClaims | None:
    try:
        return decode_access_token(token)
    except JWTError:
        return None
