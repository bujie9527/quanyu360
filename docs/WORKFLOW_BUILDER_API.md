# Workflow Builder API

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | /workflows | Create workflow (steps format) |
| POST | /workflows/builder | Create workflow (nodes, edges, configuration) |
| GET | /workflows | List workflows |
| GET | /workflows/{id} | Get workflow detail (steps format) |
| GET | /workflows/{id}/builder | Get workflow in builder format |
| POST | /workflow/run | Run a workflow |

## Workflow Builder Schema

### Nodes

```json
{
  "id": "generate_article",
  "type": "agent_node",
  "data": {
    "name": "Generate Article",
    "assigned_agent_id": "<uuid>",
    "task_title": "Write blog post",
    "task_description": "Write based on topic"
  },
  "position": { "x": 100, "y": 50 }
}
```

Node types: `agent_node`, `tool_node`, `condition_node`, `delay_node`

### Edges

```json
{
  "id": "e1",
  "source": "generate_article",
  "target": "publish_wordpress",
  "sourceHandle": null,
  "targetHandle": null
}
```

### Configuration

```json
{
  "trigger_type": "manual",
  "entry_node_id": "generate_article",
  "metadata": {}
}
```

## Example: Create and Run

### POST /workflows/builder

```json
{
  "project_id": "<project-uuid>",
  "name": "Content Pipeline",
  "slug": "content-pipeline",
  "status": "active",
  "nodes": [
    {
      "id": "generate_article",
      "type": "agent_node",
      "data": {
        "name": "Generate Article",
        "assigned_agent_id": "<writer-agent-uuid>",
        "task_title": "Write blog post",
        "task_description": "Write article based on input topic"
      }
    },
    {
      "id": "publish_wordpress",
      "type": "tool_node",
      "data": {
        "name": "Publish to WordPress",
        "tool_name": "wordpress",
        "action": "publish_post",
        "parameters": { "title": "", "content": "", "status": "publish" }
      }
    },
    {
      "id": "share_facebook",
      "type": "tool_node",
      "data": {
        "name": "Share on Facebook",
        "tool_name": "facebook",
        "action": "create_post",
        "parameters": { "page_id": "demo_page", "message": "", "link": "" }
      }
    }
  ],
  "edges": [
    { "source": "generate_article", "target": "publish_wordpress" },
    { "source": "publish_wordpress", "target": "share_facebook" }
  ],
  "configuration": {
    "trigger_type": "manual",
    "entry_node_id": "generate_article"
  }
}
```

### POST /workflow/run

```json
{
  "workflow_id": "<workflow-uuid>",
  "input_payload": {
    "topic": "AI and automation",
    "target_audience": "developers"
  }
}
```

### GET /workflows

Returns list of workflows (project_id, status, search query params supported).

### GET /workflows/{id}/builder

Returns workflow in builder format (nodes, edges, configuration).
