"""Data access layer."""
from app.repositories.platform_domain_repository import PlatformDomainRepository
from app.repositories.role_repository import RoleRepository
from app.repositories.tenant_repository import TenantRepository

__all__ = ["PlatformDomainRepository", "RoleRepository", "TenantRepository"]
