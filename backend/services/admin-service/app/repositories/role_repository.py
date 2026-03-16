"""Role and permission data access."""
from __future__ import annotations

from uuid import UUID

from sqlalchemy import func
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.orm import selectinload

from common.app.models import Permission
from common.app.models import Role
from common.app.models import User
from common.app.models import UserRoleAssignment


class RoleRepository:
    """Handles database access for roles and permissions."""

    def __init__(self, db: Session):
        self.db = db

    def list_roles(
        self,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Role], int]:
        statement = select(Role).order_by(Role.slug.asc())
        items = list(self.db.scalars(statement.offset(offset).limit(limit)).all())
        total = self.db.scalar(select(func.count(Role.id))) or 0
        return items, total

    def get_role(self, role_id: UUID) -> Role | None:
        return self.db.get(Role, role_id)

    def get_role_by_slug(self, slug: str) -> Role | None:
        return self.db.scalar(select(Role).where(Role.slug == slug))

    def add_role(self, role: Role) -> None:
        self.db.add(role)

    def delete_role(self, role: Role) -> None:
        self.db.delete(role)

    def get_user(self, user_id: UUID) -> User | None:
        return self.db.get(User, user_id)

    def get_user_role_assignments(self, user_id: UUID) -> list[UserRoleAssignment]:
        return list(
            self.db.scalars(
                select(UserRoleAssignment)
                .options(selectinload(UserRoleAssignment.role))
                .where(UserRoleAssignment.user_id == user_id)
            ).unique().all()
        )

    def user_has_role(self, user_id: UUID, role_id: UUID, tenant_id: UUID | None) -> bool:
        stmt = select(UserRoleAssignment).where(
            UserRoleAssignment.user_id == user_id,
            UserRoleAssignment.role_id == role_id,
        )
        if tenant_id is None:
            stmt = stmt.where(UserRoleAssignment.tenant_id.is_(None))
        else:
            stmt = stmt.where(UserRoleAssignment.tenant_id == tenant_id)
        return self.db.scalar(stmt.limit(1)) is not None

    def add_user_role_assignment(self, assignment: UserRoleAssignment) -> None:
        self.db.add(assignment)

    def delete_user_role_assignment(
        self,
        user_id: UUID,
        role_id: UUID,
        tenant_id: UUID | None,
    ) -> bool:
        """Remove role from user. Returns True if deleted, False if not found."""
        stmt = select(UserRoleAssignment).where(
            UserRoleAssignment.user_id == user_id,
            UserRoleAssignment.role_id == role_id,
        )
        if tenant_id is None:
            stmt = stmt.where(UserRoleAssignment.tenant_id.is_(None))
        else:
            stmt = stmt.where(UserRoleAssignment.tenant_id == tenant_id)
        assignment = self.db.scalar(stmt.limit(1))
        if assignment:
            self.db.delete(assignment)
            return True
        return False

    def get_user_role_assignment(
        self,
        user_id: UUID,
        role_id: UUID,
        tenant_id: UUID | None,
    ) -> UserRoleAssignment | None:
        stmt = select(UserRoleAssignment).where(
            UserRoleAssignment.user_id == user_id,
            UserRoleAssignment.role_id == role_id,
        )
        if tenant_id is None:
            stmt = stmt.where(UserRoleAssignment.tenant_id.is_(None))
        else:
            stmt = stmt.where(UserRoleAssignment.tenant_id == tenant_id)
        return self.db.scalar(stmt.limit(1))

    def list_permissions(self) -> list[Permission]:
        return list(self.db.scalars(select(Permission).order_by(Permission.slug.asc())).all())
