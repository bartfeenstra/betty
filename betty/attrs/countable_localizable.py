"""
Countable localizable properties.
"""

from __future__ import annotations

from typing import final

from betty.attr import AttrProperty
from betty.datas.countable_localizable import CountableLocalizableDefinition
from betty.descriptor import HasDescriptors
from betty.locale.localizable import (
    CountableLocalizable,
    ResolvableCountableLocalizable,
    ResolvableLocalizable,
    resolve_countable_localizable,
)


@final
class CountableLocalizableProperty(
    AttrProperty[HasDescriptors, CountableLocalizable, ResolvableCountableLocalizable]
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
            CountableLocalizableDefinition(),
            label=label,
            description=description,
            resolver=resolve_countable_localizable,
        )
