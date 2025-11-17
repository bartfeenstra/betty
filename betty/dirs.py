"""
System directories for Betty to store data in.

These directories must only be used in production/live environments, and must therefore be injected into anything
that needs it, so during testing temporary, isolated directories can be used.
"""

from __future__ import annotations

from pathlib import Path

import platformdirs

from betty.about import VERSION_MAJOR

_APPNAME = "betty"
_APPAUTHOR = "betty"

ROOT_DIRECTORY_PATH = Path(__file__).resolve().parents[1]
"""
The betty installation root directory path.

This is read-only.
"""

ASSETS_DIRECTORY_PATH = ROOT_DIRECTORY_PATH / "betty" / "assets"
"""
The betty installation assets directory path.

This is read-only.
"""

DATA_DIRECTORY_PATH = ROOT_DIRECTORY_PATH / "betty" / "data"
"""
The betty installation packaged third-party assets directory path.

This is read-only.
"""

CACHE_DIRECTORY_PATH = platformdirs.user_cache_path(_APPNAME, _APPAUTHOR, VERSION_MAJOR)
"""
The Betty instance's cache directory path on the local system.
"""

APP_CONFIG_DIRECTORY_PATH = platformdirs.user_config_path(
    _APPNAME, _APPAUTHOR, VERSION_MAJOR
)
"""
The Betty instance's :py:class:`betty.app.App` configuration path on the local system.
"""
