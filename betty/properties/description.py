"""
Data that has human-readable descriptions.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from betty.locale.localizable.gettext import _
from betty.properties.localizable import LocalizableProperty
from betty.property import Optional

if TYPE_CHECKING:
    from betty.locale.localizable import ResolvableLocalizable


class HasDescription:
    """
    Data with a description.
    """

    description = Optional(LocalizableProperty(label=_("Description")))
    """
    The description.
    """

    def __init__(
        self,
        *args: Any,
        description: ResolvableLocalizable | None = None,
        **kwargs: Any,
    ):
        super().__init__(*args, **kwargs)
        self.description = description
