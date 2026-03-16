"""Site building batch service - create WordPress site placeholders from platform domains."""
from __future__ import annotations

import logging
import uuid
from uuid import UUID

import httpx
from sqlalchemy.orm import Session

from common.app.models import PlatformDomain
from common.app.models import PlatformDomainStatus
from common.app.models import Project
from common.app.models import TaskRun
from common.app.models import WordPressSite
from common.app.models import WordPressSiteStatus
from common.app.models import Workflow
from app.repositories.platform_domain_repository import PlatformDomainRepository
from app.repositories.project_repository import ProjectRepository
from app.repositories.wordpress_site_repository import WordPressSiteRepository


class SiteBuildingResult:
    """Result of create_batch. execution_items: (task_run_id, wordpress_site_id, domain, workflow_id) for workflow trigger."""

    def __init__(
        self,
        wordpress_site_ids: list[UUID],
        task_run_ids: list[UUID],
        execution_items: list[tuple[UUID, UUID, str, UUID]] | None = None,
    ) -> None:
        self.wordpress_site_ids = wordpress_site_ids
        self.task_run_ids = task_run_ids
        self.execution_items = execution_items or []


class SiteBuildingService:
    def __init__(
        self,
        db: Session,
        *,
        project_repo: ProjectRepository | None = None,
        platform_domain_repo: PlatformDomainRepository | None = None,
        wordpress_site_repo: WordPressSiteRepository | None = None,
        admin_service_url: str | None = None,
        workflow_service_url: str | None = None,
    ) -> None:
        self.db = db
        self.project_repo = project_repo or ProjectRepository(db)
        self.platform_domain_repo = platform_domain_repo or PlatformDomainRepository(db)
        self.wordpress_site_repo = wordpress_site_repo or WordPressSiteRepository(db)
        self.admin_service_url = admin_service_url
        self.workflow_service_url = workflow_service_url

    def create_batch(
        self,
        tenant_id: UUID,
        project_id: UUID,
        count: int,
        domain_ids: list[UUID],
        workflow_id: UUID | None = None,
    ) -> SiteBuildingResult:
        project = self.project_repo.get(project_id)
        if project is None or project.tenant_id != tenant_id:
            raise ValueError("Project not found or access denied")

        available = self.platform_domain_repo.get_available()
        available_ids = {d.id for d in available}
        requested = set(domain_ids)
        if not requested.issubset(available_ids):
            raise ValueError("Some domain_ids are not available")
        if len(domain_ids) < count:
            raise ValueError("Not enough domains provided for count")

        domains_to_use = [d for d in available if d.id in domain_ids][:count]

        if self.admin_service_url:
            from common.app.quota_client import check_quota_with_count

            allowed, err = check_quota_with_count(
                self.admin_service_url,
                tenant_id=str(tenant_id),
                resource="wordpress_sites_per_month",
                requested_count=count,
            )
            if not allowed:
                raise ValueError(err or "wordpress_sites_per_month quota exceeded")

        wordpress_site_ids: list[UUID] = []
        task_run_ids: list[UUID] = []
        execution_items: list[tuple[UUID, UUID, str, UUID]] = []

        workflow: Workflow | None = None
        if workflow_id:
            workflow = self.db.get(Workflow, workflow_id)
            if workflow is None or workflow.project_id != project_id:
                workflow = None

        for pd in domains_to_use:
            site = WordPressSite(
                tenant_id=tenant_id,
                project_id=project_id,
                name=pd.domain,
                domain=pd.domain,
                api_url=pd.api_base_url,
                username="pending",
                app_password="pending",
                status=WordPressSiteStatus.inactive,
                platform_domain_id=pd.id,
            )
            self.wordpress_site_repo.add(site)
            wordpress_site_ids.append(site.id)

            pd.status = PlatformDomainStatus.assigned

            if workflow:
                tr = TaskRun(
                    workflow_id=workflow.id,
                    execution_id=str(uuid.uuid4()),
                    task_template_id=None,
                    status="running",
                )
                self.db.add(tr)
                self.db.flush()
                task_run_ids.append(tr.id)
                execution_items.append((tr.id, site.id, pd.domain, workflow.id))

        return SiteBuildingResult(
            wordpress_site_ids=wordpress_site_ids,
            task_run_ids=task_run_ids,
            execution_items=execution_items,
        )

    def trigger_workflows_for_site_building(self, result: SiteBuildingResult) -> None:
        """Call workflow-service execute for each task run. Call after db.commit()."""
        if not self.workflow_service_url or not result.execution_items:
            return
        base = self.workflow_service_url.rstrip("/")
        for task_run_id, wordpress_site_id, domain, workflow_id in result.execution_items:
            try:
                with httpx.Client(timeout=30.0) as client:
                    response = client.post(
                        f"{base}/workflows/{workflow_id}/execute",
                        json={
                            "task_run_id": str(task_run_id),
                            "input_payload": {
                                "domain": domain,
                                "wordpress_site_id": str(wordpress_site_id),
                            },
                        },
                    )
                    response.raise_for_status()
            except httpx.HTTPError as e:
                logging.warning(
                    "Workflow trigger failed for task_run_id=%s: %s",
                    task_run_id,
                    str(e),
                )
