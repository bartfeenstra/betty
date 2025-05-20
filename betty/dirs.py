"""
System directories for Betty to store data in.

These directories must only be used in production/live environments, and must therefore be injected into anything
that needs it, so during testing temporary, isolated directories can be used.
"""

import platformdirs

from betty.about import VERSION

_APPNAME = "betty"
_APPAUTHOR = "betty"

CACHE_DIRECTORY_PATH = platformdirs.user_cache_path(_APPNAME, _APPAUTHOR, VERSION)
APP_CONFIG_DIRECTORY_PATH = platformdirs.user_config_path(_APPNAME, _APPAUTHOR, VERSION)
