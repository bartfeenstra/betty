"""
Localizable properties.
"""

from __future__ import annotations

from typing import final

from betty.attr import ProxyAttr
from betty.attrs.attr import AttrAttr
from betty.datas.localizable import LocalizableDefinition
from betty.locale.localizable import (
    Localizable,
    ResolvableLocalizable,
    resolve_localizable,
)
from betty.property import HasProperties


@final
class LocalizableAttr(ProxyAttr[HasProperties, Localizable, ResolvableLocalizable]):
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
            AttrAttr(
                LocalizableDefinition(), label=label, description=description
            ).setter(resolve_localizable)
        )
