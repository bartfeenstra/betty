"""
Countable localizable data.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final

from betty.classtools import Singleton
from betty.data import DataDefinition
from betty.importlib import fully_qualified_name
from betty.localizable import CountableLocalizable
from betty.localizables.gettext import _
from betty.localizables.plain import Plain
from betty.localizables.static import CountableStaticTranslations
from betty.portable.error import NotPortable
from betty.porters.callback import CallbackPorter

if TYPE_CHECKING:
    from betty.portable import PortableData


@final
class CountableLocalizableDefinition(DataDefinition[CountableLocalizable], Singleton):
    """
    The data definition for :py:class:`betty.localizable.CountableLocalizable`.
    """

    def __init__(self):
        super().__init__(
            cls=CountableLocalizable,
            label=_("A countable localizable string"),
            porter=CallbackPorter(CountableStaticTranslations.load, self._dump),
        )

    def _dump(self, data: CountableLocalizable) -> PortableData:
        if isinstance(data, CountableStaticTranslations):
            return data.dump()
        raise NotPortable(
            Plain(
                "Only static translations and plain text can be dumped to portable data, not `{localizable}` objects."
            ).format(localizable=fully_qualified_name(type(data)))
        )
