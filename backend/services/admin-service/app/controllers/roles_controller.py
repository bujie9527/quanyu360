"""Role and user-role admin HTTP endpoints."""
from uuid import UUID

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Query
from fastapi import status

from app.dependencies import get_role_service
from app.schemas.role_schemas import RoleCreateRequest
from app.schemas.role_schemas import RoleDetailResponse
from app.schemas.role_schemas import RoleUpdateRequest
from app.schemas.role_schemas import RoleListResponse
from app.schemas.role_schemas import RoleSummaryResponse
from app.schemas.role_schemas import UserRoleAssignmentResponse
from app.schemas.role_schemas import UserRolesAssignRequest
from app.services import RoleService
from common.app.models import Role

router = APIRouter(prefix="/admin", tags=["roles"])


def _to_summary(role: Role) -> RoleSummaryResponse:
    return RoleSummaryResponse(
        id=role.id,
        slug=role.slug,
        name=role.name,
        description=role.description,
        created_at=role.created_at,
        updated_at=role.updated_at,
    )


def _to_detail(role: Role) -> RoleDetailResponse:
    return RoleDetailResponse(
        id=role.id,
        slug=role.slug,
        name=role.name,
        description=role.description,
        created_at=role.created_at,
        updated_at=role.updated_at,
    )


@router.post("/roles", response_model=RoleDetailResponse, status_code=status.HTTP_201_CREATED)
def create_role(
    payload: RoleCreateRequest,
    role_service: RoleService = Depends(get_role_service),
) -> RoleDetailResponse:
    role = role_service.create_role(payload)
    return _to_detail(role)


@router.get("/roles", response_model=RoleListResponse)
def list_roles(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    role_service: RoleService = Depends(get_role_service),
) -> RoleListResponse:
    items, total = role_service.list_roles(limit=limit, offset=offset)
    return RoleListResponse(
        items=[_to_summary(r) for r in items],
        total=total,
    )


@router.get("/roles/{role_id}", response_model=RoleDetailResponse)
def get_role(
    role_id: UUID,
    role_service: RoleService = Depends(get_role_service),
) -> RoleDetailResponse:
    role = role_service.get_role(role_id)
    return _to_detail(role)


@router.put("/roles/{role_id}", response_model=RoleDetailResponse)
def update_role(
    role_id: UUID,
    payload: RoleUpdateRequest,
    role_service: RoleService = Depends(get_role_service),
) -> RoleDetailResponse:
    role = role_service.update_role(role_id, payload)
    return _to_detail(role)


@router.delete("/roles/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_role(
    role_id: UUID,
    role_service: RoleService = Depends(get_role_service),
) -> None:
    role_service.delete_role(role_id)


@router.get("/users/{user_id}/roles", response_model=list[UserRoleAssignmentResponse])
def get_user_roles(
    user_id: UUID,
    role_service: RoleService = Depends(get_role_service),
) -> list[UserRoleAssignmentResponse]:
    assignments = role_service.get_user_roles(user_id)
    return [
        UserRoleAssignmentResponse(
            id=a.id,
            user_id=a.user_id,
            role_id=a.role_id,
            tenant_id=a.tenant_id,
            created_at=a.created_at,
        )
        for a in assignments
    ]


@router.delete("/users/{user_id}/roles", status_code=status.HTTP_204_NO_CONTENT)
def unassign_role_from_user(
    user_id: UUID,
    role_id: UUID = Query(...),
    tenant_id: UUID | None = Query(default=None),
    role_service: RoleService = Depends(get_role_service),
) -> None:
    role_service.unassign_role_from_user(user_id, role_id=role_id, tenant_id=tenant_id)


@router.post("/users/{user_id}/roles", response_model=list[UserRoleAssignmentResponse])
def assign_roles_to_user(
    user_id: UUID,
    payload: UserRolesAssignRequest,
    role_service: RoleService = Depends(get_role_service),
) -> list[UserRoleAssignmentResponse]:
    assignments = role_service.assign_roles_to_user(user_id, payload)
    return [
        UserRoleAssignmentResponse(
            id=a.id,
            user_id=a.user_id,
            role_id=a.role_id,
            tenant_id=a.tenant_id,
            created_at=a.created_at,
        )
        for a in assignments
    ]
