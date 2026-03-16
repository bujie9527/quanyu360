# Tool Registry System

## Tool Interface

All tools implement:

| Member | Type | Description |
|--------|------|-------------|
| `name` | `str` | Unique tool identifier |
| `description` | `str` | Human-readable description for agent discovery |
| `actions` | `dict[str, ToolActionDefinition]` | Action definitions with parameters schema |
| `execute(action, parameters, context)` | → `ToolExecutionResult` | Execute the given action |

### Parameters Schema

Each action defines parameters via `ToolParameterDefinition`:

- `name`: Parameter name
- `type`: `string`, `number`, `boolean`, `array`, `object`
- `required`: Whether the parameter is required
- `description`: Human-readable description

## Dynamic Tool Loading

Tools are **auto-discovered at runtime** from the `tools` folder via `ToolLoader` and `ToolRegistry`.

### Structure

```
tools/
  wordpress/
    tool.py     # WordPressTool
  facebook/
    tool.py     # FacebookTool
  seo/
    tool.py     # SEOTool
  plugins/      # Legacy: tools/plugins/*.py (fallback)
  runtime/      # ToolLoader, ToolRegistry, BaseTool
  connectors/   # Shared connectors (WordPress, Facebook, etc.)
```

### Discovery Order

1. **Folder-based (primary)**: `tools/{name}/tool.py` — one folder per tool
2. **Legacy (fallback)**: `tools/plugins/{name}.py` — flat structure for backward compatibility

### Components

| Component | Role |
|-----------|------|
| **ToolLoader** | Scans tools folder, discovers `BaseTool` subclasses, returns factories |
| **ToolRegistry** | Holds loaded tools, provides `get()`, `list_tools()`, `execute()` |
| **get_tool_registry()** | Returns a populated `ToolRegistry` (cached); use `clear_registry_cache()` to force reload |

### Adding a New Tool

1. Create `tools/my_tool/tool.py`:

```python
from tools.runtime.base import StructuredTool, ToolActionDefinition, ToolParameterDefinition, ...

class MyTool(StructuredTool):
    name = "my_tool"
    description = "Does something useful."

    @property
    def actions(self):
        return {
            "do_thing": ToolActionDefinition(
                name="do_thing",
                description="Execute the thing.",
                parameters=[ToolParameterDefinition(name="input", type="string", description="...")],
            ),
        }

    def handle(self, action, payload, context):
        return ToolExecutionResult(tool_name=self.name, action=action, success=True, output={...})
```

2. The tool is discovered automatically. No manual registration needed.

### Configuration

- `ENABLED_TOOL_PLUGINS`: Comma-separated list to restrict which tools load. **Empty or unset** = load all discovered tools.
- Example: `ENABLED_TOOL_PLUGINS=wordpress,facebook` loads only those; `ENABLED_TOOL_PLUGINS=` loads all.

## Flow

```
tools/{name}/tool.py (BaseTool subclasses)
    → ToolLoader.discover_factories()
    → ToolRegistry.load_from_loader()
    → get_tool_registry()
    → list_tools() / execute()  ← Workflow engine, Agent runtime
```
