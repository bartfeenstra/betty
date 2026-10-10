"""
Describe locations of data and information.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from betty.operator import Chain, Operator
from betty.url import HasUrl

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator, Sequence

    from betty.localizer import Localizer

type Locator = Operator | HasLocation | HasUrl | Path
"""
Describe part of something's location.
"""

type ResolvableLocation = Operator | Iterable[Locator]
"""
Describe the location of something.
"""


def resolve_location(location: ResolvableLocation, /) -> tuple[Locator]:
    """
    Resolve locators to a location.
    """
    if isinstance(location, Operator):
        return (location,)
    return tuple(location)


class HasLocation:
    """
    An object with a location.
    """

    def __init__(self, *args: Any, location: ResolvableLocation = (), **kwargs: Any):
        super().__init__(*args, **kwargs)
        self._location = resolve_location(location)

    @property
    def location(self) -> Sequence[Locator]:
        """
        The object's location.

        The first locator is the innermost, and the last locator is the outermost.
        """
        return self._location


def reduce(*location: Locator) -> Sequence[Locator]:
    """
    Reduce a location to its most compact and descriptive form.
    """
    return Chain.reduce(*_flatten(*location))


def _flatten(*location: Locator) -> Iterator[Locator]:
    for locator in location:
        if isinstance(locator, HasLocation):
            yield from locator.location
        else:
            yield locator


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
