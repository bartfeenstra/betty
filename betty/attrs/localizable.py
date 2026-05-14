"""
Localizable properties.
"""

from __future__ import annotations

from typing import final

from betty.attrs.attr import AttrAttr
from betty.datas.localizable import LocalizableDefinition
from betty.locale.localizable import (
    Localizable,
    ResolvableLocalizable,
    resolve_localizable,
)


@final
class LocalizableAttr(AttrAttr[Localizable, ResolvableLocalizable]):
    """
    An attribute containing a :py:class:`betty.locale.localizable.Localizable`.
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
