"""Dynamic tool loading: discover and load tools from tools folder.

Supports two discovery modes:
  1. tools/{name}/tool.py - folder per tool (primary)
  2. tools/plugins/{name}.py - legacy flat structure (fallback)

Example structure:
  tools/
    wordpress/
      tool.py
    facebook/
      tool.py
    seo/
      tool.py
"""
from __future__ import annotations

import importlib
import inspect
import logging
from pathlib import Path
from typing import Any
from typing import Callable

from tools.runtime.base import BaseTool

logger = logging.getLogger(__name__)

# Directories to skip during discovery
_SKIP_DIRS = frozenset({"runtime", "connectors", "plugins", "scripts", "__pycache__", ".git"})


class ToolLoader:
    """
    Discovers and loads tools dynamically from the tools folder.
    Scans subdirectories for tool.py (e.g. tools/wordpress/tool.py).
    """

    def __init__(self, tools_base_path: Path | None = None) -> None:
        """
        Args:
            tools_base_path: Root path for tools (default: tools package directory).
        """
        if tools_base_path is not None:
            self._base = Path(tools_base_path)
        else:
            # Resolve tools package location
            tools_pkg = importlib.import_module("tools")
            pkg_path = getattr(tools_pkg, "__path__", [])
            self._base = Path(pkg_path[0]) if pkg_path else Path("tools")

    def discover_factories(
        self,
        *,
        include_plugins: bool = True,
        enabled_only: tuple[str, ...] | None = None,
    ) -> dict[str, Callable[[], BaseTool]]:
        """
        Discover tool factories from tools folder.
        Returns {tool_name: factory} where factory() -> BaseTool instance.

        Args:
            include_plugins: Also scan tools/plugins/*.py for backward compatibility.
            enabled_only: If set, load only these tool names. Empty = load all.
        """
        factories: dict[str, Callable[[], BaseTool]] = {}

        # 1. Folder-based: tools/{name}/tool.py
        for name in self._list_tool_dirs():
            if enabled_only and name not in enabled_only:
                continue
            factory = self._load_tool_from_dir(name)
            if factory:
                instance = factory()
                factories[instance.name] = factory
                logger.debug("ToolLoader: loaded %s from tools/%s/tool.py", instance.name, name)

        # 2. Multi-tool dir: tools/wordpress/*.py (publish_post, update_post, etc.)
        wp_dir = self._base / "wordpress"
        if wp_dir.is_dir():
            _skip = {"__init__", "base", "site_resolver"}
            for path in sorted(wp_dir.glob("*.py")):
                if path.stem in _skip or path.name.startswith("_"):
                    continue
                factory = self._load_tool_from_module(f"tools.wordpress.{path.stem}")
                if factory:
                    inst = factory()
                    if enabled_only and inst.name not in enabled_only:
                        continue
                    if inst.name not in factories:
                        factories[inst.name] = factory
                        logger.debug("ToolLoader: loaded %s from tools/wordpress/%s.py", inst.name, path.stem)

        # 3. Multi-tool dir: tools/seo/*.py (keyword_research, generate_meta, etc.)
        seo_dir = self._base / "seo"
        if seo_dir.is_dir():
            _skip = {"__init__", "llm_client", "tool"}
            for path in sorted(seo_dir.glob("*.py")):
                if path.stem in _skip or path.name.startswith("_"):
                    continue
                factory = self._load_tool_from_module(f"tools.seo.{path.stem}")
                if factory:
                    inst = factory()
                    if enabled_only and inst.name not in enabled_only:
                        continue
                    if inst.name not in factories:
                        factories[inst.name] = factory
                        logger.debug("ToolLoader: loaded %s from tools/seo/%s.py", inst.name, path.stem)

        # 4. Legacy: tools/plugins/{name}.py
        if include_plugins:
            plugins_path = self._base / "plugins"
            if plugins_path.is_dir():
                for path in sorted(plugins_path.glob("*.py")):
                    if path.name.startswith("_"):
                        continue
                    factory = self._load_tool_from_module(f"tools.plugins.{path.stem}")
                    if factory:
                        inst = factory()
                        if enabled_only and inst.name not in enabled_only:
                            continue
                        if inst.name not in factories:
                            factories[inst.name] = factory
                            logger.debug("ToolLoader: loaded %s from tools/plugins/%s.py", inst.name, path.stem)

        return factories

    def _list_tool_dirs(self) -> list[str]:
        """List subdirectories that may contain tools (have tool.py)."""
        if not self._base.is_dir():
            return []
        return [
            d.name
            for d in self._base.iterdir()
            if d.is_dir()
            and d.name not in _SKIP_DIRS
            and not d.name.startswith("_")
            and (d / "tool.py").exists()
        ]

    def _load_tool_from_dir(self, dir_name: str) -> Callable[[], BaseTool] | None:
        """Load BaseTool subclass from tools/{dir_name}/tool.py."""
        module_name = f"tools.{dir_name}.tool"
        return self._load_tool_from_module(module_name)

    def _load_tool_from_module(self, module_name: str) -> Callable[[], BaseTool] | None:
        """Import module and return factory for first BaseTool subclass found."""
        try:
            mod = importlib.import_module(module_name)
        except Exception as exc:
            logger.warning("ToolLoader: failed to import %s: %s", module_name, exc)
            return None

        for _name, obj in inspect.getmembers(mod, inspect.isclass):
            if obj is BaseTool:
                continue
            if issubclass(obj, BaseTool) and obj.__module__ == mod.__name__:
                try:
                    instance = obj()
                    tool_name = instance.name
                except Exception as exc:
                    logger.warning("ToolLoader: failed to instantiate %s.%s: %s", module_name, obj.__name__, exc)
                    continue

                def make_factory(cls: type[BaseTool]) -> Callable[[], BaseTool]:
                    return lambda _c=cls: _c()

                return make_factory(obj)
        return None

    def load_all(
        self,
        *,
        include_plugins: bool = True,
        enabled_only: tuple[str, ...] | None = None,
    ) -> list[BaseTool]:
        """Discover and instantiate all tools. Returns list of BaseTool instances."""
        factories = self.discover_factories(include_plugins=include_plugins, enabled_only=enabled_only)
        return [f() for f in factories.values()]


def discover_tool_plugins(package_name: str = "tools.plugins") -> dict[str, Callable[[], BaseTool]]:
    """
    Legacy: Scan tools.plugins for BaseTool subclasses.
    Kept for backward compatibility. Prefer ToolLoader for new code.
    """
    loader = ToolLoader()
    return loader.discover_factories(include_plugins=True, enabled_only=None)
