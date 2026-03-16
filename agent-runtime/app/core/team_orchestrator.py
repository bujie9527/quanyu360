"""Multi-agent team orchestration: sequential, parallel, review-loop execution."""
from __future__ import annotations

from datetime import datetime
from datetime import timezone
from typing import Any

import structlog

from app.core.config import get_settings
from app.core.runner import build_execution
from app.core.schemas import AgentExecutionResult
from app.core.schemas import AgentRunRequest
from app.core.schemas import ExecutionLogEntry
from app.core.schemas import MemberRunResult
from app.core.schemas import RuntimeTaskPayload
from app.core.schemas import TeamExecutionResult
from app.core.schemas import TeamMemberInput
from app.core.schemas import TeamRunRequest


class TeamOrchestrator:
    """
    Orchestrates multi-agent collaboration.

    Execution types:
    - sequential: Run agents in order, pass each output as input to next (e.g. Writer → Editor → Publisher)
    - parallel: Run all agents concurrently with same task, aggregate outputs
    - review_loop: Run agents in order; each reviewer gets prior output as context (Editor reviews Writer, etc.)
    """

    def __init__(self) -> None:
        self.settings = get_settings()
        self.logger = structlog.get_logger(self.settings.service_name).bind(component="team-orchestrator")

    def run(self, request: TeamRunRequest) -> TeamExecutionResult:
        """Execute team based on execution_type."""
        started_at = datetime.now(timezone.utc)
        logs: list[ExecutionLogEntry] = []
        exec_type = (request.execution_type or "sequential").lower().strip()

        if exec_type == "parallel":
            return self._run_parallel(request, started_at, logs)
        if exec_type == "review_loop":
            return self._run_review_loop(request, started_at, logs)
        return self._run_sequential(request, started_at, logs)

    def _run_sequential(
        self,
        request: TeamRunRequest,
        started_at: datetime,
        logs: list[ExecutionLogEntry],
    ) -> TeamExecutionResult:
        """Run agents in order; each receives prior output as augmented context."""
        member_results: list[MemberRunResult] = []
        accumulated_content: list[str] = []
        total_usage: dict[str, int] = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}

        sorted_members = sorted(request.members, key=lambda m: (m.order_index, m.agent_id))

        for i, member in enumerate(sorted_members):
            task = self._build_task_for_member(
                request.task,
                member,
                accumulated_content,
                is_first=i == 0,
            )
            run_req = AgentRunRequest(
                agent_id=member.agent_id,
                task_id=request.task_id,
                model=member.model,
                task=task,
                metadata={
                    **request.metadata,
                    "team_id": request.team_id,
                    "role_in_team": member.role_in_team,
                    "order_index": i,
                },
            )
            result = build_execution(run_req)

            content = result.result.get("content", "")
            member_results.append(
                MemberRunResult(
                    agent_id=member.agent_id,
                    role_in_team=member.role_in_team,
                    order_index=member.order_index,
                    status=result.status,
                    result=result.result,
                    content=content,
                )
            )
            accumulated_content.append(f"[{member.role_in_team}]: {content[:500]}")
            if result.usage:
                total_usage["prompt_tokens"] += result.usage.get("prompt_tokens", 0)
                total_usage["completion_tokens"] += result.usage.get("completion_tokens", 0)
            if result.status != "completed":
                completed_at = datetime.now(timezone.utc)
                return TeamExecutionResult(
                    team_id=request.team_id,
                    task_id=request.task_id,
                    execution_type="sequential",
                    status="failed",
                    member_results=member_results,
                    combined_result={"content": content, "error": f"Agent {member.role_in_team} failed"},
                    logs=logs,
                    usage=total_usage,
                    started_at=started_at,
                    completed_at=completed_at,
                )

        completed_at = datetime.now(timezone.utc)
        final_content = member_results[-1].content if member_results else ""
        return TeamExecutionResult(
            team_id=request.team_id,
            task_id=request.task_id,
            execution_type="sequential",
            status="completed",
            member_results=member_results,
            combined_result={"content": final_content, "stages": accumulated_content},
            logs=logs,
            usage=total_usage,
            started_at=started_at,
            completed_at=completed_at,
        )

    def _run_parallel(
        self,
        request: TeamRunRequest,
        started_at: datetime,
        logs: list[ExecutionLogEntry],
    ) -> TeamExecutionResult:
        """Run all agents concurrently; aggregate outputs."""
        import concurrent.futures

        member_results: list[MemberRunResult] = []
        total_usage: dict[str, int] = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        combined_contents: list[str] = []

        def run_one(member: TeamMemberInput) -> AgentExecutionResult:
            run_req = AgentRunRequest(
                agent_id=member.agent_id,
                task_id=request.task_id,
                model=member.model,
                task=request.task,
                metadata={
                    **request.metadata,
                    "team_id": request.team_id,
                    "role_in_team": member.role_in_team,
                },
            )
            return build_execution(run_req)

        sorted_members = sorted(request.members, key=lambda m: (m.order_index, m.agent_id))
        with concurrent.futures.ThreadPoolExecutor(max_workers=min(len(sorted_members), 8)) as pool:
            futures = {pool.submit(run_one, m): m for m in sorted_members}
            for fut in concurrent.futures.as_completed(futures):
                member = futures[fut]
                try:
                    result = fut.result()
                    content = result.result.get("content", "")
                    member_results.append(
                        MemberRunResult(
                            agent_id=member.agent_id,
                            role_in_team=member.role_in_team,
                            order_index=member.order_index,
                            status=result.status,
                            result=result.result,
                            content=content,
                        )
                    )
                    combined_contents.append(f"[{member.role_in_team}]: {content[:500]}")
                    if result.usage:
                        total_usage["prompt_tokens"] += result.usage.get("prompt_tokens", 0)
                        total_usage["completion_tokens"] += result.usage.get("completion_tokens", 0)
                    if result.status != "completed":
                        completed_at = datetime.now(timezone.utc)
                        return TeamExecutionResult(
                            team_id=request.team_id,
                            task_id=request.task_id,
                            execution_type="parallel",
                            status="failed",
                            member_results=member_results,
                            combined_result={"content": content, "error": f"Agent {member.role_in_team} failed"},
                            logs=logs,
                            usage=total_usage,
                            started_at=started_at,
                            completed_at=completed_at,
                        )
                except Exception as exc:
                    member_results.append(
                        MemberRunResult(
                            agent_id=member.agent_id,
                            role_in_team=member.role_in_team,
                            order_index=member.order_index,
                            status="failed",
                            result={},
                            content=str(exc),
                        )
                    )
                    completed_at = datetime.now(timezone.utc)
                    return TeamExecutionResult(
                        team_id=request.team_id,
                        task_id=request.task_id,
                        execution_type="parallel",
                        status="failed",
                        member_results=member_results,
                        combined_result={"error": str(exc)},
                        logs=logs,
                        usage=total_usage,
                        started_at=started_at,
                        completed_at=completed_at,
                    )

        member_results.sort(key=lambda r: (r.order_index, r.agent_id))
        completed_at = datetime.now(timezone.utc)
        total_usage["total_tokens"] = total_usage.get("prompt_tokens", 0) + total_usage.get("completion_tokens", 0)
        return TeamExecutionResult(
            team_id=request.team_id,
            task_id=request.task_id,
            execution_type="parallel",
            status="completed",
            member_results=member_results,
            combined_result={"content": "\n\n".join(combined_contents), "contributions": combined_contents},
            logs=logs,
            usage=total_usage,
            started_at=started_at,
            completed_at=completed_at,
        )

    def _run_review_loop(
        self,
        request: TeamRunRequest,
        started_at: datetime,
        logs: list[ExecutionLogEntry],
    ) -> TeamExecutionResult:
        """
        Review loop: run agents in order; each reviewer receives prior output.
        Similar to sequential but frames context as 'review prior work'.
        """
        member_results: list[MemberRunResult] = []
        accumulated_content: list[str] = []
        total_usage: dict[str, int] = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        max_review_rounds = 2  # Allow one review pass; can be made configurable

        sorted_members = sorted(request.members, key=lambda m: (m.order_index, m.agent_id))

        for round_idx in range(max_review_rounds):
            for i, member in enumerate(sorted_members):
                if round_idx == 0:
                    is_reviewer = i > 0
                else:
                    is_reviewer = True

                task = self._build_task_for_member(
                    request.task,
                    member,
                    accumulated_content,
                    is_first=(round_idx == 0 and i == 0),
                    is_review=is_reviewer,
                )
                run_req = AgentRunRequest(
                    agent_id=member.agent_id,
                    task_id=request.task_id,
                    model=member.model,
                    task=task,
                    metadata={
                        **request.metadata,
                        "team_id": request.team_id,
                        "role_in_team": member.role_in_team,
                        "order_index": i,
                        "review_round": round_idx,
                    },
                )
                result = build_execution(run_req)

                content = result.result.get("content", "")
                member_results.append(
                    MemberRunResult(
                        agent_id=member.agent_id,
                        role_in_team=member.role_in_team,
                        order_index=member.order_index,
                        status=result.status,
                        result=result.result,
                        content=content,
                    )
                )
                if round_idx == 0:
                    accumulated_content.append(f"[{member.role_in_team}]: {content[:500]}")
                else:
                    accumulated_content[i] = f"[{member.role_in_team} (round {round_idx + 1})]: {content[:500]}"

                if result.usage:
                    total_usage["prompt_tokens"] += result.usage.get("prompt_tokens", 0)
                    total_usage["completion_tokens"] += result.usage.get("completion_tokens", 0)
                if result.status != "completed":
                    completed_at = datetime.now(timezone.utc)
                    return TeamExecutionResult(
                        team_id=request.team_id,
                        task_id=request.task_id,
                        execution_type="review_loop",
                        status="failed",
                        member_results=member_results,
                        combined_result={"content": content, "error": f"Agent {member.role_in_team} failed"},
                        logs=logs,
                        usage=total_usage,
                        started_at=started_at,
                        completed_at=completed_at,
                    )
            if round_idx == 0:
                break  # Single pass by default; extend for multi-round review

        completed_at = datetime.now(timezone.utc)
        final_content = member_results[-1].content if member_results else ""
        total_usage["total_tokens"] = total_usage.get("prompt_tokens", 0) + total_usage.get("completion_tokens", 0)
        return TeamExecutionResult(
            team_id=request.team_id,
            task_id=request.task_id,
            execution_type="review_loop",
            status="completed",
            member_results=member_results,
            combined_result={"content": final_content, "stages": accumulated_content},
            logs=logs,
            usage=total_usage,
            started_at=started_at,
            completed_at=completed_at,
        )

    def _build_task_for_member(
        self,
        task: RuntimeTaskPayload,
        member: TeamMemberInput,
        prior_outputs: list[str],
        *,
        is_first: bool = False,
        is_review: bool = False,
    ) -> RuntimeTaskPayload:
        """Build task payload for a team member, augmenting with prior outputs when present."""
        if not prior_outputs:
            return task
        base_desc = task.description or ""
        context = "\n\n--- Prior output from team ---\n" + "\n\n".join(prior_outputs)
        if is_review:
            prefix = f"You are {member.role_in_team}. Review and improve the following:\n\n"
        else:
            prefix = f"You are {member.role_in_team}. Build on prior work:\n\n"
        return RuntimeTaskPayload(
            title=task.title,
            description=prefix + base_desc + context,
            input_payload=task.input_payload,
            expected_output=task.expected_output,
        )
