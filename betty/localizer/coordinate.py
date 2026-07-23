"""
The geographic coordinate formatter.
"""

from __future__ import annotations

from typing import final

from geopy import units
from geopy.format import DEGREES_FORMAT


@final
class CoordinateFormatter:
    """
    Format geographic coordinates.
    """

    def format_degrees(self, degrees: float, /) -> str:
        """
        Format degrees.
        """
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
