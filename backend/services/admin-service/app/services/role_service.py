"""Role and user-role assignment business logic."""
from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException
from fastapi import status

from app.repositories import RoleRepository
from app.schemas.role_schemas import RoleCreateRequest
from app.schemas.role_schemas import RoleUpdateRequest
from app.schemas.role_schemas import UserRolesAssignRequest
from common.app.models import Role
from common.app.models import UserRoleAssignment


class RoleService:
    """Orchestrates role and user-role assignment logic."""

    def __init__(self, repo: RoleRepository):
        self.repo = repo

    def list_roles(self, limit: int = 50, offset: int = 0) -> tuple[list[Role], int]:
        return self.repo.list_roles(limit=limit, offset=offset)

    def get_role(self, role_id: UUID) -> Role:
        role = self.repo.get_role(role_id)
        if role is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found.")
        return role

    def create_role(self, payload: RoleCreateRequest) -> Role:
        existing = self.repo.get_role_by_slug(payload.slug)
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Role with slug '{payload.slug}' already exists.",
            )
        role = Role(
            slug=payload.slug,
            name=payload.name,
            description=payload.description,
        )
        self.repo.add_role(role)
        self.repo.db.commit()
        self.repo.db.refresh(role)
        return role

    def update_role(self, role_id: UUID, payload: RoleUpdateRequest) -> Role:
        role = self.get_role(role_id)
        if payload.slug is not None:
            existing = self.repo.get_role_by_slug(payload.slug)
            if existing is not None and existing.id != role_id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Role with slug '{payload.slug}' already exists.",
                )
            role.slug = payload.slug
        if payload.name is not None:
            role.name = payload.name
        if payload.description is not None:
            role.description = payload.description
        self.repo.db.commit()
        self.repo.db.refresh(role)
        return role

    def delete_role(self, role_id: UUID) -> None:
        role = self.get_role(role_id)
        self.repo.delete_role(role)
        self.repo.db.commit()

    def get_user_roles(self, user_id: UUID) -> list[UserRoleAssignment]:
        user = self.repo.get_user(user_id)
        if user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
        return self.repo.get_user_role_assignments(user_id)

    def unassign_role_from_user(
        self,
        user_id: UUID,
        role_id: UUID,
        tenant_id: UUID | None = None,
    ) -> None:
        if self.repo.get_user(user_id) is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
        if self.repo.get_role(role_id) is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found.")
        deleted = self.repo.delete_user_role_assignment(user_id, role_id, tenant_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User role assignment not found.",
            )
        self.repo.db.commit()

    def assign_roles_to_user(self, user_id: UUID, payload: UserRolesAssignRequest) -> list[UserRoleAssignment]:
        user = self.repo.get_user(user_id)
        if user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
        assignments = []
        for item in payload.roles:
            role = self.repo.get_role(item.role_id)
            if role is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Role {item.role_id} not found.",
                )
            tenant_id = item.tenant_id
            if self.repo.user_has_role(user_id, role.id, tenant_id):
                continue  # Already assigned
            assignment = UserRoleAssignment(
                user_id=user_id,
                role_id=role.id,
                tenant_id=tenant_id,
            )
            self.repo.add_user_role_assignment(assignment)
            assignments.append(assignment)
        self.repo.db.commit()
        for a in assignments:
            self.repo.db.refresh(a)
        return assignments
