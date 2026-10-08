"""
Describe locations of data and information in user-facing ways.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from betty.operator import Chain, Operator
from betty.url import HasUrl

if TYPE_CHECKING:
    from collections.abc import Sequence

    from betty.localizer import Localizer

type Locator = Operator | HasUrl | Path
"""
Describe a partial location of something.
"""


def reduce(*location: Locator) -> Sequence[Locator]:
    """
    Reduce a location to its most compact and descriptive form.
    """
    return Chain.reduce(*location)


def format_(*locators: Locator, localizer: Localizer) -> Sequence[str]:
    """
    Format a locator to a string.
    """
    return tuple(_format(locator, localizer) for locator in locators)


def _format(locator: Locator, localizer: Localizer, /) -> str:
    if isinstance(locator, Operator):
        return locator.format()
    if isinstance(locator, HasUrl):
        return locator.url.localize(localizer)
    return str(locator)
