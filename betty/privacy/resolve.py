"""
Resolve privacies.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from betty.privacy import Privacy

if TYPE_CHECKING:
    from betty.privacy import HasPrivacy

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


# @todo Can we remove this?
def merge_secondary_privacies(
    privacy: ResolvablePrivacy, *secondary_privacies: ResolvablePrivacy
) -> Privacy:
    """
    Merge multiple privacies into one.
    """
    privacy = resolve_privacy(privacy)
    if Privacy.PRIVATE in {
        privacy,
        *(resolve_privacy(privacy) for privacy in secondary_privacies),
    }:
        return Privacy.PRIVATE
    return privacy


def negotiate_privacies(*privacies: ResolvablePrivacy) -> Privacy:
    """
    Negotiate multiple privacies into one.

    1. The first privacy **NOT** to resolve to :py:attr:`betty.privacy.Privacy.UNDETERMINED` is returned.
    2. Else, return :py:attr:`betty.privacy.Privacy.UNDETERMINED`.
    """
    for privacy in privacies:
        resolved_privacy = resolve_privacy(privacy)
        if resolved_privacy is not Privacy.UNDETERMINED:
            return resolved_privacy
    return Privacy.UNDETERMINED
