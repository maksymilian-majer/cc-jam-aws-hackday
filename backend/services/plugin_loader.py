"""Plugin loader system for dynamically loading scraper plugins."""

import importlib
import importlib.util
import logging
from pathlib import Path
from typing import Type

from backend.plugins.base import ScraperPlugin

logger = logging.getLogger(__name__)

# Registry to store loaded plugin classes
_plugin_registry: dict[str, Type[ScraperPlugin]] = {}


def get_plugins_directory() -> Path:
    """Get the path to the plugins directory.

    Returns:
        Path to the backend/plugins directory.
    """
    return Path(__file__).parent.parent / "plugins"


def scan_plugin_files() -> list[Path]:
    """Scan the plugins directory for plugin files.

    Returns:
        List of paths to plugin Python files (excluding __init__.py and base.py).
    """
    plugins_dir = get_plugins_directory()
    plugin_files: list[Path] = []

    if not plugins_dir.exists():
        logger.warning(f"Plugins directory not found: {plugins_dir}")
        return plugin_files

    for file_path in plugins_dir.glob("*.py"):
        # Exclude __init__.py and base.py
        if file_path.name in ("__init__.py", "base.py"):
            continue
        plugin_files.append(file_path)

    return plugin_files


def load_plugin_from_file(file_path: Path) -> list[Type[ScraperPlugin]]:
    """Dynamically load plugin classes from a Python file.

    Args:
        file_path: Path to the plugin Python file.

    Returns:
        List of ScraperPlugin subclasses found in the file.
    """
    plugins: list[Type[ScraperPlugin]] = []

    try:
        # Create module name from file path
        module_name = f"backend.plugins.{file_path.stem}"

        # Load the module spec
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        if spec is None or spec.loader is None:
            logger.error(f"Could not load spec for {file_path}")
            return plugins

        # Create and execute the module
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # Find all ScraperPlugin subclasses in the module
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if (
                isinstance(attr, type)
                and issubclass(attr, ScraperPlugin)
                and attr is not ScraperPlugin
            ):
                plugins.append(attr)
                logger.info(f"Loaded plugin: {attr.name} from {file_path.name}")

    except Exception as e:
        logger.error(f"Error loading plugin from {file_path}: {e}")

    return plugins


def load_all_plugins() -> dict[str, Type[ScraperPlugin]]:
    """Load all plugins from the plugins directory.

    Returns:
        Dictionary mapping plugin names to plugin classes.
    """
    global _plugin_registry
    _plugin_registry.clear()

    plugin_files = scan_plugin_files()

    for file_path in plugin_files:
        plugin_classes = load_plugin_from_file(file_path)
        for plugin_class in plugin_classes:
            _plugin_registry[plugin_class.name] = plugin_class

    logger.info(f"Loaded {len(_plugin_registry)} plugins: {list(_plugin_registry.keys())}")
    return _plugin_registry


def reload_plugins() -> dict[str, Type[ScraperPlugin]]:
    """Reload all plugins from the plugins directory.

    This clears the existing registry and reloads all plugins.

    Returns:
        Dictionary mapping plugin names to plugin classes.
    """
    return load_all_plugins()


def get_plugin_registry() -> dict[str, Type[ScraperPlugin]]:
    """Get the current plugin registry.

    Returns:
        Dictionary mapping plugin names to plugin classes.
    """
    return _plugin_registry


def get_plugin_info() -> list[dict[str, str]]:
    """Get information about all loaded plugins.

    Returns:
        List of dictionaries with plugin name, source_url, and description.
    """
    return [
        {
            "name": plugin_class.name,
            "source_url": plugin_class.source_url,
            "description": plugin_class.description,
        }
        for plugin_class in _plugin_registry.values()
    ]
