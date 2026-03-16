# Workflow Node Execution System

## Node Types

| Node Type | Description | Config / Requirements |
|-----------|-------------|------------------------|
| **agent_node** | Runs an agent via agent-runtime | `assigned_agent_id` or `config.agent_id`, `config.task_title`, `config.task_description`, `config.input_payload` |
| **tool_node** | Executes a tool (WordPress, Facebook, etc.) | `config.tool_name`, `config.action`, `config.parameters`; or `tool_id` (Tool.slug used as tool_name) |
| **condition_node** | Branch by context value | `config.key` (dot path), `config.equals`, `config.true_next_step`, `config.false_next_step` |
| **delay_node** | Sleep for N seconds | `config.seconds` |

## Example: Content Pipeline (generate_article → publish_wordpress → share_facebook)

### 1. Create Workflow via workflow-service

```json
POST /workflows
{
  "project_id": "<project-uuid>",
  "name": "Content Pipeline",
  "slug": "content-pipeline",
  "status": "active",
  "trigger_type": "manual",
  "definition": {},
  "steps": [
    {
      "step_key": "generate_article",
      "name": "Generate Article",
      "type": "agent_task",
      "config": {
        "task_title": "Write blog post",
        "task_description": "Write an article based on input topic",
        "input_payload": {}
      },
      "next_step": "publish_wordpress",
      "assigned_agent_id": "<writer-agent-uuid>"
    },
    {
      "step_key": "publish_wordpress",
      "name": "Publish to WordPress",
      "type": "tool_call",
      "config": {
        "tool_name": "wordpress",
        "action": "publish_post",
        "parameters": {
          "title": "",
          "content": "",
          "status": "publish"
        }
      },
      "next_step": "share_facebook"
    },
    {
      "step_key": "share_facebook",
      "name": "Share on Facebook",
      "type": "tool_call",
      "config": {
        "tool_name": "facebook",
        "action": "create_post",
        "parameters": {
          "page_id": "demo_page",
          "message": "",
          "link": ""
        }
      }
    }
  ]
}
```

### 2. Execute Workflow

```json
POST /workflows/{workflow_id}/execute
{
  "input_payload": {
    "topic": "AI and automation",
    "target_audience": "developers"
  }
}
```

### 3. Data Flow

- **generate_article** (agent_node): Agent writes article; output includes `content`, `title`.
- **publish_wordpress** (tool_node): Receives `_last_output`; maps `content`/`title` to parameters if not set.
- **share_facebook** (tool_node): Same; can use prior output for `message`, `link`.

### 4. Snapshot Structure (workflow-engine)

The workflow-service emits both `steps` (legacy) and `nodes` (with `node_key`, `node_type`). The engine prefers `nodes` when present and maps legacy step types to node types.
