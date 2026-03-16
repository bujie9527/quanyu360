from __future__ import annotations

from datetime import datetime
from datetime import timezone

from fastapi import HTTPException
from fastapi import status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.schemas import LoginRequest
from app.schemas import RegisterRequest
from app.security import create_access_token
from app.security import hash_password
from app.security import verify_password
from common.app.models import AuditAction
from common.app.models import AuditLog
from common.app.models import Tenant
from common.app.models import TenantStatus
from common.app.models import User
from common.app.models import UserRole
from common.app.models import UserStatus


class AuthService:
    def __init__(self, db: Session):
        self.db = db

    def register_user(self, payload: RegisterRequest, actor: User | None) -> tuple[User, Tenant, bool]:
        tenant = self.db.scalar(select(Tenant).where(Tenant.slug == payload.tenant_slug))
        tenant_created = tenant is None

        if tenant is None:
            tenant = Tenant(
                name=payload.tenant_name or payload.tenant_slug.replace("-", " ").title(),
                slug=payload.tenant_slug,
                status=TenantStatus.active,
                plan_name="mvp",
                settings={"auth_bootstrap": True},
            )
            self.db.add(tenant)
            self.db.flush()
            target_role = UserRole.admin
        else:
            self._assert_registration_permissions(actor=actor, tenant=tenant, requested_role=payload.role)
            target_role = payload.role

        existing_user = self.db.scalar(
            select(User).where(
                User.tenant_id == tenant.id,
                User.email == payload.email,
            )
        )
        if existing_user is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A user with this email already exists in the tenant.",
            )

        user = User(
            tenant=tenant,
            email=payload.email,
            full_name=payload.full_name,
            hashed_password=hash_password(payload.password),
            role=target_role,
            status=UserStatus.active,
        )
        self.db.add(user)
        self.db.flush()

        self.db.add(
            AuditLog(
                tenant=tenant,
                actor_user=user if actor is None else actor,
                action=AuditAction.create,
                entity_type="user",
                entity_id=user.id,
                correlation_id=f"auth-register-{user.id}",
                user_agent="auth-service",
                payload={
                    "tenant_created": tenant_created,
                    "registered_email": user.email,
                    "role": user.role.value,
                },
            )
        )

        self.db.commit()
        self.db.refresh(user)
        self.db.refresh(tenant)
        return user, tenant, tenant_created

    def authenticate_user(self, payload: LoginRequest) -> tuple[str, int, User, Tenant]:
        tenant = self.db.scalar(select(Tenant).where(Tenant.slug == payload.tenant_slug))
        if tenant is None or tenant.status != TenantStatus.active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid tenant or credentials.",
            )

        user = self.db.scalar(
            select(User).where(
                User.tenant_id == tenant.id,
                User.email == payload.email,
            )
        )
        if user is None or not verify_password(payload.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid tenant or credentials.",
            )
        if user.status != UserStatus.active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive.",
            )

        user.last_login_at = datetime.now(timezone.utc)
        token, expires_in = create_access_token(user=user, tenant=tenant)

        self.db.add(
            AuditLog(
                tenant=tenant,
                actor_user=user,
                action=AuditAction.login,
                entity_type="user",
                entity_id=user.id,
                correlation_id=f"auth-login-{user.id}",
                user_agent="auth-service",
                payload={"email": user.email},
            )
        )
        self.db.commit()
        self.db.refresh(user)
        return token, expires_in, user, tenant

    @staticmethod
    def _assert_registration_permissions(actor: User | None, tenant: Tenant, requested_role: UserRole) -> None:
        if actor is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Registration into an existing tenant requires an authenticated admin or manager.",
            )
        if actor.tenant_id != tenant.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You cannot manage users for another tenant.",
            )
        if actor.role not in {UserRole.admin, UserRole.manager}:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admin or manager users can register new users.",
            )
        if actor.role == UserRole.manager and requested_role == UserRole.admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Managers cannot create admin users.",
            )
