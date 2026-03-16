"""WordPress site business logic."""
from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException
from fastapi import status
from sqlalchemy.orm import Session

from app.repositories import ProjectRepository
from app.repositories.wordpress_site_repository import WordPressSiteRepository
from app.services.wordpress_client import test_wordpress_connection
from app.services.wordpress_client import WordPressConnectionResult
from common.app.models import WordPressSite
from common.app.models import WordPressSiteStatus


class WordPressSiteService:
    def __init__(
        self,
        db: Session,
        project_repo: ProjectRepository | None = None,
        site_repo: WordPressSiteRepository | None = None,
    ):
        self.db = db
        self.project_repo = project_repo or ProjectRepository(db)
        self.site_repo = site_repo or WordPressSiteRepository(db)

    def create_site(
        self,
        tenant_id: UUID,
        project_id: UUID,
        name: str,
        domain: str,
        api_url: str,
        username: str,
        app_password: str,
    ) -> WordPressSite:
        project = self.project_repo.get(project_id)
        if not project:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="项目不存在")
        if project.tenant_id != tenant_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="项目不属于当前租户")

        site = WordPressSite(
            tenant_id=tenant_id,
            project_id=project_id,
            name=name,
            domain=domain,
            api_url=api_url.rstrip("/"),
            username=username,
            app_password=app_password,
            status=WordPressSiteStatus.active,
        )
        self.site_repo.add(site)
        self.db.commit()
        self.db.refresh(site)
        return site

    def list_sites(self, tenant_id: UUID, project_id: UUID | None = None) -> list[WordPressSite]:
        return self.site_repo.get_by_tenant(tenant_id, project_id)

    def get_site(self, site_id: UUID, tenant_id: UUID) -> WordPressSite:
        site = self.site_repo.get(site_id, tenant_id)
        if not site:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="站点不存在")
        return site

    def delete_site(self, site_id: UUID, tenant_id: UUID) -> None:
        site = self.get_site(site_id, tenant_id)
        self.site_repo.delete(site)
        self.db.commit()

    def test_connection(self, site_id: UUID, tenant_id: UUID) -> WordPressConnectionResult:
        site = self.get_site(site_id, tenant_id)
        return test_wordpress_connection(
            api_url=site.api_url,
            username=site.username,
            app_password=site.app_password,
        )

    def update_credentials_internal(
        self,
        site_id: UUID,
        username: str,
        app_password: str,
        status: WordPressSiteStatus = WordPressSiteStatus.active,
    ) -> WordPressSite:
        site = self.db.get(WordPressSite, site_id)
        if not site:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="站点不存在")
        site.username = username
        site.app_password = app_password
        site.status = status
        self.db.commit()
        self.db.refresh(site)
        return site
