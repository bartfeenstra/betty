"""
Resolve privacies.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from betty.privacy import Privacy

if TYPE_CHECKING:
    from betty.attrs.privacy import HasPrivacy


def resolve_privacy(privacy: Privacy | HasPrivacy) -> Privacy:
    """
    Resolve the privacy of a value.
    """
    if isinstance(privacy, Privacy):
        return privacy
    return privacy.privacy


def merge_privacies(*privacies: Privacy | HasPrivacy) -> Privacy:
    """
    Merge multiple privacies into one.
    """
    resolved_privacies = {resolve_privacy(privacy) for privacy in privacies}
    if Privacy.PRIVATE in resolved_privacies:
        return Privacy.PRIVATE
    if Privacy.UNDETERMINED in resolved_privacies:
        return Privacy.UNDETERMINED
    return Privacy.PUBLIC


def merge_secondary_privacies(
    privacy: Privacy | HasPrivacy, *secondary_privacies: Privacy | HasPrivacy
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
