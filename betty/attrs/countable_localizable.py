"""
Countable localizable properties.
"""

from __future__ import annotations

from typing import final

from betty.attr import ProxyAttr
from betty.attrs.attr import AttrAttr
from betty.attrs.owner import OwnerAttr
from betty.datas.countable_localizable import CountableLocalizableDefinition
from betty.locale.localizable import (
    CountableLocalizable,
    ResolvableCountableLocalizable,
    ResolvableLocalizable,
    resolve_countable_localizable,
)
from betty.property import HasProperties


@final
class CountableLocalizableAttr(
    ProxyAttr[HasProperties, CountableLocalizable, ResolvableCountableLocalizable],
    OwnerAttr[HasProperties, CountableLocalizable, ResolvableCountableLocalizable],
):
    """
    An attribute containing a :py:class:`betty.locale.localizable.CountableLocalizable`.
    """

    def __init__(
        self,
        *,
        label: ResolvableLocalizable,
        description: ResolvableLocalizable | None = None,
    ):
        super().__init__(
            AttrAttr(
                CountableLocalizableDefinition(), label=label, description=description
            ).setter(resolve_countable_localizable)
        )
