"""
Localizable properties.
"""

from __future__ import annotations

from typing import final

from betty.datas.localizable import LocalizableDefinition
from betty.locale.localizable import (
    Localizable,
    ResolvableLocalizable,
    resolve_localizable,
)
from betty.property import Property


@final
class LocalizableProperty(Property[Localizable, ResolvableLocalizable]):
    """
    A property containing a :py:class:`betty.locale.localizable.Localizable`.
    """

    def __init__(
        self,
        *,
        label: ResolvableLocalizable,
        description: ResolvableLocalizable | None = None,
    ):
        super().__init__(
            LocalizableDefinition(),
            label=label,
            description=description,
            resolver=resolve_localizable,
        )
