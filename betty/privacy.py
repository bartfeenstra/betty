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


type ResolvablePrivacy = Privacy | HasPrivacy


def resolve_privacy(privacy: ResolvablePrivacy, /) -> Privacy:
    """
    Resolve the privacy of a value.
    """
    if isinstance(privacy, Privacy):
        return privacy
    return privacy.privacy


def merge_privacies(*privacies: ResolvablePrivacy) -> Privacy:
    """
    Merge multiple privacies into one.

    All privacies are treated equally.

    1. If any of the privacies resolve to :py:attr:`betty.privacy.Privacy.PRIVATE`, return :py:attr:`betty.privacy.Privacy.PRIVATE`.
    2. Else, if any of the privacies resolve to :py:attr:`betty.privacy.Privacy.PUBLIC`, return :py:attr:`betty.privacy.Privacy.PUBLIC`.
    3. Else, return :py:attr:`betty.privacy.Privacy.UNDETERMINED`.
    """
    resolved_privacies = {resolve_privacy(privacy) for privacy in privacies}
    if Privacy.PRIVATE in resolved_privacies:
        return Privacy.PRIVATE
    if Privacy.PUBLIC in resolved_privacies:
        return Privacy.PUBLIC
    return Privacy.UNDETERMINED


def consider_privacies(*privacies: ResolvablePrivacy) -> Privacy:
    """
    Merge multiple privacies into one.

    1. If any of the privacies resolve to :py:attr:`betty.privacy.Privacy.PRIVATE`, return :py:attr:`betty.privacy.Privacy.PRIVATE`.
    2. Else, return the first privacy if any were given.
    3. Else, return :py:attr:`betty.privacy.Privacy.UNDETERMINED`.
    """
    resolved_privacies = [resolve_privacy(privacy) for privacy in privacies]
    if Privacy.PRIVATE in resolved_privacies:
        return Privacy.PRIVATE
    if resolved_privacies:
        return resolved_privacies[0]
    return Privacy.UNDETERMINED


def override_privacies(*privacies: ResolvablePrivacy) -> Privacy:
    """
    Merge multiple privacies into one, with earlier ones overriding later ones.

    1. The first privacy **NOT** to resolve to :py:attr:`betty.privacy.Privacy.UNDETERMINED` is returned.
    2. Else, return :py:attr:`betty.privacy.Privacy.UNDETERMINED`.
    """
    for privacy in privacies:
        resolved_privacy = resolve_privacy(privacy)
        if resolved_privacy is not Privacy.UNDETERMINED:
            return resolved_privacy
    return Privacy.UNDETERMINED
