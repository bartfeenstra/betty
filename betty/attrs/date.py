"""
Date attributes.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from betty.attrs.owner import OwnerAttr
from betty.classtools import TypeABCMeta
from betty.datas.date import AnyDateDefinition
from betty.prop import HasProps

if TYPE_CHECKING:
    from betty.date import AnyDate


class HasAnyDate(HasProps, metaclass=TypeABCMeta):
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
