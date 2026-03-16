# Multi-Agent Team Collaboration

## Entities

- **AgentTeam**: Team of agents that collaborate on tasks
- **TeamMember** (AgentTeamMember): Each member has `agent_id`, `role_in_team`, `order_index`

## Execution Types

| Type | Behavior |
|------|----------|
| **sequential** | Run agents in order; each receives prior output as context (Writer → Editor → Publisher) |
| **parallel** | Run all agents concurrently with same task; aggregate outputs |
| **review_loop** | Run in order; reviewers get prior output as context (Editor reviews Writer, etc.) |

## Example: Content Team

1. **Create agents** (via agent-service):
   - Writer Agent
   - Editor Agent
   - Publisher Agent

2. **Create team** (via project-service `POST /projects/{project_id}/teams`):

```json
{
  "name": "Content Team",
  "slug": "content-team",
  "description": "Writer, Editor, Publisher pipeline",
  "execution_type": "sequential",
  "members": [
    { "agent_id": "<writer-uuid>", "role_in_team": "Writer", "order_index": 0 },
    { "agent_id": "<editor-uuid>", "role_in_team": "Editor", "order_index": 1 },
    { "agent_id": "<publisher-uuid>", "role_in_team": "Publisher", "order_index": 2 }
  ]
}
```

3. **Create task** (via task-service `POST /tasks`):

```json
{
  "project_id": "<project-uuid>",
  "team_id": "<content-team-uuid>",
  "title": "Draft and publish blog post",
  "description": "Write, edit, then publish a post about AI",
  "input_payload": {}
}
```

4. **Run task** (`POST /tasks/{task_id}/run`): Worker dispatches to agent-runtime team endpoint.

## API Endpoints

- **Agent-runtime**: `POST /api/v1/teams/runs` — Team execution (called by task worker)
- **Project-service**: `POST/GET/PUT/DELETE /projects/{id}/teams` — Team CRUD
- **Task-service**: `POST /tasks` with `team_id` — Create team task

## Data Flow

```
Task (team_id set) → Worker loads team+members → POST /api/v1/teams/runs
  → TeamOrchestrator.run(sequential|parallel|review_loop)
  → Each agent runs via build_execution(AgentRunRequest)
  → Combined result returned to worker
```
