"""
Date attributes.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from betty.attrs.owner import OwnerAttr
from betty.classtools.init import Init
from betty.datas.date import AnyDateDefinition

if TYPE_CHECKING:
    from betty.date import AnyDate


class HasAnyDate(Init):
    """
    A resource with date information.
    """

    date = OwnerAttr(AnyDateDefinition()).optional
    """
    The date.
    """

    def __init__(
        self,
        *args: Any,
        date: AnyDate | None = None,
        **kwargs: Any,
    ):
        super().__init__(*args, **kwargs)
        self.date = date
