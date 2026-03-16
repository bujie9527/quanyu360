from fastapi import APIRouter
from fastapi import Depends
from fastapi import Response
from fastapi import status

from app.config import settings
from app.dependencies import get_current_user
from app.dependencies import get_db_session
from app.dependencies import get_optional_current_user
from app.schemas import AuthTokenResponse
from app.schemas import AuthenticatedUserResponse
from app.schemas import LoginRequest
from app.schemas import RegisterRequest
from app.schemas import RegisterResponse
from app.services import AuthService
from common.app.models import Tenant
from common.app.models import User
from common.app.observability.health import build_health_status
from common.app.observability.prometheus import basic_service_metrics
from common.app.observability.prometheus import build_metrics_response

router = APIRouter()


def build_user_response(user: User, tenant: Tenant) -> AuthenticatedUserResponse:
    return AuthenticatedUserResponse(
        id=user.id,
        tenant_id=user.tenant_id,
        tenant_slug=tenant.slug,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        status=user.status.value,
        created_at=user.created_at,
        updated_at=user.updated_at,
        last_login_at=user.last_login_at,
    )


@router.get("/health/live", tags=["health"])
def live() -> dict:
    return build_health_status(settings.service_name, status="live").model_dump(mode="json")


@router.get("/metrics", tags=["observability"])
def metrics() -> Response:
    return build_metrics_response(basic_service_metrics(settings.service_name))


@router.get("/health/ready", tags=["health"])
def ready() -> dict:
    return build_health_status(settings.service_name, status="ready").model_dump(mode="json")


@router.post("/auth/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED, tags=["auth"])
def register(
    payload: RegisterRequest,
    db=Depends(get_db_session),
    current_user: User | None = Depends(get_optional_current_user),
) -> RegisterResponse:
    service = AuthService(db)
    user, tenant, tenant_created = service.register_user(payload=payload, actor=current_user)
    return RegisterResponse(
        user=build_user_response(user, tenant),
        tenant_created=tenant_created,
    )


@router.post("/auth/login", response_model=AuthTokenResponse, tags=["auth"])
def login(
    payload: LoginRequest,
    db=Depends(get_db_session),
) -> AuthTokenResponse:
    service = AuthService(db)
    token, expires_in, user, tenant = service.authenticate_user(payload)
    return AuthTokenResponse(
        access_token=token,
        expires_in=expires_in,
        user=build_user_response(user, tenant),
    )


@router.get("/auth/me", response_model=AuthenticatedUserResponse, tags=["auth"])
def me(current_user: User = Depends(get_current_user)) -> AuthenticatedUserResponse:
    tenant = current_user.tenant
    return build_user_response(current_user, tenant)
