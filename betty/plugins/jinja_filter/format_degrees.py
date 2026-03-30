"""
The ``format_degrees`` Jinja filter.
"""

from __future__ import annotations

from typing import final

from geopy import units
from geopy.format import DEGREES_FORMAT

from betty.jinja.filter import JinjaFilter, JinjaFilterDefinition


@final
@JinjaFilterDefinition("format-degrees", auto=True)
class FormatDegrees(JinjaFilter):
    """
    Format geographic coordinates.

    .. plugin:: jinja-filter:format-degrees
    """

    def __call__(  # noqa: D102
        self, degrees: int
    ) -> str:
        arcminutes = units.arcminutes(degrees=degrees - int(degrees))
        arcseconds = units.arcseconds(arcminutes=arcminutes - int(arcminutes))
        format_dict = {
            "deg": "°",
            "arcmin": "'",
            "arcsec": '"',
            "degrees": degrees,
            "minutes": round(abs(arcminutes)),
            "seconds": round(abs(arcseconds)),
        }
        return DEGREES_FORMAT % format_dict
