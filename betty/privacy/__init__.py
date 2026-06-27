"""
The Privacy API.
"""

from __future__ import annotations

import enum
from abc import ABC, abstractmethod
from typing import final


@final
class Privacy(enum.Enum):
    """
    The available privacy modes.
    """

    PUBLIC = False
    """
    The resource is explicitly made public.
    """

    PRIVATE = True
    """
    The resource is explicitly made private.
    """

    UNDETERMINED = None
    """
    The resource has no explicit privacy. This means that:
    
    - it may be changed at will
    - when checking access, UNDETERMINED evaluates to PUBLIC.
    """

    @property
    def determined(self) -> bool:
        """
        Whether this privacy is determined (public or private).
        """
        return self is not Privacy.UNDETERMINED

    @property
    def publishable(self) -> bool:
        """
        Whether this privacy is publishable.

        Something is publishable when it is not private.
        """
        return self is not Privacy.PRIVATE


class HasPrivacy(ABC):
    """
    Data that that has privacy.
    """

    @property
    @abstractmethod
    def privacy(self) -> Privacy:
        """
        The data's privacy.
        """
