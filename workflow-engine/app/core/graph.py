"""WorkflowGraph: node-based workflow structure with id, type, config, next_nodes."""
from __future__ import annotations

from typing import Any


class WorkflowNode:
    """Node schema: id, type, config, next_nodes."""

    __slots__ = ("id", "type", "config", "next_nodes")

    def __init__(
        self,
        id: str,
        type: str,
        config: dict[str, Any] | None = None,
        next_nodes: list[str] | None = None,
    ) -> None:
        self.id = id
        self.type = type
        self.config = config or {}
        self.next_nodes = next_nodes or []

    def __repr__(self) -> str:
        return f"WorkflowNode(id={self.id!r}, type={self.type!r}, next_nodes={self.next_nodes})"

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "WorkflowNode":
        next_raw = d.get("next_nodes") or d.get("next_node")
        if next_raw is None:
            next_raw = d.get("next_step")
        next_nodes: list[str] = []
        if isinstance(next_raw, list):
            next_nodes = [str(n) for n in next_raw]
        elif next_raw is not None:
            next_nodes = [str(next_raw)]
        return cls(
            id=str(d.get("id", d.get("node_key", d.get("step_key", "")))),
            type=str(d.get("type", d.get("node_type", "start"))).lower(),
            config=dict(d.get("config", {})),
            next_nodes=next_nodes,
        )


class WorkflowGraph:
    """Node-based workflow graph: nodes by id, entry point, traversal."""

    def __init__(self) -> None:
        self._nodes: dict[str, WorkflowNode] = {}
        self._entry_id: str | None = None

    def add_node(self, node: WorkflowNode) -> None:
        self._nodes[node.id] = node

    def set_entry(self, node_id: str) -> None:
        self._entry_id = node_id

    def get_node(self, node_id: str) -> WorkflowNode | None:
        return self._nodes.get(node_id)

    def get_entry_node(self) -> WorkflowNode | None:
        if self._entry_id:
            return self._nodes.get(self._entry_id)
        return None

    def nodes(self) -> list[WorkflowNode]:
        return list(self._nodes.values())

    @classmethod
    def from_definition(cls, definition: dict[str, Any]) -> "WorkflowGraph":
        """Build graph from workflow definition (nodes or steps)."""
        graph = cls()
        nodes_data = definition.get("nodes") or definition.get("steps") or []

        for item in nodes_data:
            if isinstance(item, dict):
                node = WorkflowNode.from_dict(item)
            else:
                node = WorkflowNode.from_dict(item.model_dump(mode="json"))
            graph.add_node(node)

        entry_id = definition.get("entry_node_id") or definition.get("configuration", {}).get("entry_node_id")
        if not entry_id and graph._nodes:
            first = list(graph._nodes.values())[0]
            entry_id = first.id
        if entry_id:
            graph.set_entry(str(entry_id))

        return graph
