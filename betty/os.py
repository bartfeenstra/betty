"""
Operating System functionality.
"""

from __future__ import annotations

from betty.error import Error
from betty.localizables.gettext import _


class NoAvailablePort(Error, OSError):
    """
    Raised when no available networking port could be found.
    """

    _message = _("Cannot find an available networking port.")
